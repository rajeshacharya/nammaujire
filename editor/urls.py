from django.urls import path

from . import views

app_name = 'editor'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('new/', views.project_create, name='project_create'),
    path('<int:project_id>/', views.project_detail, name='project_detail'),
    path('<int:project_id>/upload/', views.upload_asset, name='upload_asset'),
    path('<int:project_id>/qr/', views.import_qr, name='import_qr'),
    path('<int:project_id>/plan/', views.generate_plan, name='generate_plan'),
    path('<int:project_id>/render/', views.render_project, name='render_project'),
    path('<int:project_id>/download/', views.download_output, name='download_output'),
]
