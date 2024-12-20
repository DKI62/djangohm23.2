from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from .views import ProfileEditView

app_name = 'users'

urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('verify/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('login/', LoginView.as_view(template_name='users/login.html'), name='login'),
    path('password_reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('profile/edit/', ProfileEditView.as_view(), name='edit_profile'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
]
