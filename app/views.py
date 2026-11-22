from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    ApplicationForm, GuardianshipForm, PetForm, RegistrationForm, WalkForm,
)
from .models import (
    AdoptionApplication, GuardianshipPayment, Pet, TransferContract, WalkBooking,
)
from .services import (
    ApprovalError, approve_application, can_apply, can_book_walk,
)


def index(request):
    pets = Pet.objects.filter(status='ready')[:6]
    stats = {
        'total': Pet.objects.count(),
        'ready': Pet.objects.filter(status='ready').count(),
        'home': TransferContract.objects.count(),
    }
    return render(request, 'index.html', {'pets': pets, 'stats': stats})


def _filtered_pets(request):
    q = request.GET.get('q', '').strip()
    species = request.GET.get('species', '')
    status = request.GET.get('status', '')
    sort = request.GET.get('sort', 'name')

    pets = Pet.objects.select_related('enclosure')
    if species:
        pets = pets.filter(species=species)
    if status:
        pets = pets.filter(status=status)
    if sort in ('name', '-name', 'age_months', '-age_months'):
        pets = pets.order_by(sort)
    if q:
        needle = q.casefold()
        pets = [
            pet for pet in pets
            if needle in (pet.name or '').casefold()
            or needle in (pet.breed or '').casefold()
        ]

    return pets, {
        'q': q,
        'species': species,
        'status': status,
        'sort': sort,
        'species_choices': Pet.SPECIES,
        'status_choices': Pet.STATUS,
    }


def pet_list(request):
    pets, filters = _filtered_pets(request)
    paginator = Paginator(pets, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'pets/list.html', {
        'pets': page_obj,
        'page_obj': page_obj,
        'total': paginator.count,
        **filters,
    })


def search(request):
    pets, filters = _filtered_pets(request)
    paginator = Paginator(pets, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'search.html', {
        'pets': page_obj,
        'page_obj': page_obj,
        'total': paginator.count,
        **filters,
    })


def _pet_payload(pet):
    return {
        'id': pet.pk,
        'name': pet.name,
        'species': pet.species,
        'species_label': pet.get_species_display(),
        'breed': pet.breed or 'порода не указана',
        'age': pet.age_display,
        'status': pet.status,
        'status_label': pet.get_status_display(),
        'enclosure': str(pet.enclosure) if pet.enclosure else 'Вольер не указан',
        'photo': pet.photo.url if pet.photo else static('images/placeholder.jpg'),
        'url': reverse('pet_detail', args=[pet.pk]),
    }


def api_pets(request):
    pets, filters = _filtered_pets(request)

    ids = request.GET.get('ids', '')
    if 'ids' in request.GET:
        id_list = [int(item) for item in ids.split(',') if item.strip().isdigit()]
        if isinstance(pets, list):
            pets = [pet for pet in pets if pet.pk in id_list]
        else:
            pets = pets.filter(pk__in=id_list)

    if request.GET.get('all') == '1':
        items = pets
        total = len(pets) if isinstance(pets, list) else pets.count()
        page_number = 1
        pages = 1
    else:
        paginator = Paginator(pets, 20)
        page_obj = paginator.get_page(request.GET.get('page'))
        items = page_obj
        total = paginator.count
        page_number = page_obj.number
        pages = paginator.num_pages

    return JsonResponse({
        'total': total,
        'page': page_number,
        'pages': pages,
        'pets': [_pet_payload(pet) for pet in items],
    })


def _detail_context(request, pet, application_form=None, walk_form=None, open_form=''):
    user_application = None
    if request.user.is_authenticated:
        user_application = pet.applications.filter(
            applicant=request.user, status__in=['new', 'approved'],
        ).first()

    return {
        'pet': pet,
        'vet_card': getattr(pet, 'vet_card', None),
        'can_apply': can_apply(pet),
        'can_walk': can_book_walk(pet),
        'user_application': user_application,
        'walks': pet.walks.filter(is_done=False).select_related('volunteer')[:5],
        'application_form': application_form or ApplicationForm(),
        'walk_form': walk_form or WalkForm(),
        'open_form': open_form,
    }


def pet_detail(request, pk):
    pet = get_object_or_404(Pet.objects.select_related('enclosure'), pk=pk)
    return render(request, 'pets/detail.html', _detail_context(request, pet))


@login_required
def apply_adoption(request, pk):
    pet = get_object_or_404(Pet, pk=pk)

    if request.method != 'POST':
        return redirect('pet_detail', pk=pet.pk)

    if not can_apply(pet):
        messages.error(request, 'Питомец недоступен для усыновления.')
        return redirect('pet_detail', pk=pet.pk)

    if pet.applications.filter(applicant=request.user, status__in=['new', 'approved']).exists():
        messages.warning(request, 'Вы уже подали анкету на этого питомца.')
        return redirect('pet_detail', pk=pet.pk)

    form = ApplicationForm(request.POST)
    if form.is_valid():
        application = form.save(commit=False)
        application.pet = pet
        application.applicant = request.user
        application.save()
        messages.success(request, 'Анкета отправлена. Куратор свяжется с вами.')
        return redirect('pet_detail', pk=pet.pk)

    messages.error(request, 'Проверьте анкету: исправьте отмеченные поля.')
    context = _detail_context(request, pet, application_form=form, open_form='application')
    return render(request, 'pets/detail.html', context)


