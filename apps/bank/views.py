from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import Wallet
from .services import transaction_history, wallet_summary


@login_required
@require_GET
def wallet_view(request):
    """Show only the authenticated user's wallet and ledger movements."""
    try:
        wallet = Wallet.objects.filter(user=request.user).first()
        if wallet is None:
            context = {
                "wallet": None,
                "summary": None,
                "transactions": [],
                "page_obj": None,
            }
            return render(request, "bank/wallet.html", context)

        summary = wallet_summary(request.user)
        page_obj = Paginator(transaction_history(request.user), 25).get_page(
            request.GET.get("page", 1)
        )
        return render(
            request,
            "bank/wallet.html",
            {
                "wallet": wallet,
                "summary": summary,
                "transactions": page_obj.object_list,
                "page_obj": page_obj,
            },
        )
    except DatabaseError:
        return HttpResponse("Servicio no disponible temporalmente.", status=503)
