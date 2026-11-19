import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import (
    ApplicationForm, GuardianshipForm, PetForm, RegistrationForm, WalkForm,
)
from .models import AdoptionApplication, Enclosure, Pet, WalkBooking


def make_pet(name='Бим', species='dog', status='ready', **extra):
    defaults = {
        'breed': 'Метис',
        'age_months': 26,
        'character': 'Спокойный',
        'rescue_story': 'Найден на улице',
        'status': status,
    }
    defaults.update(extra)
    return Pet.objects.create(name=name, species=species, **defaults)


class FormValidationTests(TestCase):
    def test_application_form_accepts_valid_phone_and_message(self):
        form = ApplicationForm(data={
            'phone': '+7 (900) 123-45-67',
            'message': 'Живу в частном доме, есть опыт содержания собак.',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_application_form_rejects_short_phone(self):
        form = ApplicationForm(data={'phone': '+7 (900) 1', 'message': 'x' * 30})
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_application_form_rejects_short_message(self):
        form = ApplicationForm(data={'phone': '+7 (900) 123-45-67', 'message': 'мало'})
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)

    def test_application_form_rejects_long_message(self):
        form = ApplicationForm(data={
            'phone': '+7 (900) 123-45-67',
            'message': 'а' * 1001,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)

    def test_guardianship_form_rejects_bad_period(self):
        pet = make_pet()
        form = GuardianshipForm(data={'pet': pet.pk, 'amount': 500, 'period': '11.2026'})
        self.assertFalse(form.is_valid())
        self.assertIn('period', form.errors)

    def test_guardianship_form_rejects_small_amount(self):
        pet = make_pet()
        form = GuardianshipForm(data={'pet': pet.pk, 'amount': 50, 'period': '2026-11'})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_guardianship_form_accepts_valid_data(self):
        pet = make_pet()
        form = GuardianshipForm(data={'pet': pet.pk, 'amount': 500, 'period': '2026-11'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_walk_form_rejects_past_date(self):
        when = timezone.now() - timedelta(days=1)
        form = WalkForm(data={'when': when.strftime('%Y-%m-%dT%H:%M')})
        self.assertFalse(form.is_valid())
        self.assertIn('when', form.errors)

    def test_walk_form_accepts_future_date(self):
        when = timezone.now() + timedelta(days=2)
        form = WalkForm(data={'when': when.strftime('%Y-%m-%dT%H:%M')})
        self.assertTrue(form.is_valid(), form.errors)

    def test_registration_form_has_client_attributes(self):
        form = RegistrationForm()
        self.assertEqual(form.fields['email'].widget.attrs['data-check'], 'email')
        self.assertEqual(form.fields['password2'].widget.attrs['data-match'], 'id_password1')

    def test_pet_form_has_required_attribute(self):
        form = PetForm()
        self.assertEqual(form.fields['name'].widget.attrs['data-check'], 'required')
        self.assertEqual(form.fields['age_months'].widget.attrs['data-max'], '360')


class CatalogApiTests(TestCase):
    def setUp(self):
        self.dog = make_pet('Бим', 'dog')
        self.cat = make_pet('Мурка', 'cat')

    def test_api_returns_json(self):
        response = self.client.get(reverse('api_pets'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['total'], 2)
        self.assertEqual(len(data['pets']), 2)
        first = data['pets'][0]
        for key in ('id', 'name', 'species', 'species_label', 'breed', 'age',
                    'status', 'status_label', 'enclosure', 'photo', 'url'):
            self.assertIn(key, first)

    def test_api_filters_by_species(self):
        response = self.client.get(reverse('api_pets'), {'species': 'cat'})
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['pets'][0]['name'], 'Мурка')

    def test_api_filters_by_query(self):
        response = self.client.get(reverse('api_pets'), {'q': 'Бим'})
        self.assertEqual(response.json()['total'], 1)

    def test_api_all_returns_single_page(self):
        response = self.client.get(reverse('api_pets'), {'all': '1'})
        data = response.json()
        self.assertEqual(data['pages'], 1)
        self.assertEqual(data['total'], 2)

    def test_api_filters_by_ids(self):
        response = self.client.get(
            reverse('api_pets'), {'ids': '%d' % self.cat.pk, 'all': '1'},
        )
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['pets'][0]['name'], 'Мурка')


class PageTests(TestCase):
    def setUp(self):
        self.pet = make_pet()

    def test_public_pages_open(self):
        for name in ('index', 'pet_list', 'search', 'about', 'login', 'register'):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_detail_page_contains_client_validation(self):
        user = User.objects.create_user('viewer', password='TestPass12345')
        self.client.force_login(user)
        response = self.client.get(reverse('pet_detail', args=[self.pet.pk]))
        self.assertContains(response, 'data-validate')
        self.assertContains(response, 'novalidate')
        self.assertContains(response, 'data-check="phone"')

    def test_catalog_contains_api_url_and_favorites(self):
        response = self.client.get(reverse('pet_list'))
        self.assertContains(response, 'data-api="/api/pets/"')
        self.assertContains(response, 'data-fav="%d"' % self.pet.pk)
        self.assertContains(response, 'data-fav-only')

    def test_register_page_has_client_validation(self):
        response = self.client.get(reverse('register'))
        self.assertContains(response, 'data-check="email"')
        self.assertContains(response, 'data-check="password"')


class AdoptionFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'applicant', password='TestPass12345', email='applicant@example.ru',
        )
        self.pet = make_pet()
        self.client.force_login(self.user)

    def test_invalid_application_keeps_values_and_shows_errors(self):
        response = self.client.post(
            reverse('apply_adoption', args=[self.pet.pk]),
            {'phone': '+7 (900) 1', 'message': 'коротко'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Укажите телефон в формате')
        self.assertContains(response, 'не менее 20 символов')
        self.assertContains(response, '+7 (900) 1')
        self.assertEqual(AdoptionApplication.objects.count(), 0)

    def test_valid_application_is_saved_and_redirects(self):
        response = self.client.post(
            reverse('apply_adoption', args=[self.pet.pk]),
            {
                'phone': '+7 (900) 123-45-67',
                'message': 'Живу в частном доме, готов гулять каждый день.',
            },
            follow=True,
        )
        self.assertRedirects(response, reverse('pet_detail', args=[self.pet.pk]))
        application = AdoptionApplication.objects.get()
        self.assertEqual(application.phone, '+7 (900) 123-45-67')
        self.assertEqual(application.applicant, self.user)
        self.assertContains(response, 'Анкета отправлена')

    def test_duplicate_application_is_blocked(self):
        AdoptionApplication.objects.create(
            pet=self.pet, applicant=self.user, phone='+7 (900) 123-45-67',
            message='Первая анкета с достаточной длиной текста.',
        )
        response = self.client.post(
            reverse('apply_adoption', args=[self.pet.pk]),
            {'phone': '+7 (900) 123-45-67', 'message': 'Вторая анкета с достаточной длиной.'},
            follow=True,
        )
        self.assertContains(response, 'уже подали анкету')
        self.assertEqual(AdoptionApplication.objects.count(), 1)

    def test_walk_booking_with_past_date_shows_error(self):
        past = timezone.now() - timedelta(hours=3)
        response = self.client.post(
            reverse('book_walk', args=[self.pet.pk]),
            {'when': past.strftime('%Y-%m-%dT%H:%M')},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Выберите будущую дату и время')
        self.assertEqual(WalkBooking.objects.count(), 0)

    def test_walk_booking_is_created(self):
        future = timezone.now() + timedelta(days=1)
        response = self.client.post(
            reverse('book_walk', args=[self.pet.pk]),
            {'when': future.strftime('%Y-%m-%dT%H:%M')},
        )
        self.assertRedirects(response, reverse('pet_detail', args=[self.pet.pk]))
        self.assertEqual(WalkBooking.objects.count(), 1)


class GuardianshipFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('guardian', password='TestPass12345')
        self.pet = make_pet()
        self.client.force_login(self.user)

    def test_invalid_period_keeps_form_open(self):
        response = self.client.post(reverse('guardianship'), {
            'pet': self.pet.pk, 'amount': 500, 'period': '2026-13',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Укажите период в формате')
        self.assertContains(response, 'value="2026-13"')

    def test_valid_payment_is_saved(self):
        response = self.client.post(reverse('guardianship'), {
            'pet': self.pet.pk, 'amount': 500, 'period': '2026-11',
        })
        self.assertRedirects(response, reverse('guardianship'))
        self.assertEqual(self.user.guardianship_payments.count(), 1)


class RegistrationFlowTests(TestCase):
    def test_duplicate_email_is_rejected(self):
        User.objects.create_user('first', password='TestPass12345', email='same@example.ru')
        form = RegistrationForm(data={
            'username': 'second',
            'email': 'same@example.ru',
            'password1': 'TestPass12345',
            'password2': 'TestPass12345',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_registration_logs_user_in(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.ru',
            'password1': 'TestPass12345',
            'password2': 'TestPass12345',
        })
        self.assertRedirects(response, reverse('index'))
        self.assertTrue(User.objects.filter(username='newuser').exists())