@login_required
def book_walk(request, pk):
    pet = get_object_or_404(Pet, pk=pk)

    if request.method != 'POST':
        return redirect('pet_detail', pk=pet.pk)

    if not can_book_walk(pet):
        messages.error(request, 'Запись на прогулку недоступна для этого статуса.')
        return redirect('pet_detail', pk=pet.pk)

    form = WalkForm(request.POST)
    if form.is_valid():
        when = form.cleaned_data['when']
        if WalkBooking.objects.filter(pet=pet, when=when).exists():
            form.add_error('when', 'На это время уже есть запись. Выберите другое.')
        else:
            booking = form.save(commit=False)
            booking.pet = pet
            booking.volunteer = request.user
            booking.save()
            messages.success(request, 'Запись на прогулку создана.')
            return redirect('pet_detail', pk=pet.pk)

    messages.error(request, 'Проверьте дату прогулки: исправьте отмеченные поля.')
    context = _detail_context(request, pet, walk_form=form, open_form='walk')
    return render(request, 'pets/detail.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('index')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Регистрация завершена. Добро пожаловать.')
        return redirect('index')

    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile(request):
    applications = request.user.adoption_applications.select_related('pet')
    walks = request.user.walk_bookings.select_related('pet')
    payments = request.user.guardianship_payments.select_related('pet')
    contracts = TransferContract.objects.filter(
        application__applicant=request.user,
    ).select_related('pet')

    return render(request, 'profile.html', {
        'applications': applications,
        'walks': walks,
        'payments': payments,
        'contracts': contracts,
    })


def _is_curator(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name='Куратор').exists()
    )


@user_passes_test(_is_curator)
def application_list(request):
    status = request.GET.get('status', '')
    pet_id = request.GET.get('pet', '')
    q = request.GET.get('q', '').strip()

    applications = AdoptionApplication.objects.select_related('pet', 'applicant')
    if status:
        applications = applications.filter(status=status)
    if pet_id:
        if pet_id.isdigit():
            applications = applications.filter(pet_id=int(pet_id))
        else:
            applications = applications.none()
    if q:
        needle = q.casefold()
        applications = [
            application for application in applications
            if needle in (application.applicant.username or '').casefold()
            or needle in (application.pet.name or '').casefold()
        ]

    return render(request, 'applications/list.html', {
        'applications': applications,
        'status': status,
        'pet_id': pet_id,
        'q': q,
        'status_choices': AdoptionApplication.STATUS,
    })


@require_POST
@user_passes_test(_is_curator)
def approve(request, pk):
    application = get_object_or_404(AdoptionApplication, pk=pk)
    try:
        approve_application(application)
    except ApprovalError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, 'Кандидат утверждён, остальные анкеты отклонены.')
    return redirect('application_list')


@require_POST
@user_passes_test(_is_curator)
def reject_application(request, pk):
    application = get_object_or_404(AdoptionApplication, pk=pk)
    if application.status == 'new':
        application.status = 'rejected'
        application.save(update_fields=['status'])
        messages.success(request, 'Анкета отклонена.')
    else:
        messages.error(request, 'Эту анкету уже нельзя отклонить.')
    return redirect('application_list')


@require_POST
@user_passes_test(_is_curator)
def walk_done(request, pk):
    booking = get_object_or_404(WalkBooking, pk=pk)
    if booking.is_done:
        messages.info(request, 'Прогулка уже отмечена как состоявшаяся.')
    else:
        booking.is_done = True
        booking.save(update_fields=['is_done'])
        messages.success(request, 'Прогулка отмечена как состоявшаяся.')
    return redirect('profile')


def is_admin(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name='Администратор').exists()
        or user.groups.filter(name='Куратор').exists()
    )


@user_passes_test(is_admin)
def pet_create(request):
    form = PetForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        pet = form.save()
        messages.success(request, 'Питомец добавлен в каталог.')
        return redirect('pet_detail', pk=pet.pk)

    return render(request, 'pets/form.html', {'form': form, 'is_edit': False})


@user_passes_test(is_admin)
def pet_edit(request, pk):
    pet = get_object_or_404(Pet, pk=pk)
    form = PetForm(request.POST or None, request.FILES or None, instance=pet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Данные питомца обновлены.')
        return redirect('pet_detail', pk=pet.pk)

    return render(request, 'pets/form.html', {'form': form, 'pet': pet, 'is_edit': True})


@user_passes_test(is_admin)
def pet_delete(request, pk):
    pet = get_object_or_404(Pet, pk=pk)
    if request.method == 'POST':
        pet.delete()
        messages.success(request, 'Питомец удалён из каталога.')
        return redirect('pet_list')

    return render(request, 'pets/confirm_delete.html', {'pet': pet})


@login_required
def guardianship(request):
    form = GuardianshipForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        pet = form.cleaned_data['pet']
        period = form.cleaned_data['period']
        if GuardianshipPayment.objects.filter(
            pet=pet, guardian=request.user, period=period,
        ).exists():
            form.add_error('period', 'Взнос за этот период уже зарегистрирован.')
        else:
            payment = form.save(commit=False)
            payment.guardian = request.user
            payment.save()
            messages.success(request, 'Опекунский взнос зарегистрирован.')
            return redirect('guardianship')

    payments = request.user.guardianship_payments.select_related('pet')
    return render(request, 'guardianship/list.html', {
        'form': form,
        'payments': payments,
    })


def about(request):
    return render(request, 'about.html')
