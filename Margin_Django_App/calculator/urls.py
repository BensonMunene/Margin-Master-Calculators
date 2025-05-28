from django.urls import path
from . import views

app_name = 'calculator'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/calculate_margin/', views.calculate_margin, name='calculate_margin'),
    path('api/calculate_scenarios/', views.calculate_scenarios, name='calculate_scenarios'),
    path('market_overview/', views.market_overview, name='market_overview'),
    path('price_analysis/', views.price_analysis, name='price_analysis'),
    path('dividend_analysis/', views.dividend_analysis, name='dividend_analysis'),
    path('kelly_criterion/', views.kelly_criterion, name='kelly_criterion'),
]
