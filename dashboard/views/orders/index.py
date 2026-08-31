from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import render

from dashboard.models import PurchaseOrder


@login_required
def order_list(request):
    orders = PurchaseOrder.objects.all()

    search = request.GET.get("search", "").strip()
    almacen = request.GET.get("almacen", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    modelo = request.GET.get("modelo", "").strip()

    if search:
        orders = orders.filter(
            Q(codigo_item__icontains=search)
            | Q(item_name__icontains=search)
        )

    if almacen:
        orders = orders.filter(almacen=almacen)

    if categoria:
        orders = orders.filter(categoria=categoria)

    if modelo:
        orders = orders.filter(modelo_ganador=modelo)

    totals = orders.aggregate(
        total_units=Sum("cantidad_a_ordenar"),
        total_value=Sum("valor_orden"),
    )

    page_obj = Paginator(
        orders.order_by("codigo_item", "almacen"), 25
    ).get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "search": search,
        "almacen": almacen,
        "categoria": categoria,
        "modelo": modelo,
        "warehouses": distinct_values("almacen"),
        "categories": distinct_values("categoria"),
        "models": distinct_values("modelo_ganador", exclude_blank=True),
        "total_units": totals["total_units"] or 0,
        "total_value": totals["total_value"] or 0,
    }

    return render(request, "orders/orders.html", context)


def distinct_values(field, exclude_blank=False):
    values = PurchaseOrder.objects.all()
    if exclude_blank:
        values = values.exclude(**{field: ""})
    return values.values_list(field, flat=True).distinct().order_by(field)
