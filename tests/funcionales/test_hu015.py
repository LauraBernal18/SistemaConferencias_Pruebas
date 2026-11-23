# HU-015 · Asignar evaluadores a los artículos · casos HU015-CP01 a CP08
# Pantalla: comité → «Consultar artículos» → botón «Asignar evaluadores» de la fila
# → /gestion/evaluadores/asignar/<id> (AsignacionEvaluadores.jsx, PR #62 del 22/11).
# No hay matriz de HU-015 en el Drive: los casos salen de los criterios CA-099 a CA-105A.
#
# Reglas del backend (SDGC-195, 197, 199, 201, 203 y 205):
# - Solo se asigna cuando terminó la postulación de la conferencia.
# - Exactamente tres evaluadores, todos del comité y con la cuenta habilitada.
# - Ningún autor del artículo (por cuenta o por correo) puede ser su evaluador.
# - Cada candidato muestra sus líneas de experiencia y si coinciden con la del artículo (CA-105A).
#
# Datos que se preparan por la API (sgc_api.py) antes de las pruebas:
# - Tres cuentas nuevas del comité («Evaluador Uno/Dos/Tres <ID>»), porque el entorno solo trae una.
# - Un artículo en la «Conferencia de Pruebas QA» y otro en el «Congreso de Pruebas»
#   (este con «Evaluador Tres» como coautor, para la regla de autoría).
# - La postulación de la conferencia QA se cierra un momento para poder asignar
#   y al terminar se restauran sus fechas originales.

import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from sgc_helpers import body
from sgc_articulos import esperar_listado, fila_de_articulo, id_unico, ir_a_ruta, xpath_titulo
from sgc_sprint2 import abrir_detalle, consulta_comite, esperar_texto, mis_articulos
import sgc_api as api

EXITO = 'Evaluadores asignados correctamente.'
EXACTAMENTE_TRES = 'Un artículo debe tener exactamente tres evaluadores.'
POSTULACION_ABIERTA = 'La asignación de evaluadores solo está disponible cuando termina el periodo de postulaciones.'
COINCIDE = 'Coincide con la línea temática'
DIFERENTE = 'Línea temática diferente'


# ---------------------------------------------------------------------------
# Preparación de datos
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def datos_hu015():
    identificador = id_unico()
    admin = api.token_de('admin')
    autor = api.token_de('autor')

    convs = api.convocatorias(autor)
    qa = api.buscar_convocatoria(convs, 'Conferencia de Pruebas QA')
    congreso = api.buscar_convocatoria(convs, 'Congreso de Pruebas')

    # Fechas de postulación de la conferencia QA (se guardan para restaurarlas)
    lista = api.plazos(admin, qa['id'])
    postulacion = api.plazo_de(lista, 'POSTULACION')
    evaluacion = api.plazo_de(lista, 'EVALUACION')
    inicio_original = api.fecha(postulacion['fecha_inicio'])
    fin_original = api.fecha(postulacion['fecha_fin'])
    inicio_evaluacion = api.fecha(evaluacion['fecha_inicio'])

    try:
        # 1. Si la postulación QA está cerrada, se abre un rato para registrar el artículo
        if api.ahora() > fin_original:
            fin_temporal = min(inicio_evaluacion - api.timedelta(minutes=1), api.ahora() + api.timedelta(hours=2))
            api.cambiar_plazo(admin, qa['id'], postulacion['id_plazo'],
                              min(inicio_original, api.ahora() - api.timedelta(days=1)), fin_temporal)

        # 2. Tres miembros nuevos del comité
        evaluadores = []
        for numero, palabra in enumerate(('Uno', 'Dos', 'Tres'), start=1):
            datos = {'nombre': 'Evaluador', 'apellido': f'{palabra} {identificador}',
                     'correo': f'qa.evaluador{numero}.{identificador}@example.com'}
            api.crear_usuario(admin, datos['nombre'], datos['apellido'], datos['correo'], ['COMITE'])
            datos['completo'] = f"{datos['nombre']} {datos['apellido']}"
            evaluadores.append(datos)

        # 3. Artículo en la conferencia QA (aquí se hace la asignación completa)
        linea_qa, nombre_linea_qa = api.id_linea(qa)
        titulo_qa = f'QA HU015 {identificador} – Asignación de evaluadores'
        id_qa = api.crear_articulo(autor, qa['id'], linea_qa, titulo_qa)

        # 4. Artículo en el Congreso (postulación abierta) con Evaluador Tres como coautor
        linea_cg, nombre_linea_cg = api.id_linea(congreso, 'Sistemas de Software', 'Ingeniería de software')
        titulo_cg = f'QA HU015 {identificador} – Postulación abierta'
        coautor = {'nombres': 'Evaluador', 'apellidos': f'Tres {identificador}',
                   'email': evaluadores[2]['correo'], 'institucion': 'Universidad del Valle'}
        id_cg = api.crear_articulo(autor, congreso['id'], linea_cg, titulo_cg, [coautor])

        # 5. Se cierra la postulación QA (hace 2 minutos) para poder asignar
        api.cambiar_plazo(admin, qa['id'], postulacion['id_plazo'],
                          min(inicio_original, api.ahora() - api.timedelta(days=1)),
                          api.ahora() - api.timedelta(minutes=2))

        yield {
            'id': identificador, 'evaluadores': evaluadores,
            'qa': {'id': id_qa, 'titulo': titulo_qa, 'linea': nombre_linea_qa},
            'congreso': {'id': id_cg, 'titulo': titulo_cg, 'linea': nombre_linea_cg},
        }
    finally:
        # Se restauran las fechas originales de la postulación QA
        api.cambiar_plazo(api.token_de('admin'), qa['id'], postulacion['id_plazo'], inicio_original, fin_original)


# ---------------------------------------------------------------------------
# Funciones de la pantalla de asignación
# ---------------------------------------------------------------------------

def _fila(navegador, titulo):
    return WebDriverWait(navegador, 60).until(EC.presence_of_element_located(
        (By.XPATH, f'{xpath_titulo(titulo)}/ancestor::div[contains(@class,"grid")][1]')))


def _abrir_asignacion(navegador, titulo):
    """Comité → «Consultar artículos» → botón de asignación de la fila del artículo."""
    consulta_comite(navegador)
    enlace = _fila(navegador, titulo).find_element(By.XPATH, './/a[contains(@href, "/gestion/evaluadores/asignar/")]')
    navegador.execute_script('arguments[0].scrollIntoView({block: "center"})', enlace)
    enlace.click()
    _esperar_asignacion(navegador)


def _esperar_asignacion(navegador):
    def cargo(d):
        texto = body(d)
        return 'Seleccionados:' in texto and (
            d.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"][aria-label^="Seleccionar a "]')
            or d.find_elements(By.CSS_SELECTOR, '[role="alert"]') or 'No se encontraron' in texto)
    WebDriverWait(navegador, 60).until(cargo)
    time.sleep(1.5)  # deja terminar la consulta de los evaluadores ya asignados


def _casilla(navegador, nombre):
    return navegador.find_element(By.CSS_SELECTOR, f'input[aria-label="Seleccionar a {nombre}"]')


def _marcar(navegador, nombre):
    casilla = _casilla(navegador, nombre)
    navegador.execute_script('arguments[0].scrollIntoView({block: "center"})', casilla)
    if not casilla.is_selected():
        casilla.click()
        time.sleep(0.3)


def _desmarcar_todo(navegador):
    for casilla in navegador.find_elements(By.CSS_SELECTOR, 'input[aria-label^="Seleccionar a "]'):
        if casilla.is_selected():
            navegador.execute_script('arguments[0].scrollIntoView({block: "center"})', casilla)
            casilla.click()
            time.sleep(0.2)


