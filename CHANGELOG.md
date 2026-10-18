# Changelog — Remote Task Manager Client

Formato de version: `vYY.MMDD.NN`. Las entradas mas recientes van arriba.

> Nota: el historial antiguo sigue en `Updates.md`. A partir de `v26.1019.02` este archivo es la fuente de verdad.

## v26.1019.03 — 19-10-2026

- `.gitignore`: omite contenido de `downloads/` (excepto `.gitkeep`) y carpeta `build/`.
- Config local ignorada: `config/download_routes.json` y `config/programs.json`.
- Plantillas en git: `config/download_routes.example.json` y `config/programs.example.json`.

## v26.1019.02 — 19-10-2026

- Cancelacion de descargas activas (`cancel_download`, endpoint `/api/download/cancel`).
- Limpieza de jobs en estado `cancelled` y borrado del fichero `.part`.
- Icono de aplicacion (`assets/app.ico`, favicon del servidor) embebido en el `.exe` portable y en la consola al arrancar.
- Build portable (`build_portable.ps1`) regenera ICO multi-tamano y usa `--icon`.
- Regla de versionado automatico + este changelog.

## v26.1019.01 — 19-10-2026

- Modulos de comando y endpoints dinamicos (incl. `download_file`, programas, procesos).
- Descargas con progreso/velocidad, rutas por dominio (`download_routes.json`) y clave Civitai en `sensible/`.
- Empaquetado portable PyInstaller (`build/RTM-Client`).
- Scripts de reinicio/disposicion de consolas en monitor secundario.
- Sync de lista de programas y mejoras de API key / agente.
