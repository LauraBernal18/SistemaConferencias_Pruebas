# HU-008 · Crear artículo · casos del diseño HU008-CP01 a CP12 (los mismos del Excel)
# Cuenta: autor@pruebas.co · Conferencia: Congreso de Pruebas · 2027 (postulación abierta)
# Cada prueba crea sus propios artículos con un ID único, así que se pueden repetir.

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from sgc_helpers import body, login, react_value, visible_text
from sgc_articulos import (anotar_id, LINEAS_CONGRESO, LINEAS_CONGRESO_ENUNCIADO, PALABRAS, RESUMEN, abrir_formulario_articulo,
                           cambiar_usuario, clic_en_panel, coautores_de_prueba, elegir_opcion,
                           enviar_articulo, esperar_listado, fila_de_articulo, id_unico, ir_a_ruta,
                           llenar_articulo, mensaje_registro, registrar_articulo, textos_de_opciones)

ID = id_unico()
anotar_id('HU-008', ID)


def titulo(texto):
    return f'QA HU008 {ID} – {texto}'


def test_hu008_cp01_acceso_formulario(navegador, evidencia):
    """Matriz CP-001. El autor abre «Registrar un artículo»."""
    login(navegador, 'autor')
    clic_en_panel(navegador, 'Registrar un artículo')
    WebDriverWait(navegador, 90).until(EC.visibility_of_element_located((By.ID, 'titulo-articulo')))
    assert 'Datos de la propuesta' in body(navegador)
    assert 'Autores del artículo' in body(navegador)
    evidencia('EXITO')


def test_hu008_cp02_ingreso_informacion(navegador, evidencia):
    """Matriz CP-003. Se escriben nombre, resumen y palabras clave."""
    login(navegador, 'autor')
    abrir_formulario_articulo(navegador)
    nombre = titulo('Pruebas automatizadas en aplicaciones web')
    llenar_articulo(navegador, titulo=nombre, resumen=RESUMEN, palabras_clave=PALABRAS)
    assert navegador.find_element(By.ID, 'titulo-articulo').get_attribute('value') == nombre
    assert navegador.find_element(By.ID, 'resumen-articulo').get_attribute('value') == RESUMEN
    assert navegador.find_element(By.ID, 'palabras-clave').get_attribute('value') == PALABRAS
    evidencia('EXITO')


def test_hu008_cp03_linea_tematica(navegador, evidencia):
    """Matriz CP-004. Aparecen las 4 líneas del Congreso y se elige Ingeniería de software."""
    login(navegador, 'autor')
    abrir_formulario_articulo(navegador)
    elegir_opcion(navegador, 'convocatoria', 'Congreso de Pruebas')
    lineas = textos_de_opciones(navegador, 'linea-tematica')
    # Desde el 22/11 el entorno usa las 5 líneas del enunciado en lugar de las 4 anteriores
    esperadas = LINEAS_CONGRESO if 'Ingeniería de software' in lineas else LINEAS_CONGRESO_ENUNCIADO
    for linea in esperadas:
        assert linea in lineas, f'Falta la línea {linea}. Hay: {lineas}'
    elegir_opcion(navegador, 'linea-tematica', 'Ingeniería de software')
    evidencia('EXITO')


def test_hu008_cp04_campos_obligatorios(navegador, evidencia):
    """Matriz CP-005. Nombre y resumen vacíos."""
    login(navegador, 'autor')
    abrir_formulario_articulo(navegador)
    llenar_articulo(navegador, palabras_clave=PALABRAS, linea='Ingeniería de software')
    enviar_articulo(navegador)
    visible_text(navegador, 'Revisa los campos señalados antes de enviar la propuesta.', 15)
    assert 'El título del artículo es obligatorio.' in body(navegador)
    assert 'El resumen del artículo es obligatorio.' in body(navegador)
    evidencia('EXITO')


