import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Address


class PhoneForm(forms.Form):
    """Step 1: enter phone number."""
    phone = forms.CharField(
        label='Номер телефона',
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': '+998 90 123 45 67',
            'autocomplete': 'tel',
            'inputmode': 'tel',
        })
    )

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        # Normalize
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        if not phone.startswith('+'):
            phone = '+' + phone
        if not re.match(r'^\+998\d{9}$', phone):
            raise forms.ValidationError('Введите корректный узбекский номер: +998 XX XXX XX XX')
        return phone


class OTPVerifyForm(forms.Form):
    """Step 2: verify OTP code."""
    code = forms.CharField(
        label='Код из SMS',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': '------',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'class': 'otp-input',
        })
    )


class RegisterCompleteForm(forms.ModelForm):
    """Step 3: complete registration after OTP verified."""
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}))
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Фамилия'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@example.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Этот email уже используется.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Пароли не совпадают.')
        return cleaned


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Email или логин',
        widget=forms.TextInput(attrs={'placeholder': 'email@example.com или номер'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'})
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'birth_date', 'avatar']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.TextInput(attrs={'placeholder': '+998 90 123 45 67'}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['type', 'full_name', 'phone', 'address_line1', 'address_line2',
                  'city', 'region', 'postal_code', 'country', 'is_default']