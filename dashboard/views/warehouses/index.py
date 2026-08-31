from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render

from dashboard.models import PurchaseOrder, Transfer


@login_required
def warehouse_list(request):
    warehouses = defaultdict(
        lambda: {
            "order_count": 0,
            "order_value": Decimal("0"),
            "outgoing_count": 0,
            "outgoing_quantity": 0,
            "incoming_count": 0,
            "incoming_quantity": 0,
        }
    )

    for row in (
        PurchaseOrder.objects.exclude(almacen="")
        .values("almacen")
        .annotate(order_count=Count("id"), order_value=Sum("valor_orden"))
    ):
        warehouses[row["almacen"]].update(
            order_count=row["order_count"],
            order_value=row["order_value"] or Decimal("0"),
        )

    for row in (
        Transfer.objects.exclude(origen="")
        .values("origen")
        .annotate(movement_count=Count("id"), quantity=Sum("cantidad"))
    ):
        warehouses[row["origen"]].update(
            outgoing_count=row["movement_count"],
            outgoing_quantity=row["quantity"] or 0,
        )

    for row in (
        Transfer.objects.exclude(destino="")
        .values("destino")
        .annotate(movement_count=Count("id"), quantity=Sum("cantidad"))
    ):
        warehouses[row["destino"]].update(
            incoming_count=row["movement_count"],
            incoming_quantity=row["quantity"] or 0,
        )

    warehouse_rows = []
    for name, values in sorted(warehouses.items()):
        warehouse_rows.append(
            {
                "name": name,
                **values,
                "movement_count": (
                    values["outgoing_count"] + values["incoming_count"]
                ),
                "net_quantity": (
                    values["incoming_quantity"] - values["outgoing_quantity"]
                ),
            }
        )

    return render(
        request,
        "warehouses/warehouses.html",
        {
            "warehouses": warehouse_rows,
            "total_warehouses": len(warehouse_rows),
            "total_orders": sum(row["order_count"] for row in warehouse_rows),
            "total_order_value": sum(
                (row["order_value"] for row in warehouse_rows), Decimal("0")
            ),
            "total_movements": Transfer.objects.count(),
        },
    )
