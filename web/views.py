from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.db import models
from .models import Usuario
from .models import Producto,Venta, DetalleVenta
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import subprocess
from django.db.models import Sum
from django.db.models import Count, F, FloatField, ExpressionWrapper
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta, time
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from django.contrib.auth.hashers import make_password
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle
from django.db import connection



###################################################################################

# CODIGO

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        try:
            usuario = Usuario.objects.get(username=username)

            if usuario.autenticar(password):  # Verifica la contraseña encriptada
                request.session["usuario_id"] = usuario.id  # Guardar el ID en la sesión

                # Redirigir según el rol
                if usuario.rol == "Administrador" and usuario.is_active == 1:  # Verifica si es administrador y está activo
                    return redirect("admin_dashboard")  # Redirige al panel de admin
                elif usuario.rol == "Cajero" and usuario.is_active == 1:  # Verifica si es cajero y está activo
                    return redirect("caja")  # Redirige al panel de cajero
            else:
                if usuario.is_active == 0:
                    messages.error(request, "Usuario inactivo. Contacte al administrador.")
                    return render(request, "login.html", {"error": "Usuario inactivo. Contacte al administrador."})
                messages.error(request, "Contraseña incorrecta.")
                return render(request, "login.html", {"error": "Contraseña incorrecta"})

        except Usuario.DoesNotExist:
            return render(request, "login.html", {"error": "Usuario no encontrado"})

    return render(request, "login.html")


def gestionar_usuarios(request):
    usuarios = Usuario.objects.all()  # Obtener todos los usuarios

    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        rol = request.POST["rol"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden.")
        else:
            if Usuario.objects.filter(username=username).exists():
                messages.success(request, "Login exitoso.")
            else:
                nuevo_usuario = Usuario(
                    username=username,
                    email=email,
                    rol=rol,
                    password=make_password(password1)  # Encripta la contraseña
                )
                nuevo_usuario.save()
                messages.success(request, "Usuario registrado correctamente.")
                return redirect("Gestionusuarios")

    return render(request, "Gestionusuarios.html", {"usuarios": usuarios})


def eliminar_usuario(request, user_id):
    try:
        usuario = Usuario.objects.get(id=user_id)

        if usuario.rol == "Administrador":
            messages.error(request, "No puedes eliminar a un administrador.")
        else:
            usuario.delete()
            messages.success(request, "Usuario eliminado correctamente.")
    except Usuario.DoesNotExist:
        messages.error(request, "El usuario no existe o ya ha sido eliminado.")

    return redirect("Gestionusuarios")

def status_usuario(request, user_id):
    try:
        usuario = Usuario.objects.get(id=user_id)
        usuario.is_active = not usuario.is_active  # Cambia el estado activo/inactivo
        usuario.save()
        status = "activo" if usuario.is_active else "inactivo"
        messages.success(request, f"Usuario {status} correctamente.")
    except Usuario.DoesNotExist:
        messages.error(request, "El usuario no existe o ya ha sido eliminado.")

    return redirect("Gestionusuarios")

def gestionar_productos(request):
    if request.method == "POST":
        codigo_barras = request.POST["codigo_barras"]
        nombre = request.POST["nombre"]
        precio = float(request.POST["precio"])
        stock = int(request.POST["stock"])
        editando = request.POST.get("editando", "")

        if editando:  # Si se está editando un producto
            producto = Producto.objects.get(codigo_barras=codigo_barras)
            producto.nombre = nombre
            producto.precio = precio
            producto.stock = stock
            producto.save()
            messages.success(request, "Producto actualizado correctamente.")
        else:  # Si se está agregando un producto nuevo
            with connection.cursor() as cursor:
                cursor.callproc('crear_producto', [codigo_barras, nombre, precio, stock])
                messages.success(request, "Producto agregado correctamente.")
        return redirect("Gestionproductos")

    productos = Producto.objects.all()
    return render(request, "Gestionproductos.html", {"productos": productos})


def eliminar_producto(request, codigo_barras):
    producto = Producto.objects.get(codigo_barras=codigo_barras)
    producto.delete()
    messages.success(request, "Producto eliminado correctamente.")
    return redirect("Gestionproductos")

def status_producto(request, codigo_barras):
    producto = Producto.objects.get(codigo_barras=codigo_barras)
    producto.is_active = not producto.is_active  # Cambia el estado activo/inactivo
    producto.save()
    status = "activo" if producto.is_active else "inactivo"
    messages.success(request, f"Producto {status} correctamente.")
    return redirect("Gestionproductos")


def gestionar_inventario(request):
    if request.method == "POST":
        codigo_barras = request.POST.get("codigo_barras")
        cantidad = int(request.POST.get("cantidad", 0))
        accion = request.POST.get("accion")  # "agregar" o "eliminar"

        if cantidad >= 0:
            try:
                with connection.cursor() as cursor:
                    if accion == "agregar":
                        cursor.callproc('actualizar_stock_producto', [codigo_barras, cantidad])
                        messages.success(request, f"Se agregaron {cantidad} unidades al stock de {codigo_barras}.")
                    elif accion == "eliminar":
                        cursor.callproc('actualizar_stock_producto', [codigo_barras, -cantidad])
                        messages.success(request, f"Se eliminaron {cantidad} unidades del stock de {codigo_barras}.")
            except Exception as e:
                messages.error(request, f"Error al actualizar stock: {str(e)}")

            return redirect("Gestioninventario")

    productos = Producto.objects.all()
    return render(request, "Gestioninventario.html", {"productos": productos})


def analizar_ventas(request):
    # Calcular el total de ventas
    total_ventas = Venta.objects.aggregate(total=models.Sum('total'))['total'] or 0

    # Ventas por dias
    ventas_por_dia = (
        Venta.objects
        .extra(select={'fecha': "DATE(fecha)"})  # Extrae solo la fecha con SQL puro
        .values('fecha')
        .annotate(total=Sum('total'))  # Suma el total de ventas por cada fecha
        .order_by('-fecha')
    )

    # Obtener los productos más vendidos correctamente
    productos_mas_vendidos = Producto.objects.annotate(
        cantidad_vendida=models.Sum('detalleventa__cantidad')
    ).order_by('-cantidad_vendida')[:10]  # Los 10 más vendidos

    # Calcular el valor total de ventas de cada producto
    productos_con_total_ventas = Producto.objects.annotate(
        total_ventas_producto=Sum(
            ExpressionWrapper(
                F('detalleventa__cantidad') * F('detalleventa__precio_unitario'),
                output_field=FloatField()
            )
        )
    ).order_by('-total_ventas_producto')[:10]


    cajeros_mas_ventas = (
        Venta.objects.values('cajero__username')
        .annotate(ventas=Count('id'), total_vendido=Sum('total'))
        .order_by('-total_vendido')
    )
    


    return render(request, 'AnalisisVentas.html', {
        'total_ventas': total_ventas,
        'ventas_por_dia': ventas_por_dia,
        'productos_mas_vendidos': productos_mas_vendidos,
        'productos_con_total_ventas': productos_con_total_ventas,
        'cajeros_mas_ventas': [{'nombre': c['cajero__username'], 'ventas': c['ventas'], 'total_vendido': c['total_vendido']} for c in cajeros_mas_ventas],

    })


# Canasta de compra (temporal)
import subprocess

canasta = []


def escanear_codigo(request):
    return render(request, 'escaner.html')




def punto_de_venta(request):
    global canasta

    if request.method == "POST":
        codigo_barras = request.POST.get("codigo_barras", "").strip()
        nombre_producto = request.POST.get("nombre_producto", "").strip()
        cantidad = int(request.POST.get("cantidad", 1))

        producto = None

        # Buscar producto por código de barras o nombre
        if codigo_barras:
            producto = Producto.objects.filter(codigo_barras=codigo_barras).first()
        elif nombre_producto:
            producto = Producto.objects.filter(nombre__icontains=nombre_producto).first()

        if producto:
            if producto.stock >= cantidad:
                subtotal = producto.precio * cantidad

                # Verificar si ya existe en la canasta para solo aumentar la cantidad
                for item in canasta:
                    if item["producto"].codigo_barras == producto.codigo_barras:
                        item["cantidad"] += cantidad
                        item["subtotal"] += subtotal
                        break
                else:
                    # Si no existe en la canasta, se agrega como nuevo
                    canasta.append({
                        "producto": producto,
                        "cantidad": cantidad,
                        "subtotal": subtotal
                    })
            else:
                messages.error(request, "Stock insuficiente.")
        else:
            messages.error(request, "Producto no encontrado.")

        return redirect("caja")

    total = sum(item["subtotal"] for item in canasta)
    return render(request, "caja.html", {"canasta": canasta, "total": total, "abrir_lector_codigos": abrir_lector_codigos})


def eliminar_de_canasta(request, codigo_barras):
    global canasta
    canasta = [item for item in canasta if item["producto"].codigo_barras != codigo_barras]
    return redirect("caja")

def abrir_lector_codigos(request):
    try:
        # Ejecuta el script del lector en un proceso separado
        subprocess.Popen(["python", "lector_codigos.py"])
        return JsonResponse({"mensaje": "Lector de códigos iniciado correctamente."})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def finalizar_venta(request):
    global canasta

    if not canasta:
        messages.error(request, "No hay productos en la venta.")
        return redirect("caja")

    total_venta = sum(item["subtotal"] for item in canasta)
    pago_cliente = float(request.POST.get("pago_cliente", 0))

    if pago_cliente < total_venta:
        messages.error(request, "El pago es insuficiente.")
        return redirect("caja")

    cambio = pago_cliente - total_venta

    # Obtiene el id del cajero al realizar la venta
    cajero_id = request.session.get("usuario_id")
    if not cajero_id:
        messages.error(request, "Debe iniciar sesión para realizar una venta.")
        return redirect("login")
    
    cajero = Usuario.objects.get(id=cajero_id)

    # Crear la venta con el total correcto y con la Id del Cajero
    venta = Venta.objects.create(total=total_venta, cajero=cajero)

    # Guardar todos los productos de la canasta en `DetalleVenta`
    for item in canasta:
        producto = item["producto"]
        cantidad = item["cantidad"]

        if producto.stock >= cantidad:
            # Guardar el detalle de la venta
            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio
            )

            # Reducir stock y guardar el producto
            producto.stock -= cantidad
            producto.save()
        else:
            messages.error(request, f"Stock insuficiente para {producto.nombre}.")
            return redirect("caja")

    # Limpiar la canasta después de la venta
    canasta = []

    return render(request, "caja.html", {"canasta": [], "total": 0, "cambio": cambio})


