"""HU-003 — Filtrar usuarios (Sprint 2).

Usa las fixtures `navegador` y `evidencia` de tests/conftest.py.
Los controles de filtro se identifican con aria-label (HTML aportado).
No modifica registros ni roles; usa cuentas QA conocidas.
"""
import os
import unicodedata

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = os.getenv('SGC_FRONTEND', 'https://conferencia-cientifica-ds1-git-develop-ds-6.vercel.app').rstrip('/')
PASSWORD = os.getenv('SGC_QA_PASSWORD', 'Prueba12345')
EMAILS = {'admin': 'admin@pruebas.co', 'comite': 'comite@pruebas.co'}

LISTADO = 'section[aria-labelledby="titulo-listado-usuarios"]'
NOMBRE = 'input[aria-label="Filtrar usuarios por nombre"]'
ROL = 'select[aria-label="Filtrar usuarios por rol"]'
BOTON_LIMPIAR = '//button[normalize-space()="Limpiar filtros"]'
CORREOS_QA = {
    'admin@pruebas.co',
    'comite@pruebas.co',
    'autor@pruebas.co',
    'multirol@pruebas.co',
}


def normalizar(valor):
    return ''.join(
        c for c in unicodedata.normalize('NFD', valor.casefold())
        if unicodedata.category(c) != 'Mn'
    )


def entrar(d, rol='admin'):
    d.get(f'{BASE}/login')
    espera = WebDriverWait(d, 90)
    espera.until(EC.visibility_of_element_located((By.ID, 'correo'))).send_keys(EMAILS[rol])
    d.find_element(By.ID, 'contrasena').send_keys(PASSWORD)
    captcha = espera.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[role="checkbox"]')))
    if captcha.get_attribute('aria-checked') != 'true':
        captcha.click()
    espera.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))).click()
    espera.until(lambda x: '/login' not in x.current_url)


def estado_listado(d):
    """Lee el listado en una sola operación del navegador.

    React puede reemplazar las filas mientras se aplican los filtros.
    Obtener todos los datos de una vez evita referencias Selenium obsoletas.
    """
    return d.execute_script("""
        const seccion = document.querySelector(arguments[0]);
        if (!seccion) return null;
        const contenedor = seccion.querySelector(':scope > div:last-child');
        const elementos = contenedor
            ? [...contenedor.children].filter(el => el.classList.contains('grid'))
            : [];
        const filas = elementos.map(el => {
            const parrafos = [...el.querySelectorAll('p')];
            const spans = [...el.querySelectorAll('span')];
            return {
                nombre: (parrafos[0]?.innerText || '').trim(),
                correos: parrafos.map(p => (p.innerText || '').trim().toLowerCase())
                    .filter(texto => texto.includes('@')),
                roles: spans.map(sp => (sp.innerText || '').trim().toUpperCase())
                    .filter(texto => ['ADMIN', 'COMITE', 'AUTOR'].includes(texto))
            };
        });
        return {texto: seccion.innerText || '', filas};
    """, LISTADO)


def obtener_correos(d):
    estado = estado_listado(d)
    return {correo for fila in estado['filas'] for correo in fila['correos']} if estado else set()


def cargando(d):
    estado = estado_listado(d)
    return estado is None or 'cargando usuarios' in normalizar(estado['texto'])


def abrir_listado(d, rol='admin'):
    entrar(d, rol)
    espera = WebDriverWait(d, 90)

    def opcion_consultar(driver):
        enlaces = driver.find_elements(
            By.XPATH,
            '//a[contains(@href,"/gestion/usuarios") and not(contains(@href,"/nuevo"))]'
        )
        enlaces += driver.find_elements(
            By.XPATH, '//button[contains(normalize-space(.), "Consultar usuarios")]'
        )
        return next((e for e in enlaces if e.is_displayed() and e.is_enabled()), False)
    espera.until(opcion_consultar).click()
    espera.until(EC.visibility_of_element_located((By.ID, 'titulo-listado-usuarios')))
    assert '/gestion/usuarios' in d.current_url, f'Ruta inesperada: {d.current_url}'
    espera.until(EC.visibility_of_element_located((By.CSS_SELECTOR, NOMBRE)))
    espera.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ROL)))

    # El título y los filtros se renderizan antes de los datos del backend.
    try:
        WebDriverWait(d, 120, poll_frequency=0.5).until(
            lambda driver: (lambda estado: estado is not None and
                'cargando usuarios' not in normalizar(estado['texto']) and
                CORREOS_QA.issubset({correo for fila in estado['filas'] for correo in fila['correos']}))
                (estado_listado(driver))
        )
    except Exception as exc:
        texto = d.find_element(By.CSS_SELECTOR, LISTADO).text[:900]
        raise AssertionError(f'No terminó de cargar el listado QA en 120 s: {texto!r}') from exc
    return d.find_element(By.CSS_SELECTOR, LISTADO)


