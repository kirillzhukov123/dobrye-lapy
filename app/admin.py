from django.contrib import admin, messages
from django.utils.html import format_html

from .models import (
    AdoptionApplication, Enclosure, GuardianshipPayment, HomePhotoReport,
    Interview, Pet, TransferContract, VetCard, WalkBooking,
)
from .services import ApprovalError, approve_application


class VetCardInline(admin.StackedInline):
    model = VetCard
    can_delete = False
    extra = 0


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'breed', 'age', 'status', 'enclosure', 'photo_preview')
    list_filter = ('species', 'status', 'enclosure')
    search_fields = ('name', 'breed', 'character', 'rescue_story')
    list_editable = ('status',)
    readonly_fields = ('photo_preview',)
    inlines = [VetCardInline]

    @admin.display(description='Возраст')
    def age(self, obj):
        return obj.age_display

    @admin.display(description='Фото')
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="max-height: 90px; border-radius: 6px;" />', obj.photo.url)
        return '—'


@admin.register(Enclosure)
class EnclosureAdmin(admin.ModelAdmin):
    list_display = ('number', 'pets_count')
    search_fields = ('number',)

    @admin.display(description='Питомцев')
    def pets_count(self, obj):
        return obj.pets.count()


@admin.register(VetCard)
class VetCardAdmin(admin.ModelAdmin):
    list_display = ('pet', 'vaccinations')
    search_fields = ('pet__name', 'vaccinations')


class InterviewInline(admin.StackedInline):
    model = Interview
    extra = 0


@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'pet', 'applicant', 'status', 'message_short')
    list_filter = ('status', 'pet__species')
    search_fields = ('pet__name', 'applicant__username', 'message')
    inlines = [InterviewInline]
    actions = ('approve_selected', 'reject_selected')

    @admin.display(description='Сообщение')
    def message_short(self, obj):
        return obj.message[:80]

    @admin.action(description='Утвердить выбранные анкеты')
    def approve_selected(self, request, queryset):
        approved = 0
        errors = []
        for application in queryset:
            try:
                approve_application(application)
                approved += 1
            except ApprovalError as error:
                errors.append(f'Анкета #{application.pk}: {error}')
        if approved:
            self.message_user(request, f'Утверждено анкет: {approved}.', messages.SUCCESS)
        if errors:
            self.message_user(request, '; '.join(errors), messages.ERROR)

    @admin.action(description='Отклонить выбранные анкеты')
    def reject_selected(self, request, queryset):
        count = queryset.filter(status='new').update(status='rejected')
        self.message_user(request, f'Отклонено анкет: {count}.', messages.SUCCESS)


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'curator', 'scheduled_at', 'result')
    list_filter = ('curator',)
    search_fields = ('application__pet__name', 'application__applicant__username')


@admin.register(WalkBooking)
class WalkBookingAdmin(admin.ModelAdmin):
    list_display = ('pet', 'volunteer', 'when', 'is_done')
    list_filter = ('is_done', 'pet__species')
    search_fields = ('pet__name', 'volunteer__username')
    date_hierarchy = 'when'


class HomePhotoReportInline(admin.TabularInline):
    model = HomePhotoReport
    extra = 0


@admin.register(TransferContract)
class TransferContractAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'pet', 'application', 'signed_at')
    search_fields = ('document_number', 'pet__name', 'application__applicant__username')
    inlines = [HomePhotoReportInline]


@admin.register(GuardianshipPayment)
class GuardianshipPaymentAdmin(admin.ModelAdmin):
    list_display = ('pet', 'guardian', 'amount', 'period')
    list_filter = ('period', 'pet__species')
    search_fields = ('pet__name', 'guardian__username')


@admin.register(HomePhotoReport)
class HomePhotoReportAdmin(admin.ModelAdmin):
    list_display = ('contract', 'photo', 'comment_short')
    search_fields = ('contract__document_number', 'comment')

    @admin.display(description='Комментарий')
    def comment_short(self, obj):
        return obj.comment[:80]
