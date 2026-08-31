import csv
import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from dashboard.models import Forecast, PurchaseOrder, Transfer


DATA_DIR = settings.BASE_DIR / "data"

FORECAST_FILE = DATA_DIR / "pronostico_futuro_producto.csv"
ORDERS_FILE = DATA_DIR / "resultados_milp_piloto.csv"
TRANSFERS_FILE = DATA_DIR / "resultado_ga_transferencias.json"


def to_float(value, default=0.0):
    if value is None:
        return default

    value = str(value).strip()

    if value == "":
        return default

    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def to_decimal(value, default="0"):
    if value is None:
        return Decimal(default)

    value = str(value).strip()

    if value == "":
        return Decimal(default)

    try:
        return Decimal(value)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def parse_json_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    value = str(value).strip()

    if not value:
        return []

    try:
        data = json.loads(value)

        if isinstance(data, list):
            return data

    except json.JSONDecodeError:
        pass

    return []


class Command(BaseCommand):
    help = "Carga los resultados de los modelos desde CSV/JSON hacia MySQL."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.NOTICE("Iniciando carga de datos...")
        )

        self.validate_files()

        try:
            with transaction.atomic():
                self.clear_tables()

                self.load_forecasts()
                self.load_purchase_orders()
                self.load_transfers()

        except Exception as error:
            self.stdout.write(
                self.style.ERROR(
                    f"Error durante la carga: {error}"
                )
            )
            raise

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Carga completada correctamente."
            )
        )

        self.show_summary()

    def validate_files(self):
        files = [
            FORECAST_FILE,
            ORDERS_FILE,
            TRANSFERS_FILE,
        ]

        missing_files = []

        for file_path in files:
            if not file_path.exists():
                missing_files.append(str(file_path))

        if missing_files:
            raise FileNotFoundError(
                "No se encontraron los siguientes archivos:\n"
                + "\n".join(missing_files)
            )

    def clear_tables(self):
        self.stdout.write(
            "Limpiando datos anteriores..."
        )

        Forecast.objects.all().delete()
        PurchaseOrder.objects.all().delete()
        Transfer.objects.all().delete()

    def load_forecasts(self):
        self.stdout.write(
            f"Leyendo pronósticos: {FORECAST_FILE.name}"
        )

        forecasts = []

        with open(
            FORECAST_FILE,
            mode="r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                status = (
                    row.get("status", "")
                    .strip()
                    .upper()
                )

                if status != "OK":
                    continue

                forecast = Forecast(
                    product_code=(
                        row.get("product_code", "")
                        .strip()
                    ),

                    product_name=(
                        row.get("product_name", "")
                        .strip()
                    ),

                    categoria=(
                        row.get("categoria", "")
                        .strip()
                    ),

                    modelo_ganador=(
                        row.get("modelo_ganador", "")
                        .strip()
                    ),

                    demanda_semanal=parse_json_list(
                        row.get(
                            "demanda_pronosticada_semanal"
                        )
                    ),

                    demanda_total=to_float(
                        row.get(
                            "demanda_pronosticada_total"
                        )
                    ),

                    horizon_weeks=int(
                        to_float(
                            row.get("horizon_weeks"),
                            4
                        )
                    ),

                    status=status,
                )

                forecasts.append(forecast)

        Forecast.objects.bulk_create(
            forecasts,
            batch_size=1000
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Pronósticos cargados: {len(forecasts)}"
            )
        )

    def load_purchase_orders(self):
        self.stdout.write(
            f"Leyendo órdenes: {ORDERS_FILE.name}"
        )

        orders = []

        with open(
            ORDERS_FILE,
            mode="r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                genera_orden = to_float(
                    row.get("genera_orden")
                )

                if genera_orden != 1:
                    continue

                cantidad = to_float(
                    row.get("cantidad_a_ordenar")
                )

                costo = to_decimal(
                    row.get("costo")
                )

                valor_orden = (
                    Decimal(str(cantidad))
                    * costo
                )

                order = PurchaseOrder(
                    codigo_item=(
                        row.get("codigo_item", "")
                        .strip()
                    ),

                    item_name=(
                        row.get("item_name", "")
                        .strip()
                    ),

                    almacen=(
                        row.get("almacen", "")
                        .strip()
                    ),

                    categoria=(
                        row.get("categoria", "")
                        .strip()
                    ),

                    modelo_ganador=(
                        row.get("modelo_ganador", "")
                        .strip()
                    ),

                    disponible=to_float(
                        row.get("disponible")
                    ),

                    forecasted_demand=to_float(
                        row.get("forecasted_demand")
                    ),

                    punto_reorden=to_float(
                        row.get("punto_reorden")
                    ),

                    cantidad_a_ordenar=cantidad,

                    costo=costo,

                    valor_orden=valor_orden,

                    moq=to_float(
                        row.get("moq")
                    ),

                    lead_time=to_float(
                        row.get("lead_time")
                    ),

                    mape=to_float(
                        row.get("mape"),
                        None
                    ),
                )

                orders.append(order)

        PurchaseOrder.objects.bulk_create(
            orders,
            batch_size=1000
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Órdenes cargadas: {len(orders)}"
            )
        )

    def load_transfers(self):
        self.stdout.write(
            f"Leyendo transferencias: {TRANSFERS_FILE.name}"
        )

        transfers = []
        product_names = dict(
            Forecast.objects.exclude(product_name="")
            .values_list("product_code", "product_name")
        )

        for product_code, product_name in (
            PurchaseOrder.objects.exclude(item_name="")
            .values_list("codigo_item", "item_name")
        ):
            product_names.setdefault(product_code, product_name)

        with open(
            TRANSFERS_FILE,
            mode="r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        for product_data in data:
            product_code = str(
                product_data.get("product", "")
            ).strip()

            transfer_plan = (
                product_data.get("transfer_plan", [])
                or []
            )

            for movement in transfer_plan:
                quantity = to_float(
                    movement.get("quantity")
                )

                if quantity <= 0:
                    continue

                transfer = Transfer(
                    product_code=product_code,

                    product_name=product_names.get(
                        product_code,
                        ""
                    ),

                    origen=str(
                        movement.get("origin", "")
                    ).strip(),

                    destino=str(
                        movement.get(
                            "destination",
                            ""
                        )
                    ).strip(),

                    cantidad=quantity,
                )

                transfers.append(transfer)

        Transfer.objects.bulk_create(
            transfers,
            batch_size=1000
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Transferencias cargadas: {len(transfers)}"
            )
        )

    def show_summary(self):
        self.stdout.write("")
        self.stdout.write("Resumen:")

        self.stdout.write(
            f"  Pronósticos: "
            f"{Forecast.objects.count()}"
        )

        self.stdout.write(
            f"  Órdenes de compra: "
            f"{PurchaseOrder.objects.count()}"
        )

        self.stdout.write(
            f"  Transferencias: "
            f"{Transfer.objects.count()}"
        )