def campo_nombre(d):
    return d.find_element(By.CSS_SELECTOR, NOMBRE)


def selector_rol(d):
    return Select(d.find_element(By.CSS_SELECTOR, ROL))


def aplicar_nombre(d, valor):
    campo = campo_nombre(d)
    campo.clear()
    campo.send_keys(valor)
    assert campo.get_attribute('value') == valor


def aplicar_rol(d, valor):
    selector_rol(d).select_by_value(valor)
    assert selector_rol(d).first_selected_option.get_attribute('value') == valor


def esperar_coincidencias(d, obligatorios=(), nombre=None, rol=None, ausentes=(), timeout=45):
    """Comprueba todas las filas usando una instantánea estable del DOM."""
    obligatorios = set(obligatorios)
    ausentes = set(ausentes)

    def correcto(driver):
        estado = estado_listado(driver)
        if estado is None or 'cargando usuarios' in normalizar(estado['texto']):
            return False
        rows = estado['filas']
        if not rows:
            return False
        emails = {correo for fila in rows for correo in fila['correos']}
        if not obligatorios.issubset(emails) or ausentes.intersection(emails):
            return False
        for fila in rows:
            if nombre is not None and normalizar(nombre) not in normalizar(fila['nombre']):
                return False
            if rol is not None and rol not in fila['roles']:
                return False
        return rows

    try:
        return WebDriverWait(d, timeout, poll_frequency=0.35).until(correcto)
    except Exception as exc:
        estado = estado_listado(d) or {'texto': '(sin listado)', 'filas': []}
        visibles = {correo for fila in estado['filas'] for correo in fila['correos']}
        raise AssertionError(
            f'Los resultados no cumplen los filtros. Nombre={nombre!r}, rol={rol!r}, '
            f'obligatorios={obligatorios!r}, ausentes={ausentes!r}. '
            f'Correos visibles: {visibles!r}. '
            f'Texto listado: {estado["texto"][:800]!r}'
        ) from exc

MENSAJES_SIN_RESULTADOS = (
    'no se encontraron', 'no hay usuarios', 'no hay resultados',
    'sin resultados', 'ningun usuario', 'ninguna coincidencia',
    'no existen usuarios', 'no hay coincidencias',
    'no encontramos usuarios', 'no encontramos resultados',
)


def esperar_sin_resultados(d, timeout=45):
    """Exige lista vacía y mensaje explícito, leídos de forma atómica."""
    def sin_resultados(driver):
        estado = estado_listado(driver)
        if estado is None or 'cargando usuarios' in normalizar(estado['texto']):
            return False
        if estado['filas']:
            return False
        texto = normalizar(estado['texto'])
        return any(m in texto for m in MENSAJES_SIN_RESULTADOS)

    try:
        WebDriverWait(d, timeout, poll_frequency=0.35).until(sin_resultados)
    except Exception as exc:
        estado = estado_listado(d) or {'texto': '(sin listado)', 'filas': []}
        visibles = {correo for fila in estado['filas'] for correo in fila['correos']}
        raise AssertionError(
            'No apareció un mensaje de sin resultados con el listado vacío. '
            f'Correos: {visibles!r}. Texto: {estado["texto"][:900]!r}'
        ) from exc


def test_hu003_cp01_controles_visibles(navegador, evidencia):
    abrir_listado(navegador)
    assert campo_nombre(navegador).is_displayed()
    assert navegador.find_element(By.CSS_SELECTOR, ROL).is_displayed()
    opciones = {op.get_attribute('value') for op in selector_rol(navegador).options}
    assert {'', 'ADMIN', 'COMITE', 'AUTOR'}.issubset(opciones)
    boton = navegador.find_element(By.XPATH, BOTON_LIMPIAR)
    assert boton.is_displayed()
    assert not boton.is_enabled(), 'Limpiar filtros debería iniciar deshabilitado sin filtros activos.'
    evidencia('EXITO')


def test_hu003_cp02_filtrar_por_nombre(navegador, evidencia):
    abrir_listado(navegador)
    aplicar_nombre(navegador, 'Admin')
    esperar_coincidencias(navegador, {'admin@pruebas.co'}, nombre='Admin',
                         ausentes={'autor@pruebas.co', 'comite@pruebas.co', 'multirol@pruebas.co'})
    evidencia('EXITO')


def test_hu003_cp03_filtrar_por_nombre_parcial(navegador, evidencia):
    abrir_listado(navegador)
    aplicar_nombre(navegador, 'Multi')
    esperar_coincidencias(navegador, {'multirol@pruebas.co'}, nombre='Multi',
                         ausentes={'admin@pruebas.co', 'comite@pruebas.co', 'autor@pruebas.co'})
    evidencia('EXITO')


def test_hu003_cp04_filtrar_rol_admin(navegador, evidencia):
    abrir_listado(navegador)
    aplicar_rol(navegador, 'ADMIN')
    esperar_coincidencias(navegador,
                         {'admin@pruebas.co', 'multirol@pruebas.co'}, rol='ADMIN',
                         ausentes={'autor@pruebas.co', 'comite@pruebas.co'})
    evidencia('EXITO')


def test_hu003_cp05_filtrar_rol_comite(navegador, evidencia):
    abrir_listado(navegador)
    aplicar_rol(navegador, 'COMITE')
    esperar_coincidencias(navegador, {'comite@pruebas.co'}, rol='COMITE',
                         ausentes={'admin@pruebas.co', 'autor@pruebas.co', 'multirol@pruebas.co'})
    evidencia('EXITO')


def test_hu003_cp06_filtrar_rol_autor(navegador, evidencia):
    abrir_listado(navegador)
    aplicar_rol(navegador, 'AUTOR')
    esperar_coincidencias(navegador,
                         {'autor@pruebas.co', 'multirol@pruebas.co'}, rol='AUTOR',
                         ausentes={'admin@pruebas.co', 'comite@pruebas.co'})
    evidencia('EXITO')

def test_hu003_cp07_combinar_filtros_con_coincidencia(navegador, evidencia):
    abrir_listado(navegador)
    aplicar_nombre(navegador, 'Multirol')
    aplicar_rol(navegador, 'AUTOR')
    esperar_coincidencias(navegador, {'multirol@pruebas.co'}, nombre='Multirol', rol='AUTOR',
                         ausentes={'admin@pruebas.co', 'autor@pruebas.co', 'comite@pruebas.co'})
    evidencia('EXITO')


def test_hu003_cp08_combinar_sin_coincidencias(navegador, evidencia):
    abrir_listado(navegador)
    aplicar_nombre(navegador, 'Admin')
    aplicar_rol(navegador, 'COMITE')
    esperar_sin_resultados(navegador)
    evidencia('EXITO')


def test_hu003_cp09_nombre_inexistente(navegador, evidencia):
    abrir_listado(navegador)
    aplicar_nombre(navegador, 'UsuarioInexistenteQA98765')
    esperar_sin_resultados(navegador)
    evidencia('EXITO')


def test_hu003_cp10_limpiar_filtros(navegador, evidencia):
    abrir_listado(navegador)
    aplicar_nombre(navegador, 'Multirol')
    aplicar_rol(navegador, 'AUTOR')
    esperar_coincidencias(navegador, {'multirol@pruebas.co'}, nombre='Multirol', rol='AUTOR')
    boton = WebDriverWait(navegador, 15).until(
        EC.element_to_be_clickable((By.XPATH, BOTON_LIMPIAR))
    )
    boton.click()
    WebDriverWait(navegador, 15).until(
        lambda d: campo_nombre(d).get_attribute('value') == ''
        and selector_rol(d).first_selected_option.get_attribute('value') == ''
    )
    esperar_coincidencias(navegador, CORREOS_QA)
    assert not navegador.find_element(By.XPATH, BOTON_LIMPIAR).is_enabled()
    evidencia('EXITO')


def test_hu003_cp11_no_muestra_deshabilitados(navegador, evidencia):
    abrir_listado(navegador)
    aplicar_nombre(navegador, 'deshabilitado')
    esperar_sin_resultados(navegador)
    assert 'deshabilitado@pruebas.co' not in obtener_correos(navegador)
    evidencia('EXITO')


def test_hu003_cp12_comite_puede_filtrar(navegador, evidencia):
    abrir_listado(navegador, rol='comite')
    aplicar_rol(navegador, 'AUTOR')
    esperar_coincidencias(navegador,
                         {'autor@pruebas.co', 'multirol@pruebas.co'}, rol='AUTOR',
                         ausentes={'admin@pruebas.co', 'comite@pruebas.co'})
    evidencia('EXITO')
