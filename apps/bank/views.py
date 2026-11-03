from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Wallet, Transaction
@login_required
def wallet(request):
    return render(request,'bank/wallet.html',{'wallet':Wallet.objects.filter(user=request.user).first()})
@login_required
def transactions(request):
    return render(request,'bank/transactions.html',{'transactions':Transaction.objects.filter(wallet__user=request.user)[:100]})
