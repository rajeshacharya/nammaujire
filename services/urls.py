from django.urls import path
from . import views

urlpatterns = [
    path('', views.services_list, name='services_list'),
    path('book/<int:provider_id>/', views.book_service, name='book_service'),
    path('update-booking/<int:booking_id>/<str:status>/', views.update_booking_status, name='update_booking_status'),
]

