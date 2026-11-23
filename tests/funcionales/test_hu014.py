# HU-014 · Gestionar versiones e historial del artículo · casos HU014-CP01 a CP07
# Pantalla: «Mis artículos» → botón «Gestionar versiones» de la fila → /autor/articulos/<id>/versiones
# (VersionesArticulo.jsx, integrada el 21/11 con los PR #48 a #52).
# Reglas: solo el autor responsable carga versiones, la versión 1 es ORIGINAL y las siguientes
# CORREGIDA, las anteriores se conservan, la más reciente se marca como «Versión actual»
# y la primera versión exige el plazo de postulación vigente.
# Se usa un artículo nuevo de autor@pruebas.co (el mismo para CP01 a CP05, en ese orden).
# CA-095 (rechazo después de la fecha límite) no se automatiza: necesita un artículo sin versiones
# en una convocatoria cerrada, y en una convocatoria cerrada ya no se pueden registrar artículos.

from selenium.webdriver.common.by import By

from sgc_helpers import body
from sgc_articulos import datos_previos, ir_a_ruta  # noqa: F401
from sgc_sprint2 import (MENSAJE_AJENO, abrir_versiones, mis_articulos, articulo_de_prueba, esperar_texto,
                         esperar_versiones, historial, id_de_articulo, pulsar_cargar, subir_archivo)

SIN_VERSIONES = 'Este artículo todavía no tiene versiones cargadas'
SIN_ARCHIVO = 'No ha seleccionado ningún archivo. Elija el PDF de la nueva versión antes de cargarla.'
NO_PDF = 'El archivo "no_es_pdf.txt" no es un PDF. Seleccione un archivo con extensión .pdf.'
SOLO_RESPONSABLE = 'Solo el autor responsable puede cargar versiones del artículo.'


def _exito(numero, archivo):
    return f'La versión {numero} del artículo se cargó correctamente (archivo: {archivo}).'


def test_hu014_cp01_acceder_a_versiones(navegador, evidencia):
    """CA-091 y CA-098B: el autor entra a «Gestionar versiones» y ve la carga y el historial (vacío)."""
    titulo = articulo_de_prueba(navegador, 'HU-014')
    abrir_versiones(navegador, titulo)
    texto = body(navegador)
    assert 'Cargar nueva versión' in texto and 'Historial de versiones' in texto
    assert SIN_VERSIONES in historial(navegador)
    assert navegador.find_element(By.ID, 'archivo-version').is_enabled()
    evidencia('EXITO')


def test_hu014_cp02_cargar_version_original(navegador, evidencia):
    """CA-092, CA-096 y CA-097: el autor responsable carga un PDF válido y queda como Versión 1 · Original."""
    titulo = articulo_de_prueba(navegador, 'HU-014')
    abrir_versiones(navegador, titulo)
    subir_archivo(navegador, 'articulo_prueba_v1.pdf')
    esperar_texto(navegador, _exito(1, 'articulo_prueba_v1.pdf'), 90)
    esperar_texto(navegador, '1 versión')
    texto = historial(navegador)
    assert 'Versión 1' in texto and 'ORIGINAL' in texto.upper() and 'articulo_prueba_v1.pdf' in texto, texto
    assert 'VERSIÓN ACTUAL' in texto.upper(), texto
    evidencia('EXITO')


def test_hu014_cp03_reemplazar_y_conservar_historial(navegador, evidencia):
    """CA-094, CA-098A y CA-098C: una nueva carga queda como Versión 2 · Corregida y actual,
    y la Versión 1 se conserva en el historial."""
    titulo = articulo_de_prueba(navegador, 'HU-014')
    abrir_versiones(navegador, titulo)
    subir_archivo(navegador, 'articulo_prueba_v2.pdf')
    esperar_texto(navegador, _exito(2, 'articulo_prueba_v2.pdf'), 90)
    esperar_texto(navegador, '2 versiones')
    texto = historial(navegador)
    assert 'Versión 2' in texto and 'CORREGIDA' in texto.upper() and 'articulo_prueba_v2.pdf' in texto, texto
    assert 'Versión 1' in texto and 'articulo_prueba_v1.pdf' in texto, texto
    # La versión actual es la primera de la lista (la más reciente)
    primera = navegador.find_element(By.CSS_SELECTOR, 'section[aria-labelledby="titulo-historial"] li').text
    assert 'Versión 2' in primera and 'VERSIÓN ACTUAL' in primera.upper(), primera
    evidencia('EXITO')


def test_hu014_cp04_archivo_no_pdf(navegador, evidencia):
    """CA-093 y CA-098: un archivo que no es PDF se rechaza con un mensaje y no se carga."""
    titulo = articulo_de_prueba(navegador, 'HU-014')
    abrir_versiones(navegador, titulo)
    antes = historial(navegador)
    subir_archivo(navegador, 'no_es_pdf.txt', enviar=False)
    esperar_texto(navegador, NO_PDF)
    evidencia('EXITO')
    pulsar_cargar(navegador)
    assert historial(navegador) == antes


def test_hu014_cp05_sin_archivo(navegador, evidencia):
    """CA-098: si se pulsa «Cargar nueva versión» sin elegir archivo, se informa el error."""
    titulo = articulo_de_prueba(navegador, 'HU-014')
    abrir_versiones(navegador, titulo)
    pulsar_cargar(navegador)
    esperar_texto(navegador, SIN_ARCHIVO)
    evidencia('EXITO')


def test_hu014_cp06_solo_el_responsable(navegador, evidencia, datos_previos):
    """Restricción: en el artículo con varios autores el responsable es Carlos Ramírez (sin cuenta),
    así que autor@pruebas.co ve el historial, pero no puede cargar versiones."""
    abrir_versiones(navegador, datos_previos['titulos']['ia'])
    assert SOLO_RESPONSABLE in body(navegador)
    assert not navegador.find_element(By.ID, 'archivo-version').is_enabled()
    assert not navegador.find_element(
        By.XPATH, '//button[@type="submit"][contains(normalize-space(), "Cargar nueva versión")]').is_enabled()
    evidencia('EXITO')


def test_hu014_cp07_autor_no_gestiona_ajeno(navegador, evidencia, datos_previos):
    """Restricción: el autor escribe en la barra la dirección de versiones del artículo de otra autora."""
    id_ajeno = id_de_articulo(navegador, datos_previos['titulos']['bd'])
    mis_articulos(navegador, 'autor')
    ir_a_ruta(navegador, f'/autor/articulos/{id_ajeno}/versiones')
    esperar_versiones(navegador)
    alerta = navegador.find_element(By.CSS_SELECTOR, 'section[role="alert"]').text
    assert MENSAJE_AJENO in alerta, alerta
    assert not navegador.find_elements(By.ID, 'archivo-version')
    evidencia('EXITO')
