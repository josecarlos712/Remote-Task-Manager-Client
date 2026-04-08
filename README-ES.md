Remote Task Manager (RTM)
Remote Task Manager es un ecosistema modular diseñado para centralizar el control de múltiples dispositivos en una red local. El proyecto elimina la barrera técnica que supone gestionar diversos sistemas operativos y dispositivos de forma individual, transformando operaciones complejas en acciones directas desde una interfaz web.

## ✨ Características Principales
- Abstracción de Comandos: Ejecuta operaciones de terminal mediante botones intuitivos en la interfaz.

- Arquitectura Modular: Basado en un sistema de blueprints, permite añadir nuevas funcionalidades sin modificar el núcleo del código.

- Interfaz Responsive: Control total desde navegadores de escritorio o dispositivos móviles.

- Seguridad y Control: Gestión de acceso mediante API Keys y asignación de dispositivos a propietarios específicos.

- Multidispositivo: Capacidad para gestionar PCs, servidores y otros dispositivos con Python instalado.

## 🖼️ Capturas de Pantalla
<p align="center">
<img src="screenshots/login.png" width="32%" alt="Login">
<img src="screenshots/dashboard.png" width="32%" alt="Dashboard">
<img src="screenshots/acciones.png" width="32%" alt="Acciones Remotas">
</p>

## 🛠️ Posibilidades del Sistema
El sistema es extensible por diseño, permitiendo implementar:

- Control de Energía: Apagado, reinicio y suspensión.

- Monitorización: Capturas de pantalla en tiempo real y estado del sistema.

- Gestión de Archivos: Transferencia de archivos entre cliente y servidor.

- Mensajería: Sistema de actividades y notificaciones entre usuarios.

## 🏗️ Estructura del Proyecto
El proyecto se divide en dos componentes independientes:

- Servidor (Django): El panel de control central que gestiona la base de datos, los usuarios y la lógica de negocio. (Este repositorio)

- Cliente (Python/Flask): Aplicación ligera que reside en los dispositivos remotos y ejecuta las órdenes recibidas. (https://github.com/josecarlos712/Remote-Task-Manager-Client)

Entiendo perfectamente. El formato anterior era muy plano y costaba distinguir los pasos. Para un README de calidad, es mejor usar **subtítulos claros**, **listas con iconos** y **bloques de código bien etiquetados**.

Aquí tienes tres opciones de reformateo para que elijas la que mejor encaje con tu estilo:

### Opción 1: Estilo Limpio y Jerárquico (Recomendada)
Esta opción separa claramente los prerrequisitos de los pasos de ejecución, usando negritas para resaltar la acción principal.

---

## ⚙️ Instalación y Configuración

> **Nota:** Se requiere Python 3.10+ y visibilidad de red local.

#### 🖥️ **Servidor**
```bash
# Instalación y arranque del orquestador
cd Remote-Task-Server && pip install -r requirements.txt
python manage.py migrate && python manage.py runserver
```

#### 🔌 **Cliente**
```bash
# Instalación y conexión del nodo
cd Remote-Task-Client && pip install -r requirements.txt
python main.py
```

---

📄 Créditos
Proyecto desarrollado por José Carlos Crespo Falcón como Trabajo Fin de Grado en Ingeniería Informática (Ingeniería de Computadores), Universidad de Sevilla, curso 2024/25.
