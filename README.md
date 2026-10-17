# Método Productivo — portal Fase A en desarrollo

Aplicación Django con el Check PyME B0 y la primera estructura navegable del portal. La Entrega 1 fue aprobada con salvedades el 17 de octubre de 2026; A-01 sigue en curso. Las páginas de herramientas, recursos, contenidos, contacto y textos legales muestran contenido provisional; sus funciones aún no están disponibles.
No está publicada. La aplicación bloquea DJANGO_DEBUG=0 hasta resolver docs/ESTADO.md.

## Estructura del proyecto

Esta carpeta (`metodo_productivo/`) es la raíz recomendada para inicializar el repositorio Git y ejecutar `manage.py`. La carpeta exterior `002_portal_metodo_productivo/` solo contiene este proyecto.

| Ruta | Contenido |
| --- | --- |
| `config/` | Configuración Django, URL y entrada WSGI. |
| `core/` | Middleware y funciones transversales. |
| `diagnostics/` | Cuestionario, catálogo, cálculo del Check, vistas, pruebas y migraciones. |
| `leads/` | Modelos de prospectos y migraciones. |
| `analytics/` | Modelos de eventos y migraciones. |
| `templates/` y `static/` | Plantillas HTML y CSS de la aplicación. |
| `docs/` | Alcance, arquitectura, experiencia, identidad, producto, prototipos, medios, estado, verificación, plan e inventarios. Los archivos fuente de esta documentación se conservan aquí. |
| `qa_artifacts/` | Capturas e informes de las pruebas manuales realizadas. Revisar su contenido antes de compartirlos. |
| `.github/workflows/` | Comprobaciones automáticas previstas para GitHub Actions. |
| `manage.py`, `requirements*.txt`, `.env.example` | Comando de administración, dependencias y ejemplo de configuración. |

`.venv/` y `dev.sqlite3` son archivos locales de ejecución; no forman parte del código fuente. Las exclusiones se definen en [`.gitignore`](.gitignore). Los documentos, catálogos, migraciones, plantillas, archivos estáticos y `.env.example` sí deben conservarse en el repositorio.

## Inicio (Python 3.12)
```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
Abrir http://127.0.0.1:8000. No se envían correos ni se usan claves externas.
Si el puerto 8000 está ocupado, ejecutar `python manage.py runserver 127.0.0.1:8765` y abrir http://127.0.0.1:8765.
Desde la Home se puede recorrer la estructura pública y entrar al Check existente. Usar únicamente datos ficticios. Las páginas provisionales no contienen formularios funcionales; los avisos legales definitivos permanecen pendientes de revisión.
SQLite es solo para la prueba local. Ver .env.example para PostgreSQL.
No crear usuarios públicos; solo personal interno en el backoffice.

## Verificación
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```
Pruebas de dominio recorren las 6,561 combinaciones de puntuaciones válidas.
No son una validación clínica/financiera del instrumento ni prueban PostgreSQL.

## Admin con OTP
```bash
python manage.py createsuperuser
```
El plugin TOTP está instalado. Para enrolar el primer dispositivo, usar shell local protegido y TOTPDevice; no guardar semillas en archivos ni logs. El runbook operativo se completará antes de habilitar administración real. No hay contraseña ni bypass predeterminados.

Documentación de alcance y límites: docs/ESTADO.md. Plan y checklist de avance: docs/PLAN_TRABAJO.md. Inventario de archivos exteriores: docs/INVENTARIO_ARCHIVOS_EXTERNOS.md. Preguntas, catálogo y selección se conservan del BRD v0.6; los diseños editoriales siguen en revisión.
