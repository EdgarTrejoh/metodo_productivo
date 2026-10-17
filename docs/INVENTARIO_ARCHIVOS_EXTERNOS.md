# Inventario de archivos incorporados a la documentación

**Fecha de corte y traslado:** 17 de octubre de 2026  
**Origen:** carpeta exterior `002_portal_metodo_productivo/`, fuera de `metodo_productivo/`.  
**Destino:** subcarpetas clasificadas de `metodo_productivo/docs/`.  
**Resultado del traslado:** 13 de 13 archivos trasladados; 6,240,240 bytes (5.95 MiB) conservados en ese momento.

El [manifiesto de integridad](INVENTARIO_INTEGRIDAD.csv) se generó **antes** del traslado y registra nombre original, destino, tamaño exacto y SHA-256. Después de cada movimiento se verificó que el archivo de destino conservara ambos valores. **Coincidencia al finalizar el traslado: 13/13; diferencias: 0.** Los originales ya no están en la carpeta exterior. Posteriormente se corrigió el enlace de imagen de la propuesta visual Markdown. **Comparación actual con la línea base: 12/13 coinciden; la única diferencia es esa edición documentada.**

| Archivo original en la carpeta exterior | Ubicación actual en `docs/` | Función | Tamaño al traslado |
| --- | --- | --- | ---: |
| `concepto_alcance_v08.docx` | [producto/concepto_alcance_v08.docx](producto/concepto_alcance_v08.docx) | Documento rector de concepto, fases y Check v1.3. | 54,466 bytes |
| `BRD_Plataforma_Digital_v0_6.docx` | [producto/BRD_Plataforma_Digital_v0_6.docx](producto/BRD_Plataforma_Digital_v0_6.docx) | Reglas de negocio, requerimientos y criterios de aceptación. | 56,462 bytes |
| `arquitectura_v05.docx` | [arquitectura/arquitectura_v05.docx](arquitectura/arquitectura_v05.docx) | Arquitectura, stack, seguridad y despliegue. | 324,239 bytes |
| `Sitemap_Journeys_FaseA_v0_2.docx` | [experiencia/Sitemap_Journeys_FaseA_v0_2.docx](experiencia/Sitemap_Journeys_FaseA_v0_2.docx) | Sitemap y recorridos de Fase A. | 48,894 bytes |
| `Catalogo_Acciones_Check_PyME_v0_1.docx` | [producto/check-pyme/Catalogo_Acciones_Check_PyME_v0_1.docx](producto/check-pyme/Catalogo_Acciones_Check_PyME_v0_1.docx) | Versión editorial del catálogo aprobado. | 47,234 bytes |
| `Catalogo_Acciones_Check_PyME_v0_1.json` | [producto/check-pyme/Catalogo_Acciones_Check_PyME_v0_1.json](producto/check-pyme/Catalogo_Acciones_Check_PyME_v0_1.json) | Fuente normativa estructurada de 72 acciones. | 29,790 bytes |
| `Propuesta_Marca_Metodo_Productivo_v0_2.docx` | [identidad/Propuesta_Marca_Metodo_Productivo_v0_2.docx](identidad/Propuesta_Marca_Metodo_Productivo_v0_2.docx) | Identidad y arquitectura de marca. | 983,110 bytes |
| `propuesta_visual_portal_metodo_productivo_v0_2.md` | [experiencia/propuesta_visual_portal_metodo_productivo_v0_2.md](experiencia/propuesta_visual_portal_metodo_productivo_v0_2.md) | Propuesta visual y sistema de diseño. | 15,643 bytes |
| `build_interactive_prototype.py` | [prototipos/build_interactive_prototype.py](prototipos/build_interactive_prototype.py) | Generador del prototipo HTML. | 86,260 bytes |
| `propuesta_visual_interactiva.html` | [prototipos/propuesta_visual_interactiva.html](prototipos/propuesta_visual_interactiva.html) | Prototipo interactivo independiente de Django. | 88,365 bytes |
| `Logo corporativo Método Productivo.png` | [identidad/assets/Logo corporativo Método Productivo.png](<identidad/assets/Logo corporativo Método Productivo.png>) | Logo horizontal, 1983 × 793 px. | 1,188,838 bytes |
| `Logotipo Método Productivo.png` | [identidad/assets/Logotipo Método Productivo.png](<identidad/assets/Logotipo Método Productivo.png>) | Activo de identidad, 1672 × 941 px. | 1,174,142 bytes |
| `gemini_generated_video_ae097137.mp4` | [medios/gemini_generated_video_ae097137.mp4](medios/gemini_generated_video_ae097137.mp4) | Referencia audiovisual; uso en producto por definir. | 2,142,797 bytes |

## Relaciones y observaciones posteriores al traslado

1. **Catálogo normativo.** El JSON trasladado sigue siendo idéntico byte a byte a [la copia que consume Django](../diagnostics/catalog_v0_1.json). SHA-256 de ambos: `17897a49df2f4752eb53d1085445be1f5e044da0ed12f0b009de83b64754f61f`.
2. **Prototipo independiente.** El generador escribe `propuesta_visual_interactiva.html` en el directorio desde el que se ejecuta, no automáticamente junto al script. El HTML no es parte de las rutas Django y requiere homologación con la propuesta visual v0.2 antes de usarse como evidencia de cumplimiento.
3. **Enlace de imagen corregido.** La propuesta visual Markdown ahora referencia `../identidad/assets/Logotipo Método Productivo.png`, una ruta relativa al documento que resuelve al PNG incluido en `docs/`. Esta edición del 17 de octubre de 2026 cambió su tamaño de 15,643 a 15,588 bytes y su SHA-256 de `a77581b467a396f05ea5d5b7d8dbb0c9d2484066784d58bb6a01a29075ed9c8f` a `ee4d73b86466b5d6660ae6dc0bc1fee813c569abd865065c53f0fbb93ab7da24`. El manifiesto conserva el valor original como línea base del traslado.
4. **Activos de marca.** Los PNG y el MP4 están ahora clasificados dentro de `docs/`; Django todavía no los sirve desde `static/`. Definir uso y versión antes de incorporarlos a la interfaz.
5. **Repositorio pendiente.** No hay `.git` inicializado. Si la carpeta exterior se convierte en raíz del repositorio, aún habrá que mover `.github/workflows/` y `.gitignore` a esa raíz y ajustar las rutas del workflow.

Este inventario documenta ubicación e integridad. No constituye aprobación editorial, legal, de marca ni de derechos de uso.
