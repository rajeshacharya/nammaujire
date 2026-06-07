from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', views.request_otp_view, name='login'),
    path('verify/', views.verify_otp_view, name='verify_otp'),
    path('complete-profile/', views.complete_profile_view, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