def _tarjeta(navegador, nombre):
    """Texto de la tarjeta del candidato (la etiqueta que contiene su casilla)."""
    return _casilla(navegador, nombre).find_element(By.XPATH, './ancestor::label[1]').text


def _nombres_candidatos(navegador):
    return [c.get_attribute('aria-label').replace('Seleccionar a ', '', 1)
            for c in navegador.find_elements(By.CSS_SELECTOR, 'input[aria-label^="Seleccionar a "]')]


def _boton_asignar(navegador):
    return navegador.find_element(By.XPATH, '//button[normalize-space()="Asignar evaluadores" or normalize-space()="Guardando..."]')


# ---------------------------------------------------------------------------
# Casos
# ---------------------------------------------------------------------------

def test_hu015_cp01_consultar_articulos_sin_evaluadores(navegador, evidencia, datos_hu015):
    """CA-099: el comité filtra «Sin evaluadores» y ve el artículo pendiente con 0/3 y «Asignar evaluadores»."""
    consulta_comite(navegador)
    casilla = navegador.find_element(By.XPATH, '//label[contains(normalize-space(), "Sin evaluadores")]//input')
    navegador.execute_script('arguments[0].scrollIntoView({block: "center"})', casilla)
    casilla.click()
    esperar_listado(navegador)
    texto = fila_de_articulo(navegador, datos_hu015['qa']['titulo'])
    assert texto is not None, 'El artículo sin evaluadores no aparece con el filtro'
    assert '0/3 evaluadores' in texto and 'Asignar evaluadores' in texto, texto
    evidencia('EXITO')


def test_hu015_cp02_candidatos_y_linea_tematica(navegador, evidencia, datos_hu015):
    """CA-100 y CA-105A: la pantalla muestra el artículo, su línea, los tres requeridos y los candidatos
    del comité con sus líneas. Comité Pruebas tiene experiencia en la línea del artículo y aparece primero."""
    articulo = datos_hu015['congreso']
    _abrir_asignacion(navegador, articulo['titulo'])
    texto = body(navegador)
    assert articulo['titulo'] in texto and f"Línea temática: {articulo['linea']}" in texto, texto
    assert 'Evaluadores requeridos: 3' in texto
    nombres = _nombres_candidatos(navegador)
    uno, dos = (e['completo'] for e in datos_hu015['evaluadores'][:2])
    assert 'Comité Pruebas' in nombres and uno in nombres and dos in nombres, nombres
    assert COINCIDE in _tarjeta(navegador, 'Comité Pruebas'), _tarjeta(navegador, 'Comité Pruebas')
    assert articulo['linea'] in _tarjeta(navegador, 'Comité Pruebas')
    assert DIFERENTE in _tarjeta(navegador, uno) and 'Sin áreas registradas' in _tarjeta(navegador, uno)
    assert nombres[0] == 'Comité Pruebas', f'Quien coincide con la línea debía aparecer primero: {nombres}'
    evidencia('EXITO')


def test_hu015_cp03_exactamente_tres(navegador, evidencia, datos_hu015):
    """CA-102: con dos seleccionados no se puede asignar y no deja marcar un cuarto evaluador."""
    _abrir_asignacion(navegador, datos_hu015['qa']['titulo'])
    _desmarcar_todo(navegador)
    uno, dos, tres = (e['completo'] for e in datos_hu015['evaluadores'])
    _marcar(navegador, uno)
    _marcar(navegador, dos)
    assert 'Seleccionados: 2 de 3' in body(navegador)
    assert not _boton_asignar(navegador).is_enabled()
    evidencia('DOS')
    _marcar(navegador, tres)
    cuarta = _casilla(navegador, 'Comité Pruebas')
    navegador.execute_script('arguments[0].scrollIntoView({block: "center"})', cuarta)
    cuarta.click()
    esperar_texto(navegador, EXACTAMENTE_TRES)
    assert 'Seleccionados: 3 de 3' in body(navegador)
    assert not _casilla(navegador, 'Comité Pruebas').is_selected()
    evidencia('EXITO')


def test_hu015_cp04_postulacion_abierta(navegador, evidencia, datos_hu015):
    """CA-102 y restricción 1: mientras la postulación está abierta no se completa la asignación."""
    _abrir_asignacion(navegador, datos_hu015['congreso']['titulo'])
    _desmarcar_todo(navegador)
    uno, dos = (e['completo'] for e in datos_hu015['evaluadores'][:2])
    for nombre in ('Comité Pruebas', uno, dos):
        _marcar(navegador, nombre)
    _boton_asignar(navegador).click()
    esperar_texto(navegador, POSTULACION_ABIERTA, 60)
    evidencia('EXITO')


def test_hu015_cp05_asignar_tres_evaluadores(navegador, evidencia, datos_hu015):
    """CA-101 y CA-103: con la postulación cerrada, el comité asigna tres evaluadores del comité."""
    _abrir_asignacion(navegador, datos_hu015['qa']['titulo'])
    _desmarcar_todo(navegador)
    for evaluador in datos_hu015['evaluadores']:
        _marcar(navegador, evaluador['completo'])
    assert 'Seleccionados: 3 de 3' in body(navegador)
    _boton_asignar(navegador).click()
    esperar_texto(navegador, EXITO, 60)
    evidencia('EXITO')


def test_hu015_cp06_consultar_asignados(navegador, evidencia, datos_hu015):
    """CA-103 y CA-104: los tres evaluadores quedan guardados y se pueden consultar después
    (listado con 3/3, pantalla con las tres casillas marcadas y detalle del artículo)."""
    articulo = datos_hu015['qa']
    nombres = [e['completo'] for e in datos_hu015['evaluadores']]
    consulta_comite(navegador)
    texto = fila_de_articulo(navegador, articulo['titulo'])
    assert '3/3 evaluadores' in texto and 'Ver evaluadores asignados' in texto, texto
    detalle = abrir_detalle(navegador, articulo['titulo'])
    for nombre in nombres:
        assert nombre in detalle, detalle
    evidencia('DETALLE')
    _abrir_asignacion(navegador, articulo['titulo'])
    assert all(_casilla(navegador, n).is_selected() for n in nombres)
    assert 'Seleccionados: 3 de 3' in body(navegador)
    evidencia('EXITO')


def test_hu015_cp07_solo_comite_y_no_autores(navegador, evidencia, datos_hu015):
    """CA-105 y restricción de autoría: los candidatos son solo del comité (no salen autor ni administrador)
    y Evaluador Tres, coautor del artículo, no aparece para evaluarlo."""
    _abrir_asignacion(navegador, datos_hu015['congreso']['titulo'])
    nombres = _nombres_candidatos(navegador)
    assert 'Autor Pruebas' not in nombres and 'Admin Pruebas' not in nombres, nombres
    assert datos_hu015['evaluadores'][2]['completo'] not in nombres, nombres
    evidencia('EXITO')


def test_hu015_cp08_autor_sin_acceso(navegador, evidencia, datos_hu015):
    """Restricción: el autor no tiene el botón de asignación y si escribe la dirección vuelve a su panel."""
    mis_articulos(navegador, 'autor')
    assert fila_de_articulo(navegador, datos_hu015['qa']['titulo']) is not None
    assert not navegador.find_elements(By.CSS_SELECTOR, 'a[href*="/gestion/evaluadores/asignar/"]')
    ir_a_ruta(navegador, f"/gestion/evaluadores/asignar/{datos_hu015['qa']['id']}")
    time.sleep(3)
    assert '/gestion/evaluadores/asignar/' not in navegador.current_url
    assert not navegador.find_elements(By.CSS_SELECTOR, 'input[aria-label^="Seleccionar a "]')
    evidencia('EXITO')

