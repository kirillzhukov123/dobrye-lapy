import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Pet, AdoptionApplication, WalkBooking, GuardianshipPayment

PHONE_RE = re.compile(r'^\+?[\d\s\-()]{10,20}$')
PERIOD_RE = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            'name', 'species', 'breed', 'age_months', 'character',
            'rescue_story', 'status', 'enclosure', 'photo',
        ]
        labels = {
            'name': 'Кличка',
            'species': 'Вид',
            'breed': 'Порода',
            'age_months': 'Возраст, месяцев',
            'character': 'Характер',
            'rescue_story': 'История спасения',
            'status': 'Статус',
            'enclosure': 'Вольер',
            'photo': 'Фото',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Например, Бим',
                'data-check': 'required', 'data-max': '100',
            }),
            'species': forms.Select(attrs={'class': 'form-select', 'data-check': 'required'}),
            'breed': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Метис, овчарка, домашняя',
                'data-max': '100',
            }),
            'age_months': forms.NumberInput(attrs={
                'class': 'form-input', 'min': 0, 'max': 360,
                'data-check': 'number', 'data-min': '0', 'data-max': '360',
            }),
            'character': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'data-max': '1000'}),
            'rescue_story': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'data-max': '2000'}),
            'status': forms.Select(attrs={'class': 'form-select', 'data-check': 'required'}),
            'enclosure': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['species'].choices = [('', 'Выберите вид')] + Pet.SPECIES
        self.fields['enclosure'].empty_label = 'Не указан'

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Размер файла не должен превышать 5 МБ.')
        return photo

    def clean_age_months(self):
        age = self.cleaned_data['age_months']
        if age > 360:
            raise forms.ValidationError('Возраст не должен превышать 360 месяцев.')
        return age

    def clean_character(self):
        character = self.cleaned_data.get('character', '')
        if len(character) > 1000:
            raise forms.ValidationError('Характер не должен быть длиннее 1000 символов.')
        return character

    def clean_rescue_story(self):
        story = self.cleaned_data.get('rescue_story', '')
        if len(story) > 2000:
            raise forms.ValidationError('История спасения не должна быть длиннее 2000 символов.')
        return story


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label='Электронная почта',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input', 'autocomplete': 'email', 'data-check': 'email',
        }),
    )
    first_name = forms.CharField(
        label='Имя', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'autocomplete': 'given-name', 'data-max': '150',
        }),
    )
    last_name = forms.CharField(
        label='Фамилия', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'autocomplete': 'family-name', 'data-max': '150',
        }),
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {'username': 'Имя пользователя'}
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input', 'autocomplete': 'username',
                'data-check': 'required', 'data-min': '3', 'data-max': '150',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Повтор пароля'
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input', 'autocomplete': 'new-password',
            'data-check': 'password', 'data-min': '8',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input', 'autocomplete': 'new-password',
            'data-check': 'password2', 'data-match': 'id_password1',
        })
        self.fields['username'].help_text = 'Не более 150 символов. Буквы, цифры и знаки @/./+/-/_.'

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с такой почтой уже зарегистрирован.')
        return email


class ApplicationForm(forms.ModelForm):
    phone = forms.CharField(
        label='Телефон',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+7 (900) 000-00-00',
            'autocomplete': 'tel',
            'data-check': 'phone',
        }),
    )

    class Meta:
        model = AdoptionApplication
        fields = ['phone', 'message']
        labels = {
            'phone': 'Телефон',
            'message': 'Расскажите о себе',
        }
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Почему вы хотите забрать питомца домой и какие условия можете создать?',
                'data-check': 'text',
                'data-min': '20',
                'data-max': '1000',
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        digits = re.sub(r'\D', '', phone)
        if not PHONE_RE.match(phone) or not 10 <= len(digits) <= 15:
            raise forms.ValidationError('Укажите телефон в формате +7 (900) 000-00-00.')
        return phone

    def clean_message(self):
        message = self.cleaned_data['message'].strip()
        if len(message) < 20:
            raise forms.ValidationError('Ответ должен содержать не менее 20 символов.')
        if len(message) > 1000:
            raise forms.ValidationError('Ответ не должен быть длиннее 1000 символов.')
        return message


class WalkForm(forms.ModelForm):
    class Meta:
        model = WalkBooking
        fields = ['when']
        labels = {'when': 'Дата и время прогулки'}
        widgets = {
            'when': forms.DateTimeInput(
                attrs={
                    'class': 'form-input',
                    'type': 'datetime-local',
                    'data-check': 'future',
                },
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def clean_when(self):
        when = self.cleaned_data['when']
        if when <= timezone.now():
            raise forms.ValidationError('Выберите будущую дату и время.')
        return when


class GuardianshipForm(forms.ModelForm):
    class Meta:
        model = GuardianshipPayment
        fields = ['pet', 'amount', 'period']
        labels = {
            'pet': 'Питомец',
            'amount': 'Сумма взноса, ₽',
            'period': 'Период',
        }
        widgets = {
            'pet': forms.Select(attrs={'class': 'form-select', 'data-check': 'required'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-input', 'min': 100, 'step': 100,
                'data-check': 'number', 'data-min': '100', 'data-max': '100000',
            }),
            'period': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '2026-11', 'maxlength': '7',
                'data-check': 'period',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pet'].queryset = Pet.objects.exclude(status='home')
        self.fields['period'].initial = timezone.localdate().strftime('%Y-%m')

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount < 100:
            raise forms.ValidationError('Минимальная сумма взноса - 100 ₽.')
        if amount > 100000:
            raise forms.ValidationError('Максимальная сумма взноса - 100 000 ₽.')
        return amount

    def clean_period(self):
        period = self.cleaned_data['period'].strip()
        if not PERIOD_RE.match(period):
            raise forms.ValidationError('Укажите период в формате ГГГГ-ММ, например 2026-11.')
        return period
