import random
import string

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, View, UpdateView
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from .forms import ProfileEditForm

from .forms import RegistrationForm
from .models import CustomUser

User = get_user_model()  # Получаем модель пользователя


class RegistrationView(CreateView):
    form_class = RegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.is_staff = True
        user.is_superuser = False
        # Хэшируем пароль перед сохранением
        user.password = make_password(form.cleaned_data['password'])
        user.save()

        # Генерация письма для подтверждения email
        current_site = get_current_site(self.request)
        subject = 'Verify your email'
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        message = render_to_string('users/verify_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': uid,
            'token': token,
        })

        # Отправляем письмо
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message
        )

        return super().form_valid(form)


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email verified. You can now log in.")
        return redirect('users:login')
    else:
        messages.error(request, "Verification link is invalid.")
        return redirect('users:register')


class PasswordResetView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'users/password_reset.html')

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()

        if user:
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user.password = make_password(new_password)
            user.save()

            send_mail(
                'Password Reset',
                f'Your new password is: {new_password}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            messages.success(request, "A new password has been sent to your email.")
        else:
            messages.error(request, "Email not found.")

        return redirect('users:login')


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileEditForm
    template_name = 'users/edit_profile.html'
    success_url = reverse_lazy('catalog:index')

    def get_object(self):
        return self.request.user  # Обновляем данные только текущего пользователя
