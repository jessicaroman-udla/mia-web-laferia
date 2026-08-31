from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import render

from dashboard.models import Transfer
from dashboard.views.transfers.names import add_transfer_display_names


@login_required
def transfer_list(request):
    transfers = Transfer.objects.all()

    search = request.GET.get("search", "").strip()
    origen = request.GET.get("origen", "").strip()
    destino = request.GET.get("destino", "").strip()

    if search:
        transfers = transfers.filter(
            Q(product_code__icontains=search)
            | Q(product_name__icontains=search)
        )

    if origen:
        transfers = transfers.filter(origen=origen)

    if destino:
        transfers = transfers.filter(destino=destino)

    total_quantity = transfers.aggregate(total=Sum("cantidad"))["total"] or 0
    page_obj = Paginator(
        transfers.order_by("-id"), 25
    ).get_page(request.GET.get("page"))
    add_transfer_display_names(page_obj.object_list)

    warehouses = sorted(
        set(
            Transfer.objects.exclude(origen="").values_list("origen", flat=True)
        )
        | set(
            Transfer.objects.exclude(destino="").values_list("destino", flat=True)
        )
    )

    return render(
        request,
        "transfers/transfers.html",
        {
            "page_obj": page_obj,
            "search": search,
            "origen": origen,
            "destino": destino,
            "warehouses": warehouses,
            "total_quantity": total_quantity,
        },
    )
