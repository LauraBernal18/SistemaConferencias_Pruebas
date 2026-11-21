# HU-014 · Gestionar versiones e historial del artículo · casos HU014-CP01 a CP06
# Estado al 21/11: el backend (rama feature/SDGC-19-backend-versiones-articulo) no está en develop
# y no hay pantalla de carga. Mientras tanto las pruebas quedan Bloqueadas (skip) con el motivo.
# Reglas tomadas del backend: solo el autor responsable carga versiones, la versión 1 es ORIGINAL
# y las siguientes CORREGIDA, las anteriores se conservan y la primera exige plazo de postulación vigente.

from sgc_helpers import body
from sgc_articulos import abrir_consulta_comite, abrir_mis_articulos, datos_previos
from sgc_sprint2 import (abrir_carga_version, abrir_detalle, boton_en_detalle, cerrar_detalle,
                         esperar_texto, exigir_boton, subir_archivo, texto_del_detalle)

EXITO = 'La versión del artículo se cargó correctamente.'


def test_hu014_cp01_cargar_version_original(navegador, evidencia, datos_previos):
    """El autor responsable carga el PDF y queda como Versión 1 · ORIGINAL."""
    titulo = datos_previos['titulos']['ing1']
    abrir_carga_version(navegador, titulo)
    subir_archivo(navegador, 'articulo_prueba_v1.pdf')
    esperar_texto(navegador, EXITO, 60)
    evidencia('EXITO')
    texto = texto_del_detalle(navegador)
    assert 'Versión 1' in texto and 'ORIGINAL' in texto.upper() and 'articulo_prueba_v1.pdf' in texto, texto


def test_hu014_cp02_cargar_version_corregida(navegador, evidencia, datos_previos):
    """Una segunda carga queda como Versión 2 · CORREGIDA y la versión 1 se conserva (historial)."""
    titulo = datos_previos['titulos']['ing1']
    abrir_carga_version(navegador, titulo)
    subir_archivo(navegador, 'articulo_prueba_v2.pdf')
    esperar_texto(navegador, EXITO, 60)
    texto = texto_del_detalle(navegador)
    assert 'Versión 2' in texto and 'CORREGIDA' in texto.upper(), texto
    assert 'Versión 1' in texto and 'articulo_prueba_v1.pdf' in texto, texto
    evidencia('EXITO')


def test_hu014_cp03_sin_archivo(navegador, evidencia, datos_previos):
    """Si no se elige archivo, se pide seleccionarlo."""
    abrir_carga_version(navegador, datos_previos['titulos']['ing2'])
    navegador.find_element('xpath', '//button[@type="submit"] | //button[contains(normalize-space(), "Cargar")]').click()
    esperar_texto(navegador, 'Debe seleccionar un archivo')
    evidencia('EXITO')


def test_hu014_cp04_archivo_no_pdf(navegador, evidencia, datos_previos):
    """Un archivo que no es PDF no se acepta."""
    abrir_carga_version(navegador, datos_previos['titulos']['ing2'])
    subir_archivo(navegador, 'no_es_pdf.txt')
    assert 'PDF' in body(navegador) and EXITO not in body(navegador)
    evidencia('EXITO')


def test_hu014_cp05_solo_responsable(navegador, evidencia, datos_previos):
    """En el artículo con varios autores el responsable es Carlos Ramírez (sin cuenta),
    así que autor@pruebas.co no debe poder cargar versiones."""
    abrir_mis_articulos(navegador, 'autor')
    abrir_detalle(navegador, datos_previos['titulos']['ia'])
    exigir_boton(navegador, 'HU-014', 'Cargar versión', 'Cargar nueva versión', 'Subir versión', 'Cargar PDF')
    evidencia('RESULTADO')
    # Si el botón aparece, al intentarlo el sistema debe rechazarlo
    boton_en_detalle(navegador, 'Cargar versión', 'Cargar nueva versión', 'Subir versión', 'Cargar PDF').click()
    from sgc_sprint2 import subir_archivo as subir
    subir(navegador, 'articulo_prueba_v1.pdf')
    esperar_texto(navegador, 'Solo el autor responsable puede cargar versiones del artículo.')
    evidencia('EXITO')


def test_hu014_cp06_comite_ve_historial(navegador, evidencia, datos_previos):
    """El comité ve en el detalle las versiones cargadas por el autor (después de CP01 y CP02)."""
    abrir_consulta_comite(navegador)
    texto = abrir_detalle(navegador, datos_previos['titulos']['ing1'])
    if 'No hay versiones registradas' in texto:
        import pytest
        pytest.skip('Bloqueado: el artículo no tiene versiones porque CP01 y CP02 no se pudieron ejecutar.')
    assert 'Versión 1' in texto and 'Versión 2' in texto, texto
    evidencia('EXITO')
    cerrar_detalle(navegador)
