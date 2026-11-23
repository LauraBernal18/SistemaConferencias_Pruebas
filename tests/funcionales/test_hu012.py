# HU-012 · Modificar artículo · casos HU012-CP01 a CP05
# Estado al 21/11: el backend (rama feature/SDGC-17-backend-modificar-articulo) bloquea toda
# modificación hasta integrar el permiso de SDGC-178, y no hay pantalla. Las pruebas quedan
# Bloqueadas (skip) hasta que aparezca la opción «Modificar» en el detalle del artículo.
# Campos modificables según el backend: título, resumen, palabras clave y línea temática.

from selenium.webdriver.common.by import By

from sgc_helpers import body
from sgc_articulos import abrir_consulta_comite, abrir_mis_articulos, datos_previos, ir_a_ruta
from sgc_sprint2 import (abrir_detalle, abrir_modificacion, boton_en_detalle, esperar_detalle,
                         escribir_en, guardar, id_de_articulo)


def _campo(navegador, nombre):
    return navegador.find_element(By.CSS_SELECTOR, f'[name="{nombre}"], #{nombre}')


def test_hu012_cp01_modificar_datos_generales(navegador, evidencia, datos_previos):
    """El autor cambia el resumen y las palabras clave de su artículo y el detalle lo muestra."""
    titulo = datos_previos['titulos']['ing2']
    abrir_modificacion(navegador, titulo)
    escribir_en(_campo(navegador, 'resumen'), 'Resumen modificado por la prueba HU-012.')
    escribir_en(_campo(navegador, 'palabras_clave'), 'pruebas, modificacion')
    guardar(navegador)
    abrir_mis_articulos(navegador, 'autor')
    texto = abrir_detalle(navegador, titulo)
    assert 'Resumen modificado por la prueba HU-012.' in texto and 'pruebas, modificacion' in texto, texto
    evidencia('EXITO')


def test_hu012_cp02_titulo_obligatorio(navegador, evidencia, datos_previos):
    """Con el título vacío no se guarda el cambio."""
    abrir_modificacion(navegador, datos_previos['titulos']['ing2'])
    escribir_en(_campo(navegador, 'titulo'), '')
    guardar(navegador)
    assert 'El título del artículo es obligatorio.' in body(navegador)
    evidencia('EXITO')


def test_hu012_cp03_cambiar_linea(navegador, evidencia, datos_previos):
    """El autor cambia la línea temática por otra de la misma conferencia."""
    from selenium.webdriver.support.ui import Select
    titulo = datos_previos['titulos']['ing2']
    abrir_modificacion(navegador, titulo)
    Select(_campo(navegador, 'id_linea')).select_by_visible_text('Bases de datos')
    guardar(navegador)
    abrir_mis_articulos(navegador, 'autor')
    assert 'Bases de datos' in abrir_detalle(navegador, titulo)
    evidencia('EXITO')


def test_hu012_cp04_comite_no_modifica(navegador, evidencia, datos_previos):
    """El comité consulta el artículo, pero no tiene la opción de modificarlo."""
    abrir_mis_articulos(navegador, 'autor')
    abrir_detalle(navegador, datos_previos['titulos']['ing2'])
    from sgc_sprint2 import exigir_boton
    exigir_boton(navegador, 'HU-012', 'Modificar', 'Editar artículo')
    navegador.execute_script('window.sessionStorage.clear(); window.localStorage.clear();')
    abrir_consulta_comite(navegador)
    abrir_detalle(navegador, datos_previos['titulos']['ing2'])
    assert boton_en_detalle(navegador, 'Modificar', 'Editar artículo') is None
    evidencia('EXITO')


def test_hu012_cp05_autor_no_modifica_ajeno(navegador, evidencia, datos_previos):
    """El autor no puede abrir ni modificar el artículo de otra autora (pedido por URL)."""
    abrir_mis_articulos(navegador, 'autor')
    abrir_detalle(navegador, datos_previos['titulos']['ing2'])
    from sgc_sprint2 import exigir_boton
    exigir_boton(navegador, 'HU-012', 'Modificar', 'Editar artículo')
    id_ajeno = id_de_articulo(navegador, datos_previos['titulos']['bd'])
    navegador.execute_script('window.sessionStorage.clear(); window.localStorage.clear();')
    abrir_mis_articulos(navegador, 'autor')
    ir_a_ruta(navegador, f'/autor/articulos?detalle={id_ajeno}')
    texto = esperar_detalle(navegador)
    assert 'Este artículo no está asociado a tu cuenta.' in texto
    assert boton_en_detalle(navegador, 'Modificar', 'Editar artículo') is None
    evidencia('EXITO')
