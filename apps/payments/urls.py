from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('plans/', views.payment_plans, name='plans'),
]
