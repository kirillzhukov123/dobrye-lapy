from django.db import transaction
from django.utils import timezone

from .models import TransferContract, AdoptionApplication, Pet

BLOCKED = ('quarantine', 'treatment')


class ApprovalError(Exception):
    pass


def can_apply(pet):
    return pet.status not in BLOCKED and pet.status != 'home'


def can_book_walk(pet):
    return pet.status not in BLOCKED and pet.status != 'home'


@transaction.atomic
def approve_application(application):
    pet = Pet.objects.select_for_update().get(pk=application.pet_id)
    application = AdoptionApplication.objects.select_for_update().get(pk=application.pk)

    if application.status != 'new':
        raise ApprovalError('Эта анкета уже обработана.')
    if pet.status == 'home':
        raise ApprovalError('Питомец уже передан в новый дом.')
    if pet.status in BLOCKED:
        raise ApprovalError('Нельзя утвердить анкету: питомец на карантине или лечении.')

    application.status = 'approved'
    application.save(update_fields=['status'])

    TransferContract.objects.create(
        pet=pet,
        application=application,
        document_number=f'PET-{application.pk}',
        signed_at=timezone.now(),
    )

    pet.status = 'home'
    pet.save(update_fields=['status'])

    AdoptionApplication.objects.filter(pet=pet) \
        .exclude(pk=application.pk) \
        .filter(status__in=['new', 'approved']) \
        .update(status='rejected_home')

    return pet
