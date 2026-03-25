from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import PhoneForm, OTPVerifyForm, RegisterCompleteForm, LoginForm, ProfileForm, AddressForm
from .models import User, PhoneOTP, Address
from services.sms import send_otp
from django.conf import settings

# ── Registration: 3-step OTP flow ────────────────────────────

def register_step1(request):
    """Step 1: Enter phone number → send OTP."""
    if request.user.is_authenticated:
        return redirect('core:home')

    form = PhoneForm(request.POST or None)
    if form.is_valid():
        phone = form.cleaned_data['phone']

        # Check if phone already registered
        if User.objects.filter(phone=phone).exists():
            messages.error(request, 'Этот номер уже зарегистрирован. Войдите в аккаунт.')
            return redirect('accounts:login')

        # Create OTP and send SMS
        otp = PhoneOTP.create_for_phone(phone, expiry_minutes=settings.OTP_EXPIRY_MINUTES)

        # In DEBUG mode, skip real SMS and show code in message
        if settings.DEBUG and not settings.ESKIZ_EMAIL:
            messages.info(request, f'[DEBUG] Ваш код: {otp.code}')
            sent = True
        else:
            sent = send_otp(phone, otp.code)

        if sent:
            request.session['otp_phone'] = phone
            request.session['otp_id'] = otp.pk
            return redirect('accounts:register_otp')
        else:
            otp.is_used = True
            otp.save()
            messages.error(request, 'Не удалось отправить SMS. Попробуйте позже.')

    return render(request, 'accounts/register_step1.html', {'form': form})


def register_step2_otp(request):
    """Step 2: Verify OTP code."""
    phone = request.session.get('otp_phone')
    otp_id = request.session.get('otp_id')

    if not phone or not otp_id:
        return redirect('accounts:register')

    form = OTPVerifyForm(request.POST or None)
    if form.is_valid():
        try:
            otp = PhoneOTP.objects.get(pk=otp_id, phone=phone)
        except PhoneOTP.DoesNotExist:
            messages.error(request, 'Код недействителен. Начните заново.')
            return redirect('accounts:register')

        if otp.verify(form.cleaned_data['code']):
            request.session['otp_verified'] = True
            return redirect('accounts:register_complete')
        else:
            if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
                messages.error(request, 'Превышено количество попыток. Начните заново.')
                return redirect('accounts:register')
            remaining = settings.OTP_MAX_ATTEMPTS - otp.attempts
            messages.error(request, f'Неверный код. Осталось попыток: {remaining}')

    return render(request, 'accounts/register_step2.html', {'form': form, 'phone': phone})


def register_resend_otp(request):
    """Resend OTP to same phone."""
    phone = request.session.get('otp_phone')
    if not phone:
        return redirect('accounts:register')

    otp = PhoneOTP.create_for_phone(phone, expiry_minutes=settings.OTP_EXPIRY_MINUTES)
    if settings.DEBUG and not settings.ESKIZ_EMAIL:
        messages.info(request, f'[DEBUG] Новый код: {otp.code}')
    else:
        send_otp(phone, otp.code)
        messages.success(request, 'Код отправлен повторно.')

    request.session['otp_id'] = otp.pk
    return redirect('accounts:register_otp')


def register_complete(request):
    """Step 3: Fill name, email, password → create account."""
    phone = request.session.get('otp_phone')
    verified = request.session.get('otp_verified')

    if not phone or not verified:
        return redirect('accounts:register')

    form = RegisterCompleteForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data.get('email') or f'{phone.replace("+", "")}@phone.timoda.uz'
        username = phone.replace('+', '').replace(' ', '')

        user = User(
            username=username,
            email=email,
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            phone=phone,
            phone_verified=True,
        )
        user.set_password(form.cleaned_data['password1'])
        user.save()

        # Clear session
        for key in ('otp_phone', 'otp_id', 'otp_verified'):
            request.session.pop(key, None)

        login(request, user, backend='accounts.backends.EmailOrUsernameBackend')
        messages.success(request, f'Добро пожаловать, {user.first_name}!')
        return redirect('core:home')

    return render(request, 'accounts/register_complete.html', {'form': form, 'phone': phone})


# ── Auth ─────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        next_url = request.GET.get('next', 'core:home')
        return redirect(next_url)
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('core:home')


# ── Profile ──────────────────────────────────────────────────

@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'Профиль обновлён.')
        return redirect('accounts:profile')
    orders = request.user.orders.all()[:5]
    return render(request, 'accounts/profile.html', {'form': form, 'orders': orders})


@login_required
def addresses_view(request):
    addresses = request.user.addresses.all()
    return render(request, 'accounts/addresses.html', {'addresses': addresses})


@login_required
def address_add_view(request):
    form = AddressForm(request.POST or None)
    if form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        address.save()
        messages.success(request, 'Адрес добавлен.')
        return redirect('accounts:addresses')
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Добавить адрес'})


@login_required
def address_edit_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    form = AddressForm(request.POST or None, instance=address)
    if form.is_valid():
        form.save()
        messages.success(request, 'Адрес обновлён.')
        return redirect('accounts:addresses')
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Изменить адрес'})


@login_required
@require_POST
def address_delete_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.success(request, 'Адрес удалён.')
    return redirect('accounts:addresses')