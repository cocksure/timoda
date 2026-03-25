from django.urls import path
from .payme import payme_webhook
from .click import click_webhook

urlpatterns = [
    path('payme/', payme_webhook, name='payme_webhook'),
    path('click/', click_webhook, name='click_webhook'),
]