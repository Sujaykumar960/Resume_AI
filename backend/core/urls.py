from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('analyze/', views.analyze, name='analyze'),
    path('results/<uuid:pk>/', views.results, name='results'),
    path('chat/<uuid:pk>/', views.chat, name='chat'),
    path('history/', views.history_list, name='history'),
    path('mock-interviews/', views.mock_interviews, name='mock_interviews'),
    path('career-opportunities/', views.career_opportunities, name='career_opportunities'),
]
