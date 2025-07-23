from django.urls import path
from . import views

app_name = 'etf_analyzer'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/get-data/', views.get_data, name='get_data'),
    path('api/download-matrix/', views.download_matrix, name='download_matrix'),
    path('api/download-returns/', views.download_annual_returns, name='download_returns'),
]