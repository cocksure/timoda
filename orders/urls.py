from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('success/<str:order_number>/', views.order_success, name='success'),
    path('my/', views.order_list, name='list'),
    path('my/<str:order_number>/', views.order_detail, name='detail'),
]