"""
URL configuration for mi_proyecto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from web.views import login_view
from web.views import gestionar_usuarios,eliminar_usuario
from web.views import gestionar_productos, eliminar_producto,gestionar_inventario,punto_de_venta, eliminar_de_canasta, finalizar_venta
from web.views import consultar_inventario,admin_dashboard
from web.views import abrir_lector_codigos
from web.views import escanear_codigo
from web.views import analizar_ventas
from web.views import generar_reporte_pdf
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path("Gestionusuarios/", gestionar_usuarios, name="Gestionusuarios"),
    path("usuarios/eliminar/<int:user_id>/", eliminar_usuario, name="eliminar_usuario"),
    path("Gestionproductos/", gestionar_productos, name="Gestionproductos"),
    path("eliminar_producto/<str:codigo_barras>/", eliminar_producto, name="eliminar_producto"),
    path("Gestioninventario/", gestionar_inventario, name="Gestioninventario"),
    path("AnalisisVentas/", analizar_ventas, name="AnalisisVentas"),
    path("caja/", punto_de_venta, name="caja"),
    path("eliminar_de_canasta/<str:codigo_barras>/", eliminar_de_canasta, name="eliminar_de_canasta"),
    path("finalizar_venta/", finalizar_venta, name="finalizar_venta"),
    path("inventario/", consultar_inventario, name="inventario"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path("abrir-lector-codigos/", abrir_lector_codigos, name="abrir_lector_codigos"),
    path('escanear/', escanear_codigo, name='escanear_codigo'),
    path('reporte/', generar_reporte_pdf, name='reporte_pdf'),
    path('reset_password/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html'
    ), name='password_reset'),
    path('reset_password_send/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete')
]