def consultar_inventario(request):
    query = request.GET.get("query", "")
    productos = Producto.objects.all()

    if query:
        productos = productos.filter(nombre__icontains=query) | productos.filter(codigo_barras__icontains=query)

    return render(request, "inventario.html", {"productos": productos})


def admin_dashboard(request):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM productos_bajo_stock")
        resultados = cursor.fetchall()

    producto = []
    for row in resultados:
        producto.append({
            "codigo_barras": row[0],
            "nombre": row[1],
            "stock": row[2],
        })

    return render(request, "admin_dashboard.html", {"productos_bajo_stock": producto})


def generar_reporte_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_ventas.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Encabezado principal
    p.setFont("Helvetica-Bold", 20)
    p.setFillColor(colors.darkblue)
    p.drawString(180, height - 50, "📊 Reporte de Ventas 📊")
    p.setFillColor(colors.black)

    # Obtener fechas del request
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    else:
        fecha_fin = datetime.combine(datetime.now().date(), time.max)
        fecha_inicio = fecha_fin - timedelta(days=6)

    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, height - 80, f"📅 Periodo: {fecha_inicio.strftime('%Y-%m-%d')} a {fecha_fin.strftime('%Y-%m-%d')}")
    
    # Línea separadora
    p.line(50, height - 90, 550, height - 90)

    # Ventas por día
    ventas_por_dia = (
        Venta.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
        .extra(select={'fecha': "DATE(fecha)"})
        .values('fecha')
        .annotate(total=Sum('total'))
        .order_by('fecha')
    )

    total_acumulado = sum(venta['total'] for venta in ventas_por_dia)

    y = height - 120
    if not ventas_por_dia:
        p.drawString(100, y, "❌ No hay ventas en el rango seleccionado.")
        y -= 20
    else:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y, "📌 Ventas por Día:")
        y -= 20

        data = [["Fecha", "Total Vendido"]]
        for venta in ventas_por_dia:
            data.append([venta['fecha'].strftime("%Y-%m-%d"), f"${venta['total']:.2f}"])

        table = Table(data, colWidths=[200, 200])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        table.wrapOn(p, width, height)
        table.drawOn(p, 100, y - len(data) * 20)

        y -= len(data) * 20 + 30
        p.drawString(100, y, f"💰 Total Acumulado: ${total_acumulado:.2f}")
        y -= 40

    # Productos más vendidos con su total de ventas
    productos_mas_vendidos = (
        Producto.objects.filter(detalleventa__venta__fecha__range=[fecha_inicio, fecha_fin])
        .annotate(
            cantidad_vendida=Sum('detalleventa__cantidad'),
            total_ventas=Sum(ExpressionWrapper(F('detalleventa__cantidad') * F('detalleventa__precio_unitario'), output_field=FloatField()))
        )
        .order_by('-cantidad_vendida')[:10]
    )

    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "🏆 Productos Más Vendidos:")
    y -= 20

    data = [["Producto", "Cantidad Vendida", "Total Generado"]]
    for producto in productos_mas_vendidos:
        data.append([producto.nombre, producto.cantidad_vendida, f"${producto.total_ventas:.2f}"])

    table = Table(data, colWidths=[150, 150, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    table.wrapOn(p, width, height)
    table.drawOn(p, 100, y - len(data) * 20)

    y -= len(data) * 20 + 30

    # Cajeros con más ventas
    cajeros_mas_ventas = (
        Venta.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
        .values('cajero__username')
        .annotate(ventas=Count('id'), total_vendido=Sum('total'))
        .order_by('-total_vendido')[:5]
    )

    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "👨‍💼 Cajeros con Más Ventas:")
    y -= 20

    data = [["Cajero", "Total Vendido"]]
    for cajero in cajeros_mas_ventas:
        data.append([cajero['cajero__username'], f"${cajero['total_vendido']:.2f}"])

    table = Table(data, colWidths=[250, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    table.wrapOn(p, width, height)
    table.drawOn(p, 100, y - len(data) * 20)

    p.showPage()
    p.save()
    return response



