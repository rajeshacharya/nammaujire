from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    path('', views.explore_index, name='explore_index'),
    path('<int:place_id>/', views.place_detail, name='place_detail'),
]