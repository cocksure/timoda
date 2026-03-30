from django.urls import path
from . import views

app_name = 'tgbot'

urlpatterns = [
    path('webhook/', views.webhook, name='webhook'),
    path('auth/', views.telegram_auth, name='auth'),
    path('auto-login/<str:token>/', views.auto_login, name='auto_login'),
]