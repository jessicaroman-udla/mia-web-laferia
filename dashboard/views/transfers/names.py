from dashboard.models import Forecast, PurchaseOrder


def add_transfer_display_names(transfers):
    transfers = list(transfers)
    product_codes = {
        transfer.product_code
        for transfer in transfers
        if transfer.product_code
    }

    names = dict(
        Forecast.objects.filter(product_code__in=product_codes)
        .exclude(product_name="")
        .values_list("product_code", "product_name")
    )

    for product_code, product_name in (
        PurchaseOrder.objects.filter(codigo_item__in=product_codes)
        .exclude(item_name="")
        .values_list("codigo_item", "item_name")
    ):
        names.setdefault(product_code, product_name)

    for transfer in transfers:
        transfer.display_name = (
            transfer.product_name
            or names.get(transfer.product_code)
            or "Nombre no disponible"
        )

    return transfers
