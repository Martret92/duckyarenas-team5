"""Interfaz local integrada. Toda mutación se delega a servicios de dominio."""
import uuid
from django.conf import settings
from django.templatetags.static import static
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from apps.bank.models import Wallet, Transaction
from apps.bank.services import BankError
from apps.shop.services import ShopError
from apps.duckies.integration_services import (initialize_player_ducky, select_initial_specialization_and_outfit, switch_specialization_and_outfit)
from apps.duckies.models import Ducky, Item, ItemLevel, EvolutionItem, SpecializationItem, InventoryItem, EquippedItem, ItemGrant
from apps.duckies.services import select_outfit, equip_item
from apps.duckies.selectors import get_outfit_catalog
from apps.ecomotor.models import EvolutionStage, LevelThreshold, Specialization, CharacterStats
from apps.shop.models import ShopItem, Purchase
from apps.shop.services import purchase_item
from apps.users.models import UserProfileEcomotor
from .image_registry import ducky_image, item_image
from apps.duckies.item_visuals import image_for_item, outfit_visual_key

SECTIONS = {'dashboard':'Inicio','player':'Mi Pato','evolution':'Evolución','specialization':'Especialización','wardrobe':'Vestuario','inventory':'Inventario','museum':'Museo','shop':'Tienda','wallet':'Banco','rewards':'Rewards','arena':'Arena'}

@login_required
@require_GET
def dashboard(request,section='dashboard'):
    if section not in SECTIONS: raise Http404()
    user=request.user
    ducky=Ducky.objects.select_related('selected_outfit').filter(user=user).first()
    profile=UserProfileEcomotor.objects.filter(user=user).first()
    wallet=Wallet.objects.filter(user=user).first()
    stage=EvolutionStage.objects.filter(code=profile.current_stage_code).first() if profile else None
    levels=LevelThreshold.objects.filter(minimum_xp__gt=profile.historical_xp_total).order_by('minimum_xp') if profile else []
    next_level=levels.first() if profile else None
    historical, spec_outfits = get_outfit_catalog(user)
    for outfit in historical: outfit['image_url'] = item_image(outfit['item'], ducky.sex if ducky else None)
    for outfit in spec_outfits: outfit['image_url'] = item_image(outfit['item'], ducky.sex if ducky else None)
    offers=list(ShopItem.objects.select_related('item','item_level').filter(is_available=True,item__is_active=True))
    visual_key = outfit_visual_key(ducky)
    for offer in offers: offer.image_url=static(image_for_item(offer.item,visual_key)) if image_for_item(offer.item,visual_key) else item_image(offer.item)
    inventory=list(InventoryItem.objects.filter(ducky=ducky).select_related('item','item_level') if ducky else [])
    for entry in inventory: entry.image_url=static(image_for_item(entry.item,visual_key)) if image_for_item(entry.item,visual_key) else item_image(entry.item)
    ctx={'section':section,'section_title':SECTIONS[section],'sections':SECTIONS,
         'user':user,'ducky':ducky,'profile':profile,'wallet':wallet,'stage':stage,
         'next_xp':next_level.minimum_xp if next_level else None,
         'stats':CharacterStats.objects.filter(profile=profile).first() if profile else None,
         'stages':EvolutionStage.objects.order_by('ordinal'),'specializations':Specialization.objects.order_by('name'),
         'outfits':historical,'spec_outfits':spec_outfits,'offers':offers,
         'inventory':inventory,
         'equipped':EquippedItem.objects.filter(ducky=ducky).select_related('inventory_item__item') if ducky else [],
         'item_grants':ItemGrant.objects.filter(ducky=ducky).select_related('item').order_by('-created_at')[:15] if ducky else [],
         'transactions':Transaction.objects.filter(wallet=wallet).order_by('-created_at')[:25] if wallet else [],
         'purchases':Purchase.objects.filter(user=user).select_related('shop_item').order_by('-created_at')[:12],
         'demo_enabled':False,'ducky_image':ducky_image(ducky),'rewards_lab_url':'http://127.0.0.1:8001/',}
    return render(request,'team5_ui/page.html',ctx)

@login_required
@require_POST
def action(request):
    user=request.user
    name=request.POST.get('action','')
    return_to=request.POST.get('return_to','dashboard')
    if return_to not in SECTIONS: return_to='dashboard'
    if name in ('xp','coins','hint'):
        return HttpResponseForbidden('Operación exclusiva del módulo de demostración.')
    key='team5:'+uuid.uuid4().hex
    try:
        if name=='create':
            initialize_player_ducky(user,request.POST.get('sex',''))
        elif name=='specialization':
            profile=UserProfileEcomotor.objects.get(user=user)
            code=request.POST.get('code','')
            if profile.active_specialization_code:
                switch_specialization_and_outfit(user,code,profile.active_specialization_code)
            else:
                select_initial_specialization_and_outfit(user,code)
        elif name=='outfit':
            select_outfit(user,Item.objects.get(pk=int(request.POST.get('item_id','0'))))
        elif name=='equip':
            item=Item.objects.get(pk=int(request.POST.get('item_id','0')))
            level=ItemLevel.objects.get(pk=int(request.POST['code'])) if request.POST.get('code') else None
            equip_item(user,item,level)
        elif name=='buy':
            purchase_item(user,request.POST.get('code',''),operation_key=key,quantity=1)
        else:
            raise ValueError('Operación desconocida.')
    except (BankError,ShopError,ValueError,ValidationError,DatabaseError,Item.DoesNotExist,ItemLevel.DoesNotExist,
            UserProfileEcomotor.DoesNotExist,Wallet.DoesNotExist,Ducky.DoesNotExist) as error:
        messages.error(request,str(error))
    else:
        messages.success(request,'Operación realizada mediante el servicio del equipo.')
    return redirect('team5_ui:'+return_to)


@require_http_methods(['GET','POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('team5_ui:dashboard')
    form=UserCreationForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save()
        login(request,user)
        return redirect('team5_ui:dashboard')
    return render(request,'registration/register.html',{'form':form})
