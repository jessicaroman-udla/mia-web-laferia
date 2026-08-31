from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from dashboard.management.commands.load_model_outputs import to_float
from dashboard.models import Forecast, PurchaseOrder, Transfer


class OrderListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="tester", password="secret123"
        )
        cls.order_a = PurchaseOrder.objects.create(
            codigo_item="ABC-1",
            item_name="Arroz premium",
            almacen="NORTE",
            categoria="A",
            modelo_ganador="XGBoost",
            cantidad_a_ordenar=10,
            valor_orden=Decimal("25.50"),
        )
        PurchaseOrder.objects.create(
            codigo_item="XYZ-2",
            item_name="Aceite",
            almacen="SUR",
            categoria="B",
            modelo_ganador="Prophet",
            cantidad_a_ordenar=5,
            valor_orden=Decimal("12.25"),
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_orders_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse("orders"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('orders')}")

    def test_orders_context_contains_totals_and_filter_options(self):
        response = self.client.get(reverse("orders"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 2)
        self.assertEqual(response.context["total_units"], 15)
        self.assertEqual(response.context["total_value"], Decimal("37.75"))
        self.assertQuerySetEqual(response.context["warehouses"], ["NORTE", "SUR"])

    def test_orders_applies_combined_filters_and_filtered_totals(self):
        response = self.client.get(
            reverse("orders"),
            {"search": "arroz", "almacen": "NORTE", "categoria": "A", "modelo": "XGBoost"},
        )
        self.assertEqual(list(response.context["page_obj"]), [self.order_a])
        self.assertEqual(response.context["total_units"], 10)
        self.assertEqual(response.context["total_value"], Decimal("25.50"))


class LoaderHelperTests(TestCase):
    def test_to_float_returns_default_for_invalid_value(self):
        self.assertEqual(to_float("invalid", default=7.5), 7.5)


class DashboardViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="dashboard-user", password="secret123"
        )
        Forecast.objects.create(
            product_code="ABC-1",
            product_name="Arroz",
            categoria="A",
            modelo_ganador="XGBoost",
            demanda_semanal=[10, "20", None, "invalid"],
            demanda_total=30,
            status="OK",
        )
        Forecast.objects.create(
            product_code="XYZ-2",
            product_name="Aceite",
            categoria="B",
            modelo_ganador="Prophet",
            demanda_semanal=[5, 7, 9],
            demanda_total=21,
            status="ERROR",
        )
        PurchaseOrder.objects.create(
            codigo_item="ABC-1",
            item_name="Arroz",
            almacen="NORTE",
            categoria="A",
            valor_orden=Decimal("25.50"),
        )
        PurchaseOrder.objects.create(
            codigo_item="ABC-1",
            item_name="Arroz",
            almacen="",
            categoria="A",
            valor_orden=Decimal("4.50"),
        )
        Transfer.objects.create(
            product_code="ABC-1", origen="NORTE", destino="SUR", cantidad=3
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('dashboard')}"
        )

    def test_dashboard_context_contains_consistent_kpis_and_charts(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_forecasts"], 1)
        self.assertEqual(response.context["total_orders"], 2)
        self.assertEqual(response.context["total_transfers"], 1)
        self.assertEqual(response.context["total_warehouses"], 1)
        self.assertEqual(response.context["total_order_value"], Decimal("30.00"))
        self.assertEqual(response.context["total_forecast_demand"], 30)
        self.assertEqual(response.context["weekly_labels"], [
            "Semana 1", "Semana 2", "Semana 3", "Semana 4"
        ])
        self.assertEqual(response.context["weekly_totals"], [10.0, 20.0, 0.0, 0.0])
        self.assertEqual(response.context["category_labels"], ["A"])
        self.assertEqual(response.context["category_values"], [1])
        self.assertEqual(list(response.context["warehouses"]), [{
            "almacen": "NORTE",
            "total_orders": 1,
            "total_value": Decimal("25.50"),
        }])


class InventoryNavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="inventory-user", password="secret123"
        )
        cls.forecast = Forecast.objects.create(
            product_code="PROD-1",
            product_name="Producto de prueba",
            categoria="A",
            modelo_ganador="Prophet",
            demanda_semanal=[10, 12, 14, 16],
            demanda_total=52,
            status="OK",
        )
        PurchaseOrder.objects.create(
            codigo_item="PROD-1",
            item_name="Producto de prueba",
            almacen="NORTE",
            categoria="A",
            cantidad_a_ordenar=20,
            valor_orden=Decimal("80.00"),
        )
        Transfer.objects.create(
            product_code="PROD-1",
            product_name="Producto de prueba",
            origen="NORTE",
            destino="SUR",
            cantidad=7,
        )
        Transfer.objects.create(
            product_code="PROD-2",
            product_name="Otro producto",
            origen="SUR",
            destino="NORTE",
            cantidad=3,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_transfer_list_filters_and_keeps_color_semantics(self):
        response = self.client.get(
            reverse("transfers"), {"search": "PROD-1", "origen": "NORTE"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertEqual(response.context["total_quantity"], 7)
        self.assertContains(response, "text-bg-secondary")
        self.assertContains(response, "text-bg-primary")
        self.assertContains(response, "Producto de prueba")
        self.assertNotContains(response, "Sin nombre registrado")

    def test_warehouse_list_combines_orders_and_transfer_movements(self):
        response = self.client.get(reverse("warehouses"))
        rows = {row["name"]: row for row in response.context["warehouses"]}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_warehouses"], 2)
        self.assertEqual(rows["NORTE"]["order_count"], 1)
        self.assertEqual(rows["NORTE"]["order_value"], Decimal("80.00"))
        self.assertEqual(rows["NORTE"]["outgoing_count"], 1)
        self.assertEqual(rows["NORTE"]["incoming_count"], 1)
        self.assertEqual(rows["NORTE"]["net_quantity"], -4)

    def test_product_detail_combines_forecast_orders_and_transfers(self):
        response = self.client.get(reverse("product_detail", args=["PROD-1"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["product_name"], "Producto de prueba")
        self.assertEqual(response.context["order_count"], 1)
        self.assertEqual(response.context["order_units"], 20)
        self.assertEqual(response.context["order_value"], Decimal("80.00"))
        self.assertEqual(response.context["transfer_count"], 1)
        self.assertEqual(response.context["transfer_quantity"], 7)
        self.assertEqual(len(response.context["weekly_forecast"]), 4)

    def test_product_detail_returns_not_found_for_unknown_code(self):
        response = self.client.get(reverse("product_detail", args=["UNKNOWN"]))
        self.assertEqual(response.status_code, 404)
