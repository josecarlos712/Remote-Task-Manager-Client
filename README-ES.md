# Remote Task Manager Client

**Version:** v26.1019.04

Agente Flask que se instala en cada PC y ejecuta comandos enviados desde el servidor Django.

## Requisitos

```bat
pip install -r requirements.txt
```

## Configuración

Edita `configuration.ini`:

- `SERVER_URL` — URL del servidor Django (ej. `http://192.168.0.3:8000`)
- `REGISTER_TOKEN` — mismo valor que `CLIENT_REGISTER_TOKEN` del servidor
- `OWNER_USERNAME` — usuario Django propietario del cliente
- `PORT` — puerto local del agente (default `5000`)
- `API_KEY` — opcional; si está vacío, el servidor genera una al registrar

## Arranque

```bat
scripts\start_client.bat
```

O: `python main.py`

Al iniciar, el cliente:

1. Se registra en `POST /api/clients/register`
2. Expone `GET /api/health`, `GET /api/command/list`, `POST /api/command/execute`
3. Envía heartbeat periódico a `POST /api/clients/health`

## Autenticación

Las rutas de comandos exigen el header `X-Client-API-Key`. El servidor lo envía al ejecutar desde la web.

## Comandos modulares

Carpeta `command_modules/`. Cada archivo define:

- `COMMAND_ID`, `TITLE`, `DESCRIPTION`, `ARGS`
- `handler(**kwargs) -> (result, http_code)`

Comandos incluidos: `test_command`, `show_popup`, `shutdown`, `screenshot`, `list_processes`, `lock_workstation`, `open_url`, `execute_program`.

Endpoints extra (sin tocar el núcleo): carpeta `endpoints/` + `blueprint_endpoint.py`.

## Autostart en Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_autostart_task.ps1
```

## Logs

`logs/system.log`

## Tests

```bat
pytest test.py -q
```

## Flujo de verificación

1. Arranca el servidor Django
2. Arranca este cliente
3. Revisa logs de registro OK
4. En la web: login → comandos → ejecuta `show_popup` o `test_command`
