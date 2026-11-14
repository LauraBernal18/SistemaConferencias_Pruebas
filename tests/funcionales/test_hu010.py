# HU-010 · Filtrar artículos · casos del diseño HU010-CP01 a CP09 (+ CP-009 de la matriz)
# Cuenta: comite@pruebas.co → «Consultar artículos». Datos previos: fixture datos_previos.

import pytest
from selenium.webdriver.common.by import By

from sgc_helpers import body
# datos_previos es un fixture: se importa para que pytest lo encuentre (por eso no se usa directamente)
from sgc_articulos import (SIN_RESULTADOS, abrir_consulta_comite, datos_previos, elegir_opcion,
                           esperar_listado, filtrar, textos_de_opciones, visibles)


def test_hu010_cp01_filtros_disponibles(navegador, evidencia, datos_previos):
    """Matriz CP-001. Filtros de línea y estado y el botón «Limpiar filtros»."""
    abrir_consulta_comite(navegador)
    estados = textos_de_opciones(navegador, 'filtro-estado')
    lineas = textos_de_opciones(navegador, 'filtro-linea')
    for estado in ('Todos los estados', 'Registrado', 'En revisión', 'Aceptado', 'Rechazado'):
        assert estado in estados, estados
    assert 'Todas las líneas' in lineas and 'Ingeniería de software' in lineas, lineas
    assert navegador.find_elements(By.XPATH, '//button[contains(., "Limpiar filtros")]')
    evidencia('EXITO')


def test_hu010_cp02_linea_ingenieria_software(navegador, evidencia, datos_previos):
    """Matriz CP-002. Solo los 2 artículos de Ingeniería de software."""
    abrir_consulta_comite(navegador)
    filtrar(navegador, 'Ingeniería de software', 'Todos los estados')
    v = visibles(navegador, datos_previos['titulos'])
    assert v == {'ing1': True, 'ing2': True, 'ia': False, 'bd': False}, v
    evidencia('EXITO')


def test_hu010_cp03_estado(navegador, evidencia, datos_previos):
    """Matriz CP-003. (a) Registrado muestra los 4. (b) Rechazado no muestra ninguno."""
    abrir_consulta_comite(navegador)
    filtrar(navegador, 'Todas las líneas', 'Registrado')
    v = visibles(navegador, datos_previos['titulos'])
    assert all(v.values()), v
    evidencia('REGISTRADO')
    elegir_opcion(navegador, 'filtro-estado', 'Rechazado')
    esperar_listado(navegador)
    assert SIN_RESULTADOS in body(navegador)
    evidencia('RECHAZADO')


def test_hu010_cp04_linea_bases_de_datos(navegador, evidencia, datos_previos):
    """No está en la matriz. Solo el artículo de Bases de datos."""
    abrir_consulta_comite(navegador)
    filtrar(navegador, 'Bases de datos', 'Todos los estados')
    v = visibles(navegador, datos_previos['titulos'])
    assert v == {'ing1': False, 'ing2': False, 'ia': False, 'bd': True}, v
    evidencia('EXITO')


def test_hu010_cp05_linea_y_estado(navegador, evidencia, datos_previos):
    """Matriz CP-004. Ingeniería de software + Registrado."""
    abrir_consulta_comite(navegador)
    filtrar(navegador, 'Ingeniería de software', 'Registrado')
    v = visibles(navegador, datos_previos['titulos'])
    assert v == {'ing1': True, 'ing2': True, 'ia': False, 'bd': False}, v
    evidencia('EXITO')


def test_hu010_cp06_sin_resultados(navegador, evidencia, datos_previos):
    """Matriz CP-005. Bases de datos + Aceptado."""
    abrir_consulta_comite(navegador)
    filtrar(navegador, 'Bases de datos', 'Aceptado')
    assert SIN_RESULTADOS in body(navegador)
    evidencia('EXITO')


def test_hu010_cp07_limpiar_filtros(navegador, evidencia, datos_previos):
    """Matriz CP-006. Con los filtros de CP05, «Limpiar filtros» vuelve a mostrar todo."""
    abrir_consulta_comite(navegador)
    filtrar(navegador, 'Ingeniería de software', 'Registrado')
    navegador.find_element(By.XPATH, '//button[contains(., "Limpiar filtros")]').click()
    esperar_listado(navegador)
    assert navegador.find_element(By.ID, 'filtro-linea').get_attribute('value') == ''
    assert navegador.find_element(By.ID, 'filtro-estado').get_attribute('value') == ''
    v = visibles(navegador, datos_previos['titulos'])
    assert all(v.values()), v
    evidencia('EXITO')


@pytest.mark.skip(reason='HU010-CP08 (matriz CP-007): la pantalla «Mis artículos» del autor no tiene filtros.')
def test_hu010_cp08_autor_sin_filtros():
    pass


def test_hu010_cp09_comite_inteligencia_artificial(navegador, evidencia, datos_previos):
    """Matriz CP-008. Línea Inteligencia artificial: solo el artículo de 3 autores."""
    abrir_consulta_comite(navegador)
    filtrar(navegador, 'Inteligencia artificial', 'Todos los estados')
    v = visibles(navegador, datos_previos['titulos'])
    assert v == {'ing1': False, 'ing2': False, 'ia': True, 'bd': False}, v
    evidencia('EXITO')


@pytest.mark.skip(reason='Matriz HU010-CP-009: no hay pantalla para deshabilitar un artículo; '
                         'requiere que desarrollo lo haga en la base de datos.')
def test_hu010_articulos_habilitados():
    pass
