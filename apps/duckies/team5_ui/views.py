import uuid
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect,render
from django.views.decorators.http import require_POST
from apps.duckies.integration_services import grant_xp_and_sync_outfit, select_initial_specialization_and_outfit, switch_specialization_and_outfit
from apps.duckies.services import select_outfit, equip_item
from apps.duckies.models import Item, ItemLevel
from apps.shop.services import purchase_item
from apps.users.models import UserProfileEcomotor
from .demo_services import demo_user, provision, credit_demo, local_initialization_config
from .forms import ActionForm
from .selectors import state

SECTIONS={"dashboard":"Inicio","player":"Mi Pato","evolution":"Evolución","specialization":"Especialización","wardrobe":"Vestuario","inventory":"Inventario","museum":"Museo","shop":"Tienda","wallet":"Banco","arena":"Arena","rewards":"Recompensas"}

def _guard(request):
    # Sin login SOLO para pruebas locales; nunca público, incluso si DEBUG=True.
    if not settings.DEBUG or request.get_host().split(":")[0].lower() not in ("127.0.0.1","localhost","[::1]"):
        raise Http404("Interfaz local deshabilitada")

def page(request,section="dashboard"):
    _guard(request)
    if section not in SECTIONS:raise Http404()
    user=demo_user()
    data=state(user)
    data.update({"rewards_lab_url":"http://127.0.0.1:8002/demo/objetivo-persistente/", "section":section,"section_title":SECTIONS[section],"sections":SECTIONS,"demo_user":user})
    return render(request,"team5_ui/page.html",data)

@require_POST
def action(request):
    _guard(request)
    form=ActionForm(request.POST)
    target=request.POST.get("return_to","dashboard")
    if target not in SECTIONS:target="dashboard"
    if not form.is_valid():
        messages.error(request,"Datos inválidos: revisa la cantidad y la selección.")
        return redirect("team5_ui:"+target)
    d=form.cleaned_data
    user=demo_user()
    try:
        act=d["action"]
        if act=="create":
            provision(user,d["sex"] or "male")
            messages.success(request,"¡Tu Ducky está preparado! El género no puede modificarse después de crear el personaje.")
        elif act=="coins":
            credit_demo(user,d["amount"] or 100,"ui-credit-"+uuid.uuid4().hex)
            messages.success(request,f"Añadidas {d['amount'] or 100} Ducky Coins mediante Bank.")
        elif act=="xp":
            with local_initialization_config():
                grant_xp_and_sync_outfit(user,d["amount"] or 100,"ui-xp-"+uuid.uuid4().hex)
            messages.success(request,f"Añadidos {d['amount'] or 100} XP y sincronizada la vestimenta.")
        elif act=="specialization":
            profile=UserProfileEcomotor.objects.get(user=user)
            code=d["code"]
            with local_initialization_config():
                if profile.active_specialization_code:
                    switch_specialization_and_outfit(user,code,profile.active_specialization_code)
                else:
                    select_initial_specialization_and_outfit(user,code)
            messages.success(request,"Especialización actualizada.")
        elif act=="outfit":
            select_outfit(user,Item.objects.get(pk=d["item_id"]))
            messages.success(request,"Vestimenta seleccionada.")
        elif act=="equip":
            item=Item.objects.get(pk=d["item_id"])
            level=ItemLevel.objects.filter(pk=d["code"],item=item).first() if d["code"] else None
            equip_item(user,item,level)
            messages.success(request,"Objeto equipado.")
        elif act=="buy":
            purchase_item(user,d["code"],operation_key="ui-buy-"+uuid.uuid4().hex,quantity=d["quantity"] or 1)
            messages.success(request,"Compra realizada: Bank ha cobrado y Duckies ha recibido el objeto.")
    except Exception as exc:
        # Demo local: errores funcionales legibles sin traceback al navegador.
        messages.error(request,f"No se pudo completar: {exc}")
    return redirect("team5_ui:"+target)
