from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('solutions/', views.solutions, name='solutions'),
    path('resources/', views.resources, name='resources'),
    path('lucid-team/', views.lucid_team, name='lucid_team'),
    path('findpartai/', views.findpartai_landing, name='findpartai_landing'),
    path('mechai/', views.mechai_landing, name='mechai_landing'),
    path('automotriz/', views.automotive, name='automotive'),
    path('custom-service/', views.custom_service, name='custom_service'),
    path('masterclass-ia-centro-automotriz/', views.masterclass_auto_ai, name='masterclass_auto_ai'),
    path('dental-ai/', views.dental_ai_landing, name='dental_ai_landing'),
    path('agencia-ia-ibague/', views.ibague_ai_landing, name='ibague_ai_landing'),
    path('agencia-ia-bogota/', views.bogota_ai_landing, name='bogota_ai_landing'),
    path('agencia-ia-cali/', views.cali_ai_landing, name='cali_ai_landing'),
    path('agencia-ia-medellin/', views.medellin_ai_landing, name='medellin_ai_landing'),
    path('agencia-ia-barranquilla/', views.barranquilla_ai_landing, name='barranquilla_ai_landing'),
    path('agencia-ia-cartagena/', views.cartagena_ai_landing, name='cartagena_ai_landing'),
    path('politica-privacidad-wh-conv/', views.privacy_policy, name='privacy_policy'),
    path('condiciones-servicio-wh-conv/', views.terms_of_service, name='terms_of_service'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap, name='sitemap'),
]