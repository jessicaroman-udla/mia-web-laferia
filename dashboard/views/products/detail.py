from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import Http404
from django.shortcuts import render

from dashboard.models import Forecast, PurchaseOrder, Transfer


@login_required
def product_detail(request, product_code):
    forecast = Forecast.objects.filter(product_code=product_code).first()
    orders = PurchaseOrder.objects.filter(codigo_item=product_code).order_by("almacen")
    transfers = Transfer.objects.filter(product_code=product_code).order_by("-id")

    if forecast is None and not orders.exists() and not transfers.exists():
        raise Http404("Producto no encontrado")

    first_order = orders.first()
    first_transfer = transfers.exclude(product_name="").first()
    product_name = (
        forecast.product_name
        if forecast
        else first_order.item_name
        if first_order
        else first_transfer.product_name
        if first_transfer
        else "Sin nombre registrado"
    )

    weekly_forecast = []
    if forecast and isinstance(forecast.demanda_semanal, list):
        weekly_forecast = [
            {"week": index + 1, "value": value}
            for index, value in enumerate(forecast.demanda_semanal)
        ]

    order_totals = orders.aggregate(
        units=Sum("cantidad_a_ordenar"), value=Sum("valor_orden")
    )
    transfer_quantity = (
        transfers.aggregate(total=Sum("cantidad"))["total"] or 0
    )

    return render(
        request,
        "products/detail.html",
        {
            "product_code": product_code,
            "product_name": product_name,
            "forecast": forecast,
            "weekly_forecast": weekly_forecast,
            "orders": orders,
            "transfers": transfers,
            "order_count": orders.count(),
            "order_units": order_totals["units"] or 0,
            "order_value": order_totals["value"] or Decimal("0"),
            "transfer_count": transfers.count(),
            "transfer_quantity": transfer_quantity,
        },
    )
