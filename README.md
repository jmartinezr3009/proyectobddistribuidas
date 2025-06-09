# proyecto bd distribuidas


# 🚀 Cómo correr el proyecto con Python y Django

## 1. Instalar Python
- Ir a: [https://www.python.org/downloads/](https://www.python.org/downloads/)
- Descargar e instalar Python.


## 2. Instalar Django

```bash
python -m pip install django
```

---

## 3. Instalar las demás dependencias

```bash
python -m pip install opencv-python
python -m pip install pyzbar
python -m pip install reportlab
```

---

## 4. Ir a la carpeta del proyecto

```bash
cd ruta/del/proyecto  # Reemplaza con tu ruta real
```

---

### 5. Configurar base de datos

En el archivo settings.py cambiar nombre, puerto y contraseña si es necesario.

---


## 6. Aplicar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 7. Correr el servidor

```bash
python manage.py runserver
```

- Luego abre tu navegador y visita:
  ```
  http://127.0.0.1:8000
  ```




