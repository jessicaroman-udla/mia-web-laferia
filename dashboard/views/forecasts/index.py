from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from dashboard.models import Forecast


@login_required
def forecast_list(request):

    forecasts = Forecast.objects.filter(
        status="OK"
    )

    search = request.GET.get("search", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    modelo = request.GET.get("modelo", "").strip()

    if search:
        forecasts = forecasts.filter(
            Q(product_code__icontains=search) |
            Q(product_name__icontains=search)
        )

    if categoria:
        forecasts = forecasts.filter(
            categoria=categoria
        )

    if modelo:
        forecasts = forecasts.filter(
            modelo_ganador=modelo
        )

    forecasts = forecasts.order_by(
        "product_name"
    )

    paginator = Paginator(
        forecasts,
        25
    )

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(
        page_number
    )

    categories = (
        Forecast.objects
        .filter(status="OK")
        .values_list(
            "categoria",
            flat=True
        )
        .distinct()
        .order_by("categoria")
    )

    models = (
        Forecast.objects
        .filter(status="OK")
        .exclude(modelo_ganador="")
        .values_list(
            "modelo_ganador",
            flat=True
        )
        .distinct()
        .order_by("modelo_ganador")
    )

    context = {
        "page_obj": page_obj,
        "search": search,
        "categoria": categoria,
        "modelo": modelo,
        "categories": categories,
        "models": models,
    }

    return render(
        request,
        "forecasts/forecasts.html",
        context
    )