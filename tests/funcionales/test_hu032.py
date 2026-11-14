# HU-032 · Consultar artículos propios · casos del diseño HU032-CP01 a CP09 (+ CP-009 de la matriz)
# Datos previos: 3 artículos de autor@pruebas.co, 1 de otra autora y una cuenta sin artículos.

import pytest

from sgc_helpers import body, login
# datos_previos es un fixture: se importa para que pytest lo encuentre (por eso no se usa directamente)
from sgc_articulos import (abrir_mis_articulos, datos_previos, encabezado_del_listado, fila_de_articulo,
                           ir_a_ruta, texto_del_titulo, visibles)


def test_hu032_cp01_acceso_mis_articulos(navegador, evidencia, datos_previos):
    """Matriz CP-001."""
    abrir_mis_articulos(navegador, 'autor')
    assert texto_del_titulo(navegador) == 'Mis artículos'
    evidencia('EXITO')


def test_hu032_cp02_solo_articulos_propios(navegador, evidencia, datos_previos):
    """Matriz CP-002. Sus 3 artículos y no el de la otra autora."""
    abrir_mis_articulos(navegador, 'autor')
    v = visibles(navegador, datos_previos['titulos'])
    assert v == {'ing1': True, 'ing2': True, 'ia': True, 'bd': False}, v
    evidencia('EXITO')


def test_hu032_cp03_informacion_principal(navegador, evidencia, datos_previos):
    """Matriz CP-003. Columnas Título, Línea temática, Fecha y Estado (sin columna Autor)."""
    abrir_mis_articulos(navegador, 'autor')
    encabezado = encabezado_del_listado(navegador)
    for columna in ('TÍTULO', 'LÍNEA TEMÁTICA', 'FECHA', 'ESTADO'):
        assert columna in encabezado, encabezado
    assert 'AUTOR' not in encabezado, encabezado
    evidencia('EXITO')


def test_hu032_cp04_estado_actual(navegador, evidencia, datos_previos):
    """Matriz CP-004. Los 3 artículos muestran «Registrado» (todavía no hay otros estados)."""
    abrir_mis_articulos(navegador, 'autor')
    for clave in ('ing1', 'ing2', 'ia'):
        fila = fila_de_articulo(navegador, datos_previos['titulos'][clave])
        assert fila is not None and 'REGISTRADO' in fila.upper(), fila
    evidencia('EXITO')


@pytest.mark.skip(reason='HU032-CP05 (matriz CP-005): «Mis artículos» no tiene vista de detalle.')
def test_hu032_cp05_detalle_articulo():
    pass


@pytest.mark.skip(reason='HU032-CP06 (matriz CP-006): no hay vista de detalle; que el autor no ve '
                         'artículos ajenos se comprueba en CP02.')
def test_hu032_cp06_detalle_ajeno():
    pass


def test_hu032_cp07_sin_articulos(navegador, evidencia, datos_previos):
    """Matriz CP-007. Cuenta nueva sin artículos (Juan Pérez)."""
    abrir_mis_articulos(navegador, datos_previos['sin_articulos']['correo'])
    assert 'Todavía no tienes artículos registrados' in body(navegador)
    assert 'Cuando registres una propuesta, aparecerá aquí con su estado.' in body(navegador)
    evidencia('EXITO')


def test_hu032_cp08_correspondencia(navegador, evidencia, datos_previos):
    """Matriz CP-008. La fila coincide con lo registrado: línea, coautores, fecha de hoy y estado."""
    abrir_mis_articulos(navegador, 'autor')
    fila = fila_de_articulo(navegador, datos_previos['titulos']['ia'])
    assert fila is not None
    for texto in ('Inteligencia artificial', 'Carlos Ramírez', 'Ana Torres'):
        assert texto in fila, fila
    assert 'REGISTRADO' in fila.upper(), fila
    fecha = navegador.execute_script(
        "return new Date(arguments[0]).toLocaleDateString('es-CO', "
        "{ day: '2-digit', month: 'short', year: 'numeric' })", datos_previos['creado'])
    assert fecha in fila, f'Se esperaba la fecha {fecha} en: {fila}'
    evidencia('EXITO')


@pytest.mark.skip(reason='HU032-CP09: los artículos todavía no tienen documentos adjuntos en este sprint.')
def test_hu032_cp09_documentos_ajenos():
    pass


def test_hu032_restriccion_sin_rol_autor(navegador, evidencia, datos_previos):
    """Matriz CP-009 (no está en el diseño). El comité intenta abrir «Mis artículos»."""
    login(navegador, 'comite')
    ir_a_ruta(navegador, '/autor/articulos')
    assert navegador.current_url.endswith('/comite'), navegador.current_url
    evidencia('EXITO')
