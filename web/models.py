from django.db import models

# Create your models here.
from django.contrib.auth.hashers import make_password, check_password

##############################from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
# from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, password=None, rol='Cajero'):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, rol=rol)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password, rol='Administrador')
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class Usuario(AbstractBaseUser, PermissionsMixin):
    ROLES = [
        ("Administrador", "Administrador"),
        ("Cajero", "Cajero"),
    ]

    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=15, choices=ROLES, default="Cajero")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.IntegerField(default=1)  # 1 para activo, 0 para inactivo

    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def set_password(self, raw_password):
        """Encripta la contraseña antes de guardarla."""
        self.password = make_password(raw_password)

    def autenticar(self, raw_password):
        """Verifica si la contraseña ingresada es correcta."""
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.username} - {self.rol}"
    
    
########################################################
class Producto(models.Model):
    codigo_barras = models.CharField(max_length=50, primary_key=True)  # Ahora es la clave primaria
    nombre = models.CharField(max_length=100)
    precio = models.FloatField()
    stock = models.IntegerField()
    is_active = models.IntegerField(default=0)  # 1 para activo, 0 para inactivo
    
    def status_producto(self, is_activo):
        """Actualiza el stock sumando o restando una cantidad."""
        self.is_active = is_activo
        self.save()

    def actualizar_stock(self, cantidad, is_active):
        """Actualiza el stock sumando o restando una cantidad."""
        self.stock += cantidad
        self.save()

    def agregar_producto(self, cantidad, is_active):
        """Aumenta el stock de un producto existente."""
        self.actualizar_stock(cantidad)

    def reducir_producto(self, cantidad):
        """Reduce el stock si hay suficiente inventario."""
        if self.stock >= cantidad:
            self.actualizar_stock(-cantidad)
        else:
            raise ValueError("Stock insuficiente para reducir.")

    def eliminar_producto(self):
        """Elimina el producto de la base de datos."""
        self.delete()

    @staticmethod
    def consultar_productos():
        """Consulta todos los productos disponibles en la base de datos."""
        return Producto.objects.all()

    def __str__(self):
        return f"{self.codigo_barras} - {self.nombre} - ${self.precio} - Stock: {self.stock}  - {self.is_active}"
    
########################
class Venta(models.Model):
    id = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.FloatField(default=0)
    cajero = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="ventas_realizadas")

    def calcular_total(self):
        """Calcula el total de la venta sumando los subtotales de los productos."""
        total = sum(item.subtotal() for item in self.detalleventa_set.all())
        self.total = total
        self.save()
    
    def _str_(self):
        return f"Venta {self.id} - {self.fecha.strftime('%Y-%m-%d %H:%M:%S')} - Cajero: {self.cajero.username if self.cajero else 'Desconocido'} - Total: ${self.total}"
    
###################################################

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.FloatField()

    def subtotal(self):
        return self.cantidad * self.precio_unitario  # Subtotal del producto

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad} - ${self.subtotal()}"

class HistorialAcciones(models.Model):
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.fecha.strftime('%Y-%m-%d %H:%M:%S')} - {self.mensaje}"
