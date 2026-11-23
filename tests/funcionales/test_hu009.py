# HU-009 · Consultar artículos · casos del diseño HU009-CP01 a CP08 (los mismos del Excel)
# Datos previos: 3 artículos de autor@pruebas.co y 1 de otra autora (fixture datos_previos).
# Como el entorno es compartido, solo se revisan los artículos de esa preparación.

from sgc_helpers import body, login
# datos_previos es un fixture: se importa para que pytest lo encuentre (por eso no se usa directamente)
from sgc_articulos import (SIN_RESULTADOS, abrir_consulta_comite, abrir_mis_articulos, contiene_linea, datos_previos,
                           elegir_opcion, encabezado_del_listado, esperar_listado, fila_de_articulo,
                           ir_a_ruta, texto_del_titulo, visibles)


def test_hu009_cp01_acceso_comite(navegador, evidencia, datos_previos):
    """Matriz CP-001. El comité abre «Consultar artículos»."""
    abrir_consulta_comite(navegador)
    assert texto_del_titulo(navegador) == 'Artículos postulados'
    evidencia('EXITO')


def test_hu009_cp02_acceso_autor(navegador, evidencia, datos_previos):
    """Matriz CP-002. El autor ve solo sus artículos en «Mis artículos»."""
    abrir_mis_articulos(navegador, 'autor')
    assert texto_del_titulo(navegador) == 'Mis artículos'
    v = visibles(navegador, datos_previos['titulos'])
    assert v['ing1'] and v['ing2'] and v['ia'], v
    assert not v['bd'], 'El autor ve el artículo de otra autora'
    evidencia('EXITO')


def test_hu009_cp03_listado_registrados(navegador, evidencia, datos_previos):
    """Matriz CP-003. El comité ve los 4 artículos de la preparación."""
    abrir_consulta_comite(navegador)
    v = visibles(navegador, datos_previos['titulos'])
    assert all(v.values()), v
    evidencia('EXITO')


def test_hu009_cp04_informacion_relevante(navegador, evidencia, datos_previos):
    """Matriz CP-004. Columnas Título, Autor, Línea temática, Fecha y Estado con datos correctos."""
    abrir_consulta_comite(navegador)
    encabezado = encabezado_del_listado(navegador)
    for columna in ('TÍTULO', 'AUTOR', 'LÍNEA TEMÁTICA', 'FECHA', 'ESTADO'):
        assert columna in encabezado, encabezado
    fila = fila_de_articulo(navegador, datos_previos['titulos']['ia'])
    assert fila is not None
    assert 'Autor Pruebas' in fila and contiene_linea(fila, 'Inteligencia artificial'), fila
    assert 'REGISTRADO' in fila.upper(), fila
    evidencia('EXITO')


def test_hu009_cp05_filtro_bases_de_datos(navegador, evidencia, datos_previos):
    """Matriz CP-006. Filtro Línea temática: Bases de datos."""
    abrir_consulta_comite(navegador)
    elegir_opcion(navegador, 'filtro-linea', 'Bases de datos')
    esperar_listado(navegador)
    v = visibles(navegador, datos_previos['titulos'])
    assert v == {'ing1': False, 'ing2': False, 'ia': False, 'bd': True}, v
    evidencia('EXITO')


def test_hu009_cp06_filtro_ingenieria_software(navegador, evidencia, datos_previos):
    """Matriz CP-007. Filtro Línea temática: Ingeniería de software."""
    abrir_consulta_comite(navegador)
    elegir_opcion(navegador, 'filtro-linea', 'Ingeniería de software')
    esperar_listado(navegador)
    v = visibles(navegador, datos_previos['titulos'])
    assert v == {'ing1': True, 'ing2': True, 'ia': False, 'bd': False}, v
    evidencia('EXITO')


def test_hu009_cp07_sin_resultados(navegador, evidencia, datos_previos):
    """Matriz CP-008. Estado «Aceptado»: ningún artículo está aceptado."""
    abrir_consulta_comite(navegador)
    elegir_opcion(navegador, 'filtro-estado', 'Aceptado')
    esperar_listado(navegador)
    assert SIN_RESULTADOS in body(navegador)
    evidencia('EXITO')


def test_hu009_cp08_autor_no_entra_a_gestion(navegador, evidencia, datos_previos):
    """Matriz CP-005. El autor escribe la ruta /gestion/articulos y vuelve a su panel."""
    login(navegador, 'autor')
    ir_a_ruta(navegador, '/gestion/articulos')
    assert navegador.current_url.endswith('/autor'), navegador.current_url
    evidencia('EXITO')
