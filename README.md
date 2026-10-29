# Método Productivo — portal Fase A en desarrollo

Aplicación Django con Check PyME, calculadora, lead magnet, contenidos, contacto y catálogo de tienda en desarrollo local. La Entrega 1 fue aprobada con salvedades el 17 de octubre de 2026; A-01 sigue en curso. Hay contenidos y textos legales provisionales, y las funciones comerciales productivas permanecen pendientes.
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
Desde la Home se puede recorrer la estructura pública y entrar al Check existente. Usar únicamente datos ficticios; los avisos legales definitivos permanecen pendientes de revisión.
Sin `DB_ENGINE=postgresql`, el método Windows usa SQLite local. La opción Docker con PostgreSQL se describe abajo.
No crear usuarios públicos; solo personal interno en el backoffice.

## Desarrollo local con Docker

Requiere Docker Desktop con motor Linux y Docker Compose. Esta opción usa Python 3.12, PostgreSQL 16 y el puerto `127.0.0.1:8767`; no utiliza ni migra `dev.sqlite3`. Si otro servidor ocupa 8767, detén ese servidor antes de iniciar Compose. Ejecuta los comandos desde la carpeta que contiene `manage.py`.

En PowerShell, crea tu configuración local y sustituye `DJANGO_SECRET_KEY` y `PGPASSWORD` por valores aleatorios propios. Conserva `.env.docker` fuera de Git y no reutilices credenciales de otros entornos:

```powershell
Copy-Item .env.docker.example .env.docker
notepad .env.docker
```

El ejemplo usa `DJANGO_DEBUG=1`, `DB_ENGINE=postgresql`, `PGHOST=db`, correo de desarrollo en memoria y `STORE_TEST_CHECKOUT_ENABLED=0`. Para observar correos transaccionales de una prueba local, cambia `DJANGO_EMAIL_BACKEND` a `django.core.mail.backends.console.EmailBackend` y consulta los logs de `web`; esos logs contendrán enlaces privados y no deben compartirse. No habilites Checkout TEST salvo para una prueba local explícita.

Construye, arranca PostgreSQL, aplica las migraciones en esa base nueva y después inicia Django:

```powershell
docker compose --env-file .env.docker build web
docker compose --env-file .env.docker up -d db
docker compose --env-file .env.docker run --rm web python manage.py migrate
docker compose --env-file .env.docker up -d web
docker compose --env-file .env.docker ps
docker compose --env-file .env.docker logs --tail 50 web
```

Abre [Home](http://127.0.0.1:8767/), [Check PyME](http://127.0.0.1:8767/check-pyme/), [Privacidad](http://127.0.0.1:8767/privacidad/), [Contenidos](http://127.0.0.1:8767/blog/), [Tienda](http://127.0.0.1:8767/tienda/) y [Backoffice](http://127.0.0.1:8767/backoffice/). El código y las plantillas se montan desde la carpeta del proyecto y el servidor de desarrollo refleja sus cambios. `local_media/` del contenedor se guarda en el volumen Docker `editorial_media`, independiente de `local_media/` de Windows. PostgreSQL utiliza `postgres_data`; los registros de SQLite no aparecen en esta base nueva.

Para crear un administrador local de prueba, ejecuta `docker compose --env-file .env.docker exec web python manage.py createsuperuser`. El ingreso a `/backoffice/` sigue requiriendo enrolamiento TOTP con los mecanismos seguros del proyecto; crear el superusuario no desactiva OTP.

El Excel privado **no se copia a la imagen ni se monta por defecto**. Para revisar A-03, configura una sola vez `PRIVATE_RESOURCE_HOST_PATH` en `.env.docker` con la carpeta local que contiene `Mapa_de_Caja_PyME_v0.3.xlsx`; el ejemplo usa `./private_resources`. En cada sesión de revisión inicia con ambos archivos Compose. El montaje es de solo lectura y no requiere volver a editar las variables:

```powershell
docker compose --env-file .env.docker -f compose.yaml -f compose.private.yaml up -d
```

Si es la primera ejecución, construye la imagen y aplica migraciones con los comandos anteriores antes de revisar el recurso. Trata los enlaces enviados por correo local como privados. Si vuelves al modo normal sin montaje, ejecuta `docker compose --env-file .env.docker up -d --force-recreate web`. Este modo sin recurso sigue disponible para pruebas independientes de A-03.

Comprobaciones y operación:

```powershell
docker compose --env-file .env.docker exec web python manage.py check
docker compose --env-file .env.docker exec web python manage.py makemigrations --check --dry-run
docker compose --env-file .env.docker exec web python manage.py test leads.test_lead_magnet.ConcurrentAccessTests
docker compose --env-file .env.docker exec web python manage.py test
docker compose --env-file .env.docker logs --tail 100 -f web
docker compose --env-file .env.docker stop
docker compose --env-file .env.docker up -d
```

`stop` detiene los contenedores y conserva ambos volúmenes. `up -d` los reinicia con sus datos. No uses `down --volumes` si deseas conservar la base PostgreSQL y los medios. Para regresar al método Windows anterior, detén Compose con `docker compose --env-file .env.docker stop` y ejecuta `python manage.py runserver 127.0.0.1:8767` en tu entorno virtual habitual; Django volverá a SQLite cuando `DB_ENGINE` no esté definido en esa terminal.

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

## Edición de contenidos en desarrollo

En `/backoffice/`, el personal autorizado con OTP puede crear imágenes editoriales y artículos. Primero agrega una imagen JPG, PNG o WebP en **Contenidos → Imágenes editoriales**, con nombre y texto alternativo; después crea un artículo en **Contenidos → Artículos**. El editor visual permite encabezados, énfasis, listas, enlaces, tablas e imágenes de la biblioteca. Guarda como borrador y usa **Vista previa del artículo guardado** antes de publicarlo. La vista previa requiere sesión administrativa verificada. La página pública solo muestra artículos publicados y vigentes; retirar un artículo oculta su URL pública. Una imagen usada por un artículo no puede eliminarse desde la biblioteca. Los videos de YouTube se administran en **Contenidos → Videos** y se reproducen cuando el visitante lo solicita.

Los archivos editoriales se guardan en `local_media/` durante el desarrollo y están excluidos de Git. La ruta de entrega comprueba si la imagen pertenece a una publicación vigente o a una sesión administrativa autorizada. La persistencia definitiva para despliegues sigue pendiente en O-03; el disco local de Cloud Run no debe utilizarse como almacén permanente.

Documentación de alcance y límites: docs/ESTADO.md. Plan y checklist de avance: docs/PLAN_TRABAJO.md. Inventario de archivos exteriores: docs/INVENTARIO_ARCHIVOS_EXTERNOS.md. Preguntas, catálogo y selección se conservan del BRD v0.6; A-05/A-06 tienen cierre funcional y visual local, con contenido real y almacenamiento persistente aún pendientes para publicación.
