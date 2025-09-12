from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def payment_plans(request):
    """Planes de pago"""
    return render(request, 'payments/plans.html')