def test_hu008_cp05_registro_exitoso(navegador, evidencia):
    """Matriz CP-006. Registro completo dentro del plazo de postulación."""
    login(navegador, 'autor')
    nombre = titulo('Pruebas automatizadas en aplicaciones web')
    registrar_articulo(navegador, titulo=nombre, resumen=RESUMEN, palabras_clave=PALABRAS,
                       linea='Ingeniería de software')
    assert mensaje_registro(nombre) in body(navegador)
    evidencia('EXITO')


def test_hu008_cp06_asociacion_autor(navegador, evidencia):
    """Matriz CP-007. El artículo queda a nombre de quien lo registró (lo ve el comité)."""
    login(navegador, 'autor')
    nombre = titulo('Asociación con el autor')
    registrar_articulo(navegador, titulo=nombre, resumen=RESUMEN, palabras_clave=PALABRAS,
                       linea='Ingeniería de software')
    cambiar_usuario(navegador, 'comite')
    clic_en_panel(navegador, 'Consultar artículos')
    esperar_listado(navegador)
    fila = fila_de_articulo(navegador, nombre)
    assert fila is not None, 'El comité no ve el artículo'
    assert 'Autor Pruebas' in fila, fila
    evidencia('EXITO')


def _abrir_plazos_qa(navegador):
    cambiar_usuario(navegador, 'admin')
    clic_en_panel(navegador, 'Configurar fechas y líneas temáticas')
    WebDriverWait(navegador, 100).until(EC.visibility_of_element_located((By.ID, 'POSTULACION-inicio')))
    # La página carga primero la conferencia por defecto: se elige QA y se confirma que quedó elegida
    # (si se elige antes de que termine esa carga, la página vuelve al Congreso).
    for _ in range(4):
        time.sleep(1.5)
        elegir_opcion(navegador, 'conferencia-configuracion', 'Conferencia de Pruebas QA')
        time.sleep(2)
        if 'se aplica únicamente a Conferencia de Pruebas QA' in body(navegador):
            break
    assert 'se aplica únicamente a Conferencia de Pruebas QA' in body(navegador), 'No se pudo elegir la conferencia QA'
    WebDriverWait(navegador, 100).until(EC.visibility_of_element_located((By.ID, 'EVALUACION-inicio')))
    time.sleep(1)


def _guardar_postulacion(navegador, inicio, fin):
    react_value(navegador, navegador.find_element(By.ID, 'POSTULACION-inicio'), inicio)
    react_value(navegador, navegador.find_element(By.ID, 'POSTULACION-fin'), fin)
    navegador.find_element(By.XPATH, '//button[contains(., "Guardar fechas límite")]').click()
    visible_text(navegador, 'Los cinco plazos de la conferencia se guardaron correctamente.', 100)


def test_hu008_cp07_fecha_limite(navegador, evidencia):
    """Matriz CP-008. Se cierra la postulación de QA, el autor ya no la ve y al final se restaura.
    OJO: cambia la Conferencia de Pruebas QA unos segundos; no correr a la vez que HU-030."""
    _abrir_plazos_qa(navegador)
    inicio_original = navegador.find_element(By.ID, 'POSTULACION-inicio').get_attribute('value')
    fin_original = navegador.find_element(By.ID, 'POSTULACION-fin').get_attribute('value')
    _guardar_postulacion(navegador, '2026-10-01T08:00', '2026-10-31T23:59')
    try:
        cambiar_usuario(navegador, 'autor')
        abrir_formulario_articulo(navegador)
        convocatorias = textos_de_opciones(navegador, 'convocatoria')
        evidencia('EXITO')
    finally:
        _abrir_plazos_qa(navegador)
        _guardar_postulacion(navegador, inicio_original, fin_original)
    assert any('Congreso de Pruebas' in c for c in convocatorias), convocatorias
    assert not any('Conferencia de Pruebas QA' in c for c in convocatorias), convocatorias


def test_hu008_cp08_mensaje_resultado(navegador, evidencia):
    """Matriz CP-009. Intento 1 correcto (mensaje de éxito); intento 2 sin título (mensaje de error)."""
    login(navegador, 'autor')
    registrar_articulo(navegador, titulo=titulo('Resultado'), resumen=RESUMEN, palabras_clave=PALABRAS,
                       linea='Ingeniería de software')
    abrir_formulario_articulo(navegador)
    llenar_articulo(navegador, resumen=RESUMEN, palabras_clave=PALABRAS, linea='Ingeniería de software')
    enviar_articulo(navegador)
    visible_text(navegador, 'El título del artículo es obligatorio.', 15)
    evidencia('EXITO')


def test_hu008_cp09_varios_autores(navegador, evidencia):
    """Matriz CP-010. Artículo con 3 autores (autor + Carlos Ramírez + Ana Torres)."""
    login(navegador, 'autor')
    nombre = titulo('Varios autores')
    registrar_articulo(navegador, titulo=nombre, resumen=RESUMEN, palabras_clave=PALABRAS,
                       linea='Inteligencia artificial', coautores=coautores_de_prueba(ID), responsable=1)
    assert mensaje_registro(nombre) in body(navegador)
    evidencia('EXITO')


def test_hu008_cp10_datos_cada_autor(navegador, evidencia):
    """Matriz CP-011. Se guardan los datos de cada coautor y no se acepta un correo repetido."""
    login(navegador, 'autor')
    nombre = titulo('Datos de cada autor')
    coautores = coautores_de_prueba(ID + '-10')
    registrar_articulo(navegador, titulo=nombre, resumen=RESUMEN, palabras_clave=PALABRAS,
                       linea='Inteligencia artificial', coautores=coautores)
    ir_a_ruta(navegador, '/autor')
    clic_en_panel(navegador, 'Mis artículos')
    esperar_listado(navegador)
    fila = fila_de_articulo(navegador, nombre)
    assert fila is not None and 'Carlos Ramírez' in fila and 'Ana Torres' in fila, fila

    abrir_formulario_articulo(navegador)
    repetidos = [coautores[0], dict(coautores[1], email=coautores[0]['email'])]
    llenar_articulo(navegador, titulo=titulo('Correo repetido'), resumen=RESUMEN, palabras_clave=PALABRAS,
                    linea='Inteligencia artificial', coautores=repetidos)
    enviar_articulo(navegador)
    visible_text(navegador, 'Cada autor debe tener un correo electrónico diferente.', 15)
    evidencia('EXITO')


def test_hu008_cp11_responsable_versiones(navegador, evidencia):
    """Matriz CP-012. «Responsable de versiones» queda en Carlos Ramírez."""
    login(navegador, 'autor')
    abrir_formulario_articulo(navegador)
    nombre = titulo('Responsable de versiones')
    llenar_articulo(navegador, titulo=nombre, resumen=RESUMEN, palabras_clave=PALABRAS,
                    linea='Inteligencia artificial', coautores=coautores_de_prueba(ID + '-11'), responsable=1)
    radios = navegador.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
    assert radios[1].is_selected(), 'Carlos Ramírez no quedó como responsable'
    assert not radios[0].is_selected()
    evidencia('ANTES_DE_ENVIAR')
    enviar_articulo(navegador)
    visible_text(navegador, mensaje_registro(nombre), 90)
    evidencia('EXITO')


def test_hu008_cp12_coautores_sin_cuenta(navegador, evidencia):
    """Matriz CP-013. Los coautores (qa.coautor…@example.com) no tienen cuenta y aun así se registra."""
    login(navegador, 'autor')
    abrir_formulario_articulo(navegador)
    assert 'Los coautores pueden participar aunque no tengan una cuenta en la plataforma.' in body(navegador)
    nombre = titulo('Coautores sin cuenta')
    llenar_articulo(navegador, titulo=nombre, resumen=RESUMEN, palabras_clave=PALABRAS,
                    linea='Inteligencia artificial', coautores=coautores_de_prueba(ID + '-12'))
    enviar_articulo(navegador)
    visible_text(navegador, mensaje_registro(nombre), 90)
    evidencia('EXITO')
