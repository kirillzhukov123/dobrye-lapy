from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Pet, AdoptionApplication, WalkBooking, GuardianshipPayment


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
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Например, Бим'}),
            'species': forms.Select(attrs={'class': 'form-select'}),
            'breed': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Метис, овчарка, домашняя'}),
            'age_months': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'max': 360}),
            'character': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
            'rescue_story': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'enclosure': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['species'].choices = [('', 'Выберите вид')] + Pet.SPECIES
        self.fields['enclosure'].empty_label = 'Не указан'


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label='Электронная почта',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'autocomplete': 'email'}),
    )
    first_name = forms.CharField(
        label='Имя', required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'autocomplete': 'given-name'}),
    )
    last_name = forms.CharField(
        label='Фамилия', required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'autocomplete': 'family-name'}),
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {'username': 'Имя пользователя'}
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'autocomplete': 'username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Повтор пароля'
        self.fields['password1'].widget.attrs.update({'class': 'form-input', 'autocomplete': 'new-password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input', 'autocomplete': 'new-password'})
        self.fields['username'].help_text = 'Не более 150 символов. Буквы, цифры и знаки @/./+/-/_.'

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с такой почтой уже зарегистрирован.')
        return email


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = AdoptionApplication
        fields = ['message']
        labels = {'message': 'Расскажите о себе'}
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Почему вы хотите забрать питомца домой и какие условия можете создать?',
            }),
        }

    def clean_message(self):
        message = self.cleaned_data['message'].strip()
        if len(message) < 20:
            raise forms.ValidationError('Ответ должен содержать не менее 20 символов.')
        return message


class WalkForm(forms.ModelForm):
    class Meta:
        model = WalkBooking
        fields = ['when']
        labels = {'when': 'Дата и время прогулки'}
        widgets = {
            'when': forms.DateTimeInput(
                attrs={'class': 'form-input', 'type': 'datetime-local'},
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
            'pet': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'min': 100, 'step': 100}),
            'period': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '2026-11'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pet'].queryset = Pet.objects.exclude(status='home')
        self.fields['period'].initial = timezone.localdate().strftime('%Y-%m')

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount < 100:
            raise forms.ValidationError('Минимальная сумма взноса — 100 ₽.')
        return amount
