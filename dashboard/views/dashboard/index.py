from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render

from dashboard.models import Forecast, PurchaseOrder, Transfer
from dashboard.views.transfers.names import add_transfer_display_names


@login_required
def dashboard_view(request):

    # =========================================================
    # KPIs PRINCIPALES
    # =========================================================

    total_forecasts = Forecast.objects.filter(
        status="OK"
    ).count()

    total_orders = PurchaseOrder.objects.count()

    total_transfers = Transfer.objects.count()

    total_warehouses = (
        PurchaseOrder.objects
        .exclude(almacen="")
        .values("almacen")
        .distinct()
        .count()
    )

    # =========================================================
    # VALOR TOTAL DE ÓRDENES
    # =========================================================

    total_order_value = (
        PurchaseOrder.objects
        .aggregate(total=Sum("valor_orden"))
        .get("total")
        or Decimal("0")
    )

    # =========================================================
    # DEMANDA TOTAL PRONOSTICADA
    # =========================================================

    total_forecast_demand = (
        Forecast.objects
        .filter(status="OK")
        .aggregate(total=Sum("demanda_total"))
        .get("total")
        or 0
    )

    # =========================================================
    # DEMANDA SEMANAL
    # Suma las semanas de todos los productos
    # =========================================================

    weekly_totals = []

    forecasts = (
        Forecast.objects
        .filter(status="OK")
        .values_list("demanda_semanal", flat=True)
    )

    for weekly_demand in forecasts:

        if not isinstance(weekly_demand, list):
            continue

        while len(weekly_totals) < len(weekly_demand):
            weekly_totals.append(0)

        for index, value in enumerate(weekly_demand):
            try:
                weekly_totals[index] += float(value or 0)
            except (ValueError, TypeError):
                continue

    weekly_labels = [
        f"Semana {index + 1}"
        for index in range(len(weekly_totals))
    ]

    weekly_totals = [
        round(value, 2)
        for value in weekly_totals
    ]

    # =========================================================
    # PRODUCTOS POR CATEGORÍA
    # =========================================================

    category_queryset = (
        Forecast.objects
        .filter(status="OK")
        .values("categoria")
        .annotate(total=Count("id"))
        .order_by("categoria")
    )

    category_labels = []
    category_values = []

    for category in category_queryset:

        label = category["categoria"]

        if not label:
            label = "Sin categoría"

        category_labels.append(label)
        category_values.append(category["total"])

    # =========================================================
    # TOP ÓRDENES DE COMPRA
    # =========================================================

    top_orders = (
        PurchaseOrder.objects
        .order_by("-valor_orden")[:10]
    )

    # =========================================================
    # TRANSFERENCIAS RECIENTES
    # =========================================================

    recent_transfers = add_transfer_display_names(
        Transfer.objects
        .order_by("-id")[:10]
    )

    # =========================================================
    # TOP ALMACENES POR ÓRDENES
    # =========================================================

    warehouses = (
        PurchaseOrder.objects
        .exclude(almacen="")
        .values("almacen")
        .annotate(
            total_orders=Count("id"),
            total_value=Sum("valor_orden")
        )
        .order_by("-total_value")[:5]
    )

    # =========================================================
    # CONTEXTO
    # =========================================================

    context = {
        "total_forecasts": total_forecasts,
        "total_orders": total_orders,
        "total_transfers": total_transfers,
        "total_warehouses": total_warehouses,

        "total_order_value": total_order_value,
        "total_forecast_demand": total_forecast_demand,

        "weekly_labels": weekly_labels,
        "weekly_totals": weekly_totals,

        "category_labels": category_labels,
        "category_values": category_values,

        "top_orders": top_orders,
        "recent_transfers": recent_transfers,
        "warehouses": warehouses,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )
