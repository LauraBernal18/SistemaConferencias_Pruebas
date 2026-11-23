# HU-012 · Modificar artículo · casos HU012-CP01 a CP07
# Pantalla: «Mis artículos» → botón «Editar» de la fila → /autor/articulos/<id>/editar
# (EditarArticulo.jsx, integrada el 21/11 con los PR #54 a #56).
# Campos modificables: nombre del artículo, resumen, palabras clave y línea temática.
# Los autores se muestran pero no se pueden cambiar desde esta pantalla.
# Se usa un artículo nuevo de autor@pruebas.co para no alterar los datos de HU-009, HU-010 y HU-032.

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from sgc_helpers import body
from sgc_articulos import datos_previos, fila_de_articulo, ir_a_ruta  # noqa: F401
from sgc_sprint2 import (abrir_detalle, abrir_modificacion, articulo_de_prueba, consulta_comite, mis_articulos,
                         esperar_texto, escribir, guardar, id_de_articulo)

RESUMEN_NUEVO = 'Resumen modificado por la prueba HU-012.'
PALABRAS_NUEVAS = 'pruebas, modificacion, selenium'
OBLIGATORIO = 'El título del artículo es obligatorio.'
SIN_CAMBIOS = 'No realizaste ningún cambio. Modifica algún dato antes de guardar.'
SIN_PERMISO = 'No puedes modificar este artículo'


def _exito(titulo):
    return f'El artículo «{titulo}» se actualizó correctamente.'


LINEA_INICIAL = ('Ingeniería de software', 'Sistemas de Software')  # antes y después del 22/11


def _linea_elegida(navegador):
    return Select(navegador.find_element(By.ID, 'linea-tematica')).first_selected_option.text.strip()


def _elegir_otra_linea(navegador):
    """Elige una línea habilitada distinta de la actual y devuelve su nombre."""
    lista = Select(navegador.find_element(By.ID, 'linea-tematica'))
    actual = _linea_elegida(navegador)
    for opcion in lista.options:
        texto = opcion.text.strip()
        if opcion.get_attribute('value') and texto != actual and opcion.is_enabled():
            lista.select_by_visible_text(opcion.text)
            return texto
    raise AssertionError('La convocatoria no tiene otra línea temática para elegir')


def test_hu012_cp01_autor_selecciona_su_articulo(navegador, evidencia):
    """CA-078: en «Mis artículos» el autor tiene el botón «Editar» en su artículo y abre el formulario."""
    titulo = articulo_de_prueba(navegador, 'HU-012')
    abrir_modificacion(navegador, titulo)
    assert '/editar' in navegador.current_url
    assert 'Autores del artículo' in body(navegador)
    evidencia('EXITO')


def test_hu012_cp02_muestra_datos_actuales(navegador, evidencia):
    """CA-079: el formulario trae el título, el resumen, las palabras clave y la línea actuales."""
    from sgc_articulos import PALABRAS, RESUMEN
    titulo = articulo_de_prueba(navegador, 'HU-012')
    abrir_modificacion(navegador, titulo)
    assert navegador.find_element(By.ID, 'titulo-articulo').get_attribute('value') == titulo
    assert navegador.find_element(By.ID, 'resumen-articulo').get_attribute('value') == RESUMEN
    assert navegador.find_element(By.ID, 'palabras-clave').get_attribute('value') == PALABRAS
    assert _linea_elegida(navegador) in LINEA_INICIAL
    evidencia('EXITO')


def test_hu012_cp03_modificar_y_guardar(navegador, evidencia):
    """CA-080, CA-082 y CA-084: cambia resumen, palabras clave y línea, se guarda y se informa el resultado."""
    titulo = articulo_de_prueba(navegador, 'HU-012')
    abrir_modificacion(navegador, titulo)
    escribir(navegador, 'resumen-articulo', RESUMEN_NUEVO)
    escribir(navegador, 'palabras-clave', PALABRAS_NUEVAS)
    linea = _elegir_otra_linea(navegador)
    guardar(navegador)
    esperar_texto(navegador, _exito(titulo), 60)
    evidencia('EXITO')
    # Al volver a entrar, el formulario y el detalle muestran los datos nuevos
    abrir_modificacion(navegador, titulo)
    assert navegador.find_element(By.ID, 'resumen-articulo').get_attribute('value') == RESUMEN_NUEVO
    assert navegador.find_element(By.ID, 'palabras-clave').get_attribute('value') == PALABRAS_NUEVAS
    assert _linea_elegida(navegador) == linea
    mis_articulos(navegador, 'autor')
    texto = abrir_detalle(navegador, titulo)
    assert RESUMEN_NUEVO in texto and linea.upper() in texto.upper(), texto
    evidencia('DETALLE')


def test_hu012_cp04_titulo_obligatorio(navegador, evidencia):
    """CA-081 y CA-084: con el nombre del artículo vacío no se guarda y se informa el error."""
    titulo = articulo_de_prueba(navegador, 'HU-012')
    abrir_modificacion(navegador, titulo)
    escribir(navegador, 'titulo-articulo', '')
    guardar(navegador)
    esperar_texto(navegador, OBLIGATORIO)
    evidencia('EXITO')
    mis_articulos(navegador, 'autor')
    assert fila_de_articulo(navegador, titulo) is not None, 'El título no debía cambiar'


def test_hu012_cp05_sin_cambios(navegador, evidencia):
    """CA-081 y CA-084: si no se cambia ningún dato, el sistema lo informa y no envía nada."""
    titulo = articulo_de_prueba(navegador, 'HU-012')
    abrir_modificacion(navegador, titulo)
    guardar(navegador)
    esperar_texto(navegador, SIN_CAMBIOS)
    evidencia('EXITO')


def test_hu012_cp06_autor_no_modifica_ajeno(navegador, evidencia, datos_previos):
    """CA-083: el autor escribe en la barra la dirección de edición del artículo de otra autora."""
    id_ajeno = id_de_articulo(navegador, datos_previos['titulos']['bd'])
    mis_articulos(navegador, 'autor')
    ir_a_ruta(navegador, f'/autor/articulos/{id_ajeno}/editar')
    esperar_texto(navegador, SIN_PERMISO, 60)
    assert not navegador.find_elements(By.ID, 'titulo-articulo')
    evidencia('EXITO')


def test_hu012_cp07_comite_no_modifica(navegador, evidencia):
    """Restricción: el comité consulta el artículo, pero no tiene «Editar» ni puede abrir la edición."""
    titulo = articulo_de_prueba(navegador, 'HU-012')
    abrir_modificacion(navegador, titulo)
    id_propio = navegador.current_url.rstrip('/').split('/')[-2]
    consulta_comite(navegador)
    assert fila_de_articulo(navegador, titulo) is not None
    assert not navegador.find_elements(By.CSS_SELECTOR, f'a[aria-label="Editar el artículo {titulo}"]')
    ir_a_ruta(navegador, f'/autor/articulos/{id_propio}/editar')
    time.sleep(3)
    assert '/editar' not in navegador.current_url and not navegador.find_elements(By.ID, 'titulo-articulo'), \
        'El comité no debía llegar a la pantalla de edición'
    evidencia('EXITO')
