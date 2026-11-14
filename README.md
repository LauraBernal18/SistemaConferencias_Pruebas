# Pruebas funcionales SGC — Sprint 1

Contenido: HU-006 (inicio de sesión), HU-030 (configuración), HU-031 (registro autónomo).

## Preparación (Windows / VS Code)

1. Descomprime el ZIP en una carpeta. Si ya tienes el repositorio, copia `tests`, `pytest.ini`, `EJECUTAR_PRUEBAS.bat`, `.gitignore` y `requirements.txt` sobre sus equivalentes (haz una copia de seguridad primero).
2. Abre la carpeta en VS Code. Activa tu entorno existente: `venv\Scripts\activate` (PowerShell: `.\venv\Scripts\Activate.ps1`). Si el entorno estaba en otro computador, créalo con `python -m venv venv`.
3. Instala: `python -m pip install -r requirements.txt`.
4. Abre https://conferencia-cientifica-ds1-pruebas.onrender.com/api/health/ y verifica que responda OK; el backend gratuito puede tardar hasta ~1 minuto en despertar.
5. Coordina que nadie modifique al mismo tiempo la **Conferencia de Pruebas QA · 2027**.
6. Ejecuta `EJECUTAR_PRUEBAS.bat` o:
   `python -m pytest tests/funcionales/test_hu006.py tests/funcionales/test_hu030.py tests/funcionales/test_hu031.py -v --html=reportes/sprint1_hu006_hu030_hu031.html --self-contained-html`
7. Encontrarás el reporte HTML en `reportes/` y capturas en `evidencias/Sprint_1/HUxxx/`.

## Limitaciones actuales

- HU006-CP10 y HU030-CP10: navegación directa a rutas interiores devuelve 404 de Vercel incluso para administradores. Se requiere corrección de fallback SPA y validación de autorización.
- HU030-CP09: bloqueado por HU008, donde el selector de líneas temáticas aparece inhabilitado al autor.
- HU031-CP07: requiere petición técnica de API para comprobar que no se puede otorgar un rol privilegiado.
- HU031-CP08: requiere revisión autorizada del hash en almacenamiento/backend.

**Ninguna prueba ha sido ejecutada o verificada en este paquete contra la aplicación en vivo**: los selectores se basan en el HTML y comportamiento compartidos. Un fallo puede indicar un defecto real o una variación de interfaz que necesita revisar el selector.

## Riesgos y limpieza

- HU030-CP02 cambia fechas y después intenta restaurarlas en `finally`. Si hay una caída de red durante la restauración, **revisa manualmente los valores**.
- HU030-CP05 y CP11 crean líneas con nombres únicos y luego las desactivan; NO se eliminan de la base de datos.
- HU031-CP05 y CP09 crean cuentas nuevas con correos únicos. No se eliminan automáticamente.
- El modo de CAPTCHA simulado solo comprueba la interacción UI, no la validación de un CAPTCHA de producción.
- No ejecutes estas pruebas contra producción, ni en paralelo contra la misma conferencia.
- Los casos con `skip` deben consignarse como pendientes/bloqueados según causa, nunca aprobados.
- Capturas de éxito se toman en casos representativos; toda falla durante el cuerpo de una prueba genera captura si el navegador sigue disponible.
