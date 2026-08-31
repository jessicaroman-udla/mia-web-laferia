# MIA Web La Feria

Dashboard web (Django + AdminLTE) para visualizar los resultados del proyecto de
pronóstico de demanda y optimización de inventario de La Feria: pronósticos de
demanda, órdenes de compra (MILP) y transferencias entre sucursales (GA).

## Stack

- Python 3.11
- Django 5.2
- MySQL 8 (driver `mysqlclient`)
- AdminLTE 4 (archivos estáticos ya incluidos en `dashboard/static/`)

## Requisitos previos

- Python 3.11+
- Un servidor MySQL en ejecución (local o remoto) y una base de datos vacía creada
- En macOS, `mysqlclient` necesita las librerías de cliente de MySQL:
  ```bash
  brew install mysql-client pkg-config
  export PKG_CONFIG_PATH="$(brew --prefix mysql-client)/lib/pkgconfig"
  ```
  (En Linux: `sudo apt install default-libmysqlclient-dev build-essential pkg-config`)

## 1. Clonar y crear el entorno virtual

```bash
cd mia-web-laferia
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Variables de entorno

Crea un archivo `.env` en la raíz del proyecto (junto a `manage.py`). No se versiona.

```dotenv
SECRET_KEY=pon-aqui-una-clave-larga-y-aleatoria
DEBUG=True

DB_NAME=mia_web_laferia
DB_USER=root
DB_PASSWORD=tu_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

Notas:
- `DEBUG` solo es `True` si el valor es exactamente `True`.
- Para generar una `SECRET_KEY`:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- `ALLOWED_HOSTS` ya incluye `localhost`, `127.0.0.1` y `*.ngrok-free.dev`.

## 3. Crear la base de datos en MySQL

```sql
CREATE DATABASE mia_web_laferia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 4. Migraciones y superusuario

```bash
python manage.py migrate
python manage.py createsuperuser
```

El login del dashboard usa los usuarios de Django, así que el superusuario sirve
para entrar en `/login/` y en `/admin/`.

## 5. Cargar los datos de los modelos

La app trae un comando que importa los resultados de los modelos desde archivos
CSV/JSON. Coloca estos archivos dentro de una carpeta `data/` en la raíz:

| Archivo                              | Contenido                        |
|--------------------------------------|----------------------------------|
| `data/pronostico_futuro_producto.csv`| Pronósticos de demanda por producto |
| `data/resultados_milp_piloto.csv`    | Órdenes de compra (MILP)         |
| `data/resultado_ga_transferencias.json` | Transferencias entre sucursales (GA) |

Luego:

```bash
python manage.py load_model_outputs
```

El comando limpia las tablas y las vuelve a llenar (operación idempotente).

## 6. Levantar el servidor

```bash
python manage.py runserver
```

- Dashboard: http://127.0.0.1:8000/login/
- Admin de Django: http://127.0.0.1:8000/admin/

## Rutas principales

| URL                       | Vista                          |
|---------------------------|--------------------------------|
| `/login/` `/logout/`      | Autenticación                  |
| `/dashboard/`             | KPIs, gráficas y tablas resumen|
| `/pronosticos/`           | Listado de pronósticos         |
| `/ordenes/`               | Listado de órdenes de compra   |
| `/transferencias/`        | Listado de transferencias      |
| `/almacenes/`             | Resumen por almacén            |
| `/productos/<codigo>/`    | Detalle de un producto         |

## Exponer con ngrok (opcional)

`settings.py` ya confía en dominios `*.ngrok-free.dev` para CSRF:

```bash
ngrok http 8000
```

Si usas un subdominio fijo distinto, añádelo a `CSRF_TRUSTED_ORIGINS` en
`mia_web_laferia/settings.py`.

## Problemas comunes

- **`django.db.utils.OperationalError` al migrar**: revisa que MySQL esté
  levantado y que las credenciales del `.env` sean correctas.
- **Falla la instalación de `mysqlclient`**: instala las librerías de cliente de
  MySQL y `pkg-config` (ver "Requisitos previos").
- **`FileNotFoundError` en `load_model_outputs`**: falta alguno de los archivos en
  `data/` o el nombre no coincide con la tabla de arriba.
