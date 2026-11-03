import uuid
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .models import ShopItem, Purchase
from .services import purchase_item
@login_required
def catalog(request):
    return render(request,'shop/catalog.html',{'offers':ShopItem.objects.filter(is_available=True,item__is_active=True).select_related('item')})
@login_required
def history(request):
    return render(request,'shop/history.html',{'purchases':Purchase.objects.filter(user=request.user).select_related('shop_item')[:100]})
@login_required
@require_POST
def buy(request):
    try:
        code=request.POST.get('code','')
        if not ShopItem.objects.filter(code=code,is_available=True,item__is_active=True).exists(): raise ValueError('Oferta no disponible')
        purchase_item(request.user,code,operation_key='web:'+uuid.uuid4().hex,quantity=1)
    except (ValueError,ValidationError) as error: messages.error(request,str(error))
    else: messages.success(request,'Compra realizada')
    return redirect('shop:catalog')
