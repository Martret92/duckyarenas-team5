"""Acciones opcionales y restringidas: nunca importadas por la interfaz normal."""
import uuid
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from apps.bank.services import adjust_wallet
from apps.duckies.integration_services import grant_xp_and_sync_outfit
from apps.duckies.models import Item
from apps.duckies.services import grant_item

ALLOWED_SECTIONS = ('dashboard','player','evolution','specialization','wardrobe','inventory','museum','shop','wallet','rewards','arena')

def authorized(request):
    return (getattr(settings, 'TEAM5_DEMO_ENABLED', False) and settings.DEBUG
        and request.user.is_authenticated and request.user.is_staff
        and request.META.get('REMOTE_ADDR') in ('127.0.0.1', '::1')
        and request.get_host().split(':')[0] in ('localhost', '127.0.0.1', 'testserver')
        and str(settings.DATABASES['default']['NAME']).endswith('db_team5_demo.sqlite3'))

@login_required
@require_POST
def action(request):
    if not authorized(request):
        return HttpResponseForbidden('Herramientas de demostración no autorizadas.')
    section=request.POST.get('return_to','dashboard')
    if section not in ALLOWED_SECTIONS: section='dashboard'
    name=request.POST.get('action','')
    key='team5:demo:'+uuid.uuid4().hex
    try:
        if name in ('xp','coins'):
            amount=int(request.POST.get('amount','0'))
            if not 1 <= amount <= 1000000:
                raise ValueError('Cantidad fuera del rango permitido (1–1.000.000).')
            if name == 'xp':
                grant_xp_and_sync_outfit(request.user, amount, key)
            else:
                adjust_wallet(request.user,amount,operation_key=key,description='Crédito manual de demostración',source='team5_demo',issuing_entity='Team5Demo')
        elif name == 'hint':
            hint=Item.objects.filter(category=Item.HINT,is_active=True).first()
            if hint is None: raise ValueError('No hay HINT de prueba en el catálogo.')
            grant_item(request.user,hint,1,key,reference_type='team5_demo',reference_id=key)
        else:
            return HttpResponseForbidden('Acción no autorizada.')
    except (ValueError, ValidationError, DatabaseError) as error:
        messages.error(request,str(error))
    else:
        messages.success(request,'Operación de demostración registrada.')
    return redirect('team5_ui:'+section)
