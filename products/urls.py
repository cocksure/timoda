from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('favorites/', views.favorite_list, name='favorites'),
    path('categories/', views.category_list, name='categories'),
    path('favorite/<int:product_id>/toggle/', views.favorite_toggle, name='favorite_toggle'),
    path('variant/<int:variant_id>/stock/', views.get_variant_stock, name='variant_stock'),
    path('<slug:slug>/', views.product_detail, name='detail'),
    path('<slug:slug>/review/', views.add_review, name='add_review'),
]