from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Registration (3 steps)
    path('register/', views.register_step1, name='register'),
    path('register/otp/', views.register_step2_otp, name='register_otp'),
    path('register/otp/resend/', views.register_resend_otp, name='register_resend'),
    path('register/complete/', views.register_complete, name='register_complete'),
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('addresses/', views.addresses_view, name='addresses'),
    path('addresses/add/', views.address_add_view, name='address_add'),
    path('addresses/<int:pk>/edit/', views.address_edit_view, name='address_edit'),
    path('addresses/<int:pk>/delete/', views.address_delete_view, name='address_delete'),
]