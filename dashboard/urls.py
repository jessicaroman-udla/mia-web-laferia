from django.urls import path
from .views.login.index import login_view, logout_view
from .views.dashboard.index import dashboard_view
from .views.forecasts.index import forecast_list
from .views.orders.index import order_list
from .views.products.detail import product_detail
from .views.transfers.index import transfer_list
from .views.warehouses.index import warehouse_list


urlpatterns = [
    path('', login_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('pronosticos/', forecast_list, name='forecasts'),
    path('ordenes/', order_list, name='orders'),
    path('transferencias/', transfer_list, name='transfers'),
    path('almacenes/', warehouse_list, name='warehouses'),
    path('productos/<str:product_code>/', product_detail, name='product_detail'),
]
