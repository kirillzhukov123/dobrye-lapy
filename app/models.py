from django.db import models
from django.db.models import Q


class Enclosure(models.Model):
    number = models.CharField('Номер', max_length=20, unique=True)

    class Meta:
        verbose_name = 'Вольер'
        verbose_name_plural = 'Вольеры'
        ordering = ['number']

    def __str__(self):
        return f'Вольер {self.number}'


class Pet(models.Model):
    SPECIES = [('dog', 'Собака'), ('cat', 'Кошка')]
    STATUS = [
        ('quarantine', 'На карантине'),
        ('treatment', 'На лечении'),
        ('ready', 'Готов к усыновлению'),
        ('reserved', 'Забронирован'),
        ('home', 'Дома'),
    ]

    name = models.CharField('Кличка', max_length=100)
    species = models.CharField('Вид', max_length=10, choices=SPECIES)
    breed = models.CharField('Порода', max_length=100, blank=True)
    age_months = models.PositiveIntegerField('Возраст, мес.', default=0)
    character = models.TextField('Характер', blank=True)
    rescue_story = models.TextField('История спасения', blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS, default='quarantine')
    enclosure = models.ForeignKey(
        Enclosure, verbose_name='Вольер', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pets',
    )
    photo = models.ImageField('Фото', upload_to='pets/', blank=True)

    class Meta:
        verbose_name = 'Питомец'
        verbose_name_plural = 'Питомцы'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'

    @property
    def age_display(self):
        if self.age_months < 12:
            return f'{self.age_months} мес.'
        years = self.age_months // 12
        months = self.age_months % 12
        if months:
            return f'{years} г. {months} мес.'
        return f'{years} г.'

    @property
    def is_available(self):
        return self.status not in ('quarantine', 'treatment', 'home')


class VetCard(models.Model):
    pet = models.OneToOneField(
        Pet, verbose_name='Питомец', on_delete=models.CASCADE, related_name='vet_card',
    )
    vaccinations = models.TextField('Прививки', blank=True)

    class Meta:
        verbose_name = 'Ветеринарная карточка'
        verbose_name_plural = 'Ветеринарные карточки'

    def __str__(self):
        return f'Веткарта: {self.pet.name}'


class AdoptionApplication(models.Model):
    STATUS = [
        ('new', 'Новая'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
        ('rejected_home', 'Отклонено (питомец обрёл дом)'),
    ]
    pet = models.ForeignKey(
        Pet, verbose_name='Питомец', on_delete=models.CASCADE, related_name='applications',
    )
    applicant = models.ForeignKey(
        'auth.User', verbose_name='Заявитель', on_delete=models.CASCADE,
        related_name='adoption_applications',
    )
    message = models.TextField('Сообщение', blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS, default='new')

    class Meta:
        verbose_name = 'Анкета на усыновление'
        verbose_name_plural = 'Анкеты на усыновление'
        ordering = ['-pk']
        constraints = [
            models.UniqueConstraint(
                fields=['pet', 'applicant'],
                condition=Q(status__in=['new', 'approved']),
                name='unique_active_application',
            ),
        ]

    def __str__(self):
        return f'Анкета #{self.pk} на {self.pet}'

    @property
    def is_active(self):
        return self.status in ('new', 'approved')


class Interview(models.Model):
    application = models.OneToOneField(
        AdoptionApplication, verbose_name='Анкета', on_delete=models.CASCADE,
        related_name='interview',
    )
    curator = models.ForeignKey(
        'auth.User', verbose_name='Куратор', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='interviews',
    )
    scheduled_at = models.DateTimeField('Дата и время')
    result = models.CharField('Результат', max_length=100, blank=True)

    class Meta:
        verbose_name = 'Собеседование'
        verbose_name_plural = 'Собеседования'
        ordering = ['scheduled_at']

    def __str__(self):
        return f'Собеседование по анкете #{self.application_id}'


class WalkBooking(models.Model):
    pet = models.ForeignKey(
        Pet, verbose_name='Питомец', on_delete=models.CASCADE, related_name='walks',
    )
    volunteer = models.ForeignKey(
        'auth.User', verbose_name='Волонтёр', on_delete=models.CASCADE,
        related_name='walk_bookings',
    )
    when = models.DateTimeField('Дата и время')
    is_done = models.BooleanField('Состоялась', default=False)

    class Meta:
        verbose_name = 'Запись на прогулку'
        verbose_name_plural = 'Записи на прогулку'
        ordering = ['-when']
        constraints = [
            models.UniqueConstraint(fields=['pet', 'when'], name='unique_walk_slot'),
        ]

    def __str__(self):
        return f'Прогулка с {self.pet} ({self.when:%d.%m.%Y %H:%M})'


class TransferContract(models.Model):
    pet = models.OneToOneField(
        Pet, verbose_name='Питомец', on_delete=models.CASCADE, related_name='contract',
    )
    application = models.OneToOneField(
        AdoptionApplication, verbose_name='Анкета', on_delete=models.CASCADE,
        related_name='contract',
    )
    document_number = models.CharField('Номер документа', max_length=50, unique=True)
    signed_at = models.DateTimeField('Дата подписания')

    class Meta:
        verbose_name = 'Договор передачи животного'
        verbose_name_plural = 'Договоры передачи животных'

    def __str__(self):
        return f'Договор {self.document_number}'


class GuardianshipPayment(models.Model):
    pet = models.ForeignKey(
        Pet, verbose_name='Питомец', on_delete=models.CASCADE, related_name='payments',
    )
    guardian = models.ForeignKey(
        'auth.User', verbose_name='Опекун', on_delete=models.CASCADE,
        related_name='guardianship_payments',
    )
    amount = models.DecimalField('Сумма', max_digits=10, decimal_places=2)
    period = models.CharField('Период', max_length=20, help_text='например 2026-11')

    class Meta:
        verbose_name = 'Опекунский взнос'
        verbose_name_plural = 'Опекунские взносы'
        ordering = ['-pk']
        constraints = [
            models.UniqueConstraint(
                fields=['pet', 'guardian', 'period'],
                name='unique_payment_period',
            ),
        ]

    def __str__(self):
        return f'Взнос {self.amount} ₽ за {self.period}'


class HomePhotoReport(models.Model):
    contract = models.ForeignKey(
        TransferContract, verbose_name='Договор', on_delete=models.CASCADE,
        related_name='reports',
    )
    photo = models.ImageField('Фото', upload_to='reports/', blank=True)
    comment = models.TextField('Комментарий', blank=True)

    class Meta:
        verbose_name = 'Фотоотчёт из нового дома'
        verbose_name_plural = 'Фотоотчёты из нового дома'

    def __str__(self):
        return f'Фотоотчёт по договору {self.contract.document_number}'
