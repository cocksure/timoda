from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    # Images
    path('images/<int:pk>/delete/', views.image_delete, name='image_delete'),
    path('images/<int:pk>/primary/', views.image_set_primary, name='image_primary'),
    # Variants
    path('variants/<int:pk>/stock/', views.variant_update_stock, name='variant_stock'),
    path('variants/<int:pk>/delete/', views.variant_delete, name='variant_delete'),
    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    # Banners
    path('banners/', views.banner_list, name='banner_list'),
    path('banners/add/', views.banner_add, name='banner_add'),
    path('banners/<int:pk>/edit/', views.banner_edit, name='banner_edit'),
    path('banners/<int:pk>/delete/', views.banner_delete, name='banner_delete'),
    # Pickup points
    path('pickups/', views.pickup_list, name='pickup_list'),
    path('pickups/add/', views.pickup_edit, name='pickup_add'),
    path('pickups/<int:pk>/edit/', views.pickup_edit, name='pickup_edit'),
    path('pickups/<int:pk>/delete/', views.pickup_delete, name='pickup_delete'),
]