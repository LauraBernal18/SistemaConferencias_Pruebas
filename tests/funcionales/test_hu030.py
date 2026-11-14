def test_hu030_cp04_etapas_superpuestas(navegador):
    login(navegador)
    fecha_qa(navegador)
    originales = leer_fechas(navegador)
    modificar_input_react(navegador, "EVALUACION-inicio", "2026-12-12T16:07")
    guardar_fechas(navegador)
    esperar_texto(navegador, "«Evaluación por el comité científico» debe iniciar después de que termine «Postulación de artículos».")
    fecha_qa(navegador)
    assert leer_fechas(navegador) == originales


# CP05: crear, editar y desactivar una línea de prueba
def test_hu030_cp05_gestion_lineas(navegador):
    login(navegador)
    fecha_qa(navegador)
    nombre = "Computación en la nube QA_" + uuid.uuid4().hex[:8]
    agregar_linea(navegador, nombre, "Arquitecturas y servicios de computación en la nube")
    try:
        editar_descripcion(navegador, nombre, "Arquitecturas, servicios y seguridad en la nube")
        screenshot(navegador, "HU030-CP05_EDICION")
    finally:
        # No hay eliminación confirmada: se desactiva para no dejar líneas habilitadas.
        desactivar_linea(navegador, nombre)
    assert "Desactivada" in articulo_linea(navegador, nombre).text


# CP06: líneas de QA y estado visible
def test_hu030_cp06_consultar_lineas(navegador):
    login(navegador)
    fecha_qa(navegador)
    for nombre in ["Ciencia de datos", "Interacción humano-computador", "Redes y comunicaciones"]:
        assert "Habilitada" in articulo_linea(navegador, nombre).text
    assert "Desactivada" in articulo_linea(navegador, "prueba").text


# CP07: dos conferencias muestran configuraciones diferentes
def test_hu030_cp07_configuraciones_independientes(navegador):
    login(navegador)
    abrir_config(navegador)
    seleccionar(navegador, MAIN)
    main_fechas, main_lineas = leer_fechas(navegador), datos_lineas(navegador)
    seleccionar(navegador, QA)
    qa_fechas, qa_lineas = leer_fechas(navegador), datos_lineas(navegador)
    assert main_fechas != qa_fechas
    assert "Bases de datos" in main_lineas
    assert "Ciencia de datos" in qa_lineas
    assert "Ciencia de datos" not in main_lineas
    assert "Bases de datos" not in qa_lineas


# CP08: modificar QA y comprobar que MAIN no cambia; restaurar QA
def test_hu030_cp08_cambios_solo_qa(navegador):
    login(navegador)
    abrir_config(navegador)
    seleccionar(navegador, MAIN)
    main_antes = (leer_fechas(navegador), datos_lineas(navegador))
    seleccionar(navegador, QA)
    card = articulo_linea(navegador, "Ciencia de datos")
    desc_original = card.find_element(By.TAG_NAME, "p").text
    temporal = desc_original + " [verificación QA]"
    try:
        editar_descripcion(navegador, "Ciencia de datos", temporal)
        seleccionar(navegador, MAIN)
        main_despues = (leer_fechas(navegador), datos_lineas(navegador))
        assert main_despues == main_antes, "¡Modificar QA alteró la conferencia principal!"
    finally:
        seleccionar(navegador, QA)
        editar_descripcion(navegador, "Ciencia de datos", desc_original)


# CP09: integración con HU-008, bloqueada actualmente
@pytest.mark.skip(reason="HU-008: selector de líneas temáticas inhabilitado para autor; desarrollo debe corregir integración frontend/backend antes de ejecutar este caso")
def test_hu030_cp09_plazo_permite_o_restringe_articulos():
    pass


# CP10: un autor no puede modificar la configuración
def test_hu030_cp10_autor_sin_permisos(navegador):
    login(navegador, "autor")
    navegador.get(f"{BASE_URL}/configuracion-conferencia")
    WebDriverWait(navegador, 30).until(lambda d: d.current_url.rstrip("/") != f"{BASE_URL}/configuracion-conferencia" or
                                      "Acceso denegado" in texto(d) or "No autorizado" in texto(d) or
                                      d.find_elements(By.ID, "conferencia-configuracion"))
    # No basta con comprobar el texto; el autor no debe tener controles de escritura activos.
    assert not any(b.is_displayed() and b.is_enabled() for b in navegador.find_elements(
        By.XPATH, "//button[normalize-space()='Guardar fechas límite' or normalize-space()='Agregar línea temática']"
    )), "El autor tiene controles de configuración habilitados"


# CP11: confirmación al crear línea; luego desactivar para no dejarla habilitada
def test_hu030_cp11_confirmacion_guardado(navegador):
    login(navegador)
    fecha_qa(navegador)
    nombre = "Arquitectura de software QA_" + uuid.uuid4().hex[:8]
    agregar_linea(navegador, nombre, "Diseño de sistemas y arquitecturas de software")
    try:
        assert "Habilitada" in articulo_linea(navegador, nombre).text
        screenshot(navegador, "HU030-CP11_EXITO")
    finally:
        desactivar_linea(navegador, nombre)


# CP12: falta inicio de evaluación, error junto al recuadro y no persistencia
def test_hu030_cp12_fecha_incompleta(navegador):
    login(navegador)
    fecha_qa(navegador)
    originales = leer_fechas(navegador)
    modificar_input_react(navegador, "EVALUACION-inicio", "")
    guardar_fechas(navegador)
    error = "Completa las fechas de inicio y fin para «Evaluación por el comité científico»."
    esperar_texto(navegador, error)
    fieldset = navegador.find_element(By.XPATH, "//fieldset[.//input[@id='EVALUACION-inicio']]")
    assert error in fieldset.text, "El error no aparece dentro del recuadro de evaluación"
    fecha_qa(navegador)
    assert leer_fechas(navegador) == originales, "¡Se guardaron fechas incompletas!"
