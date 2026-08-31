from django.db import models


# ============================================================
# PRONÓSTICO DE DEMANDA
# Fuente: pronostico_futuro_producto.csv
# Granularidad: nacional por producto
# ============================================================

class Forecast(models.Model):
    product_code = models.CharField(
        max_length=50,
        unique=True
    )

    product_name = models.CharField(
        max_length=255
    )

    categoria = models.CharField(
        max_length=10
    )

    modelo_ganador = models.CharField(
        max_length=50
    )

    # Ejemplo:
    # [5398.3, 5506.6, 5620.1, 5700.4]
    demanda_semanal = models.JSONField(
        default=list
    )

    demanda_total = models.FloatField(
        default=0
    )

    horizon_weeks = models.PositiveIntegerField(
        default=4
    )

    # Lo completaremos luego con
    # model_comparison_results_A/B.csv
    mape = models.FloatField(
        null=True,
        blank=True
    )

    selected_model = models.CharField(
        max_length=50,
        blank=True,
        default=''
    )

    status = models.CharField(
        max_length=20,
        default='OK'
    )

    class Meta:
        verbose_name = 'Pronóstico'
        verbose_name_plural = 'Pronósticos'
        ordering = ['product_code']
        indexes = [
            models.Index(fields=['categoria']),
            models.Index(fields=['modelo_ganador']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.product_code} - {self.product_name}'


# ============================================================
# ÓRDENES DE COMPRA
# Fuente: resultados_milp_piloto.csv
# Granularidad: producto + sucursal
# Solo registros con genera_orden = 1
# ============================================================

class PurchaseOrder(models.Model):
    codigo_item = models.CharField(
        max_length=50
    )

    item_name = models.CharField(
        max_length=255
    )

    almacen = models.CharField(
        max_length=50
    )

    categoria = models.CharField(
        max_length=10
    )

    modelo_ganador = models.CharField(
        max_length=50,
        blank=True,
        default=''
    )

    disponible = models.FloatField(
        default=0
    )

    forecasted_demand = models.FloatField(
        default=0
    )

    punto_reorden = models.FloatField(
        default=0
    )

    cantidad_a_ordenar = models.FloatField(
        default=0
    )

    costo = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=0
    )

    valor_orden = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0
    )

    moq = models.FloatField(
        default=0
    )

    lead_time = models.FloatField(
        default=0
    )

    mape = models.FloatField(
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Orden de compra'
        verbose_name_plural = 'Órdenes de compra'
        ordering = ['codigo_item', 'almacen']

        indexes = [
            models.Index(fields=['codigo_item']),
            models.Index(fields=['almacen']),
            models.Index(fields=['categoria']),
            models.Index(fields=['modelo_ganador']),
        ]

    def __str__(self):
        return f'{self.codigo_item} - {self.almacen}'


# ============================================================
# TRANSFERENCIAS ENTRE SUCURSALES
# Fuente: resultado_ga_transferencias.json
# Granularidad: cada movimiento individual
# ============================================================

class Transfer(models.Model):
    product_code = models.CharField(
        max_length=50
    )

    # Lo completaremos con abc_classification.json
    product_name = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    origen = models.CharField(
        max_length=50
    )

    destino = models.CharField(
        max_length=50
    )

    cantidad = models.FloatField(
        default=0
    )

    class Meta:
        verbose_name = 'Transferencia'
        verbose_name_plural = 'Transferencias'
        ordering = ['product_code', 'origen', 'destino']

        indexes = [
            models.Index(fields=['product_code']),
            models.Index(fields=['origen']),
            models.Index(fields=['destino']),
        ]

    def __str__(self):
        return (
            f'{self.product_code}: '
            f'{self.origen} → {self.destino} '
            f'({self.cantidad})'
        )
