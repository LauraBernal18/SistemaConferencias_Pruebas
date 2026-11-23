# HU-011 · Consultar detalle de artículo según permisos · casos HU011-CP01 a CP10
# También cubre HU032-CP05 y CP06 (detalle propio y ajeno), que se pasaron a esta HU.
# Datos previos: los mismos de HU-009/010/032 (3 artículos de autor@pruebas.co y 1 de otra autora).

from sgc_helpers import body, login
# datos_previos es un fixture: se importa para que pytest lo encuentre
from sgc_articulos import abrir_consulta_comite, abrir_mis_articulos, clic_en_panel, datos_previos, esperar_listado
from sgc_sprint2 import (ERROR_DETALLE, MENSAJE_AJENO, MENSAJE_NO_EXISTE, TITULO_MODAL, abrir_detalle,
                         abrir_detalle_por_url, cerrar_detalle, entrar_como_multirol_autor, id_de_articulo,
                         id_en_la_url, titulo_del_detalle)


def test_hu011_cp01_comite_abre_detalle(navegador, evidencia, datos_previos):
    """El comité abre el detalle desde «Artículos postulados»."""
    titulo = datos_previos['titulos']['ia']
    abrir_consulta_comite(navegador)
    texto = abrir_detalle(navegador, titulo)
    assert TITULO_MODAL in texto
    assert titulo_del_detalle(navegador) == titulo
    assert id_en_la_url(navegador) is not None
    evidencia('EXITO')


def test_hu011_cp02_informacion_completa(navegador, evidencia, datos_previos):
    """El detalle muestra conferencia, título, estado, línea, fecha, resumen y palabras clave,
    y coincide con lo que se registró."""
    abrir_consulta_comite(navegador)
    texto = abrir_detalle(navegador, datos_previos['titulos']['ia'])
    # Algunos rótulos se ven en mayúsculas por el estilo, por eso se compara sin mayúsculas
    for dato in ('Congreso de Pruebas - 2027', 'Registrado', 'Línea temática', 'Inteligencia artificial',
                 'Fecha de postulación', 'Resumen',
                 'Propuesta de prueba para validar el registro de artículos en el sistema.',
                 'Palabras clave', 'pruebas, selenium, calidad'):
        assert dato.lower() in texto.lower(), f'Falta «{dato}» en el detalle:\n{texto}'
    fecha = navegador.execute_script(
        "return new Date(arguments[0]).toLocaleDateString('es-CO', "
        "{ day: '2-digit', month: 'long', year: 'numeric' })", datos_previos['creado'])
    assert fecha in texto, f'Se esperaba la fecha {fecha}'
    evidencia('EXITO')


def test_hu011_cp03_autores(navegador, evidencia, datos_previos):
    """El detalle lista a todos los autores con su institución y correo."""
    identificador = datos_previos['id']
    abrir_consulta_comite(navegador)
    texto = abrir_detalle(navegador, datos_previos['titulos']['ia'])
    for dato in ('Autores', 'Autor Pruebas', 'autor@pruebas.co',
                 'Carlos Ramírez', 'Universidad Icesi', f'qa.coautor1.{identificador}@example.com',
                 'Ana Torres', 'Pontificia Universidad Javeriana Cali', f'qa.coautor2.{identificador}@example.com'):
        assert dato in texto, f'Falta «{dato}» en el detalle:\n{texto}'
    evidencia('EXITO')


def test_hu011_cp04_versiones_y_cesion(navegador, evidencia, datos_previos):
    """Sin PDF cargado, el detalle informa que no hay versiones ni documento de cesión."""
    abrir_consulta_comite(navegador)
    texto = abrir_detalle(navegador, datos_previos['titulos']['ia'])
    assert 'Versiones y documentos' in texto
    assert 'No hay versiones registradas para este artículo.' in texto
    assert 'Cesión de derechos' in texto
    assert 'No hay documento de cesión cargado.' in texto
    evidencia('EXITO')


def test_hu011_cp05_admin_consulta_cualquier_articulo(navegador, evidencia, datos_previos):
    """El administrador abre el detalle de un artículo de otra autora."""
    titulo = datos_previos['titulos']['bd']
    login(navegador, 'admin')
    clic_en_panel(navegador, 'Consultar artículos')
    esperar_listado(navegador)
    texto = abrir_detalle(navegador, titulo)
    assert titulo_del_detalle(navegador) == titulo
    assert 'María Fernanda López' in texto and 'Bases de datos' in texto
    evidencia('EXITO')


def test_hu011_cp06_autor_detalle_propio(navegador, evidencia, datos_previos):
    """El autor abre el detalle de su artículo desde «Mis artículos» (antes HU032-CP05)."""
    titulo = datos_previos['titulos']['ing1']
    abrir_mis_articulos(navegador, 'autor')
    texto = abrir_detalle(navegador, titulo)
    assert titulo_del_detalle(navegador) == titulo
    assert 'Ingeniería de software' in texto and 'Autor Pruebas' in texto
    evidencia('EXITO')


def test_hu011_cp07_autor_no_ve_articulo_ajeno(navegador, evidencia, datos_previos):
    """El autor escribe a mano la dirección del detalle de un artículo ajeno (antes HU032-CP06)."""
    id_ajeno = id_de_articulo(navegador, datos_previos['titulos']['bd'])
    navegador.execute_script('window.sessionStorage.clear(); window.localStorage.clear();')
    abrir_mis_articulos(navegador, 'autor')
    texto = abrir_detalle_por_url(navegador, '/autor/articulos', id_ajeno)
    assert ERROR_DETALLE in texto and MENSAJE_AJENO in texto, texto
    assert datos_previos['titulos']['bd'] not in texto
    assert 'María Fernanda López' not in texto
    evidencia('EXITO')


def test_hu011_cp08_articulo_inexistente(navegador, evidencia, datos_previos):
    """Un número de artículo que no existe muestra que no está disponible."""
    abrir_consulta_comite(navegador)
    texto = abrir_detalle_por_url(navegador, '/gestion/articulos', 999999)
    assert ERROR_DETALLE in texto and MENSAJE_NO_EXISTE in texto, texto
    evidencia('EXITO')


def test_hu011_cp09_cerrar_detalle(navegador, evidencia, datos_previos):
    """Al cerrar la ventana se vuelve al listado y la dirección ya no tiene el detalle."""
    abrir_consulta_comite(navegador)
    abrir_detalle(navegador, datos_previos['titulos']['ia'])
    cerrar_detalle(navegador)
    assert id_en_la_url(navegador) is None
    assert 'Artículos postulados' in body(navegador)
    evidencia('EXITO')


def test_hu011_cp10_multirol_como_autor(navegador, evidencia, datos_previos):
    """Una cuenta con roles administrador y autor entra como autor y pide el detalle de un artículo
    ajeno. Como trabaja con el rol autor, solo debería ver sus artículos."""
    id_ajeno = id_de_articulo(navegador, datos_previos['titulos']['bd'])
    navegador.execute_script('window.sessionStorage.clear(); window.localStorage.clear();')
    entrar_como_multirol_autor(navegador)
    clic_en_panel(navegador, 'Mis artículos')
    esperar_listado(navegador)
    texto = abrir_detalle_por_url(navegador, '/autor/articulos', id_ajeno)
    evidencia('RESULTADO')
    assert MENSAJE_AJENO in texto, (
        'Con el rol autor activo se mostró el detalle de un artículo ajeno:\n' + texto[:300])
