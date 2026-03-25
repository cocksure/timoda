from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.register_view, name='api_register'),
    path('auth/login/', views.login_view, name='api_login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('auth/profile/', views.ProfileView.as_view(), name='api_profile'),
    # Products
    path('categories/', views.CategoryListView.as_view(), name='api_categories'),
    path('products/', views.ProductListView.as_view(), name='api_products'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='api_product_detail'),
    # Orders
    path('orders/', views.OrderListView.as_view(), name='api_orders'),
    path('orders/<str:order_number>/', views.OrderDetailView.as_view(), name='api_order_detail'),
]