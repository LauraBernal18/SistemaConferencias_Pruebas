"""HU-002 — Consultar usuarios. Sprint 2.

Requiere fixture 'navegador' de tests/conftest.py y selenium + pytest.
Las pruebas acceden a rutas internas haciendo clic en la interfaz React,
no mediante navegador.get('/gestion/usuarios').
"""
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = os.getenv('SGC_FRONTEND', 'https://conferencia-cientifica-ds1-git-develop-ds-6.vercel.app').rstrip('/')
PASSWORD = os.getenv('SGC_QA_PASSWORD', 'Prueba12345')
EMAILS = {
    'admin': 'admin@pruebas.co',
    'comite': 'comite@pruebas.co',
    'autor': 'autor@pruebas.co',
}

USUARIOS = {
    'admin@pruebas.co': {'nombre': 'Admin Pruebas', 'institucion': 'Univalle', 'roles': {'ADMIN'}},
    'comite@pruebas.co': {'nombre': 'Comité Pruebas', 'institucion': 'Univalle', 'roles': {'COMITE'}},
    'autor@pruebas.co': {'nombre': 'Autor Pruebas', 'institucion': 'Univalle', 'roles': {'AUTOR'}},
    'multirol@pruebas.co': {'nombre': 'Multirol Pruebas', 'institucion': 'Univalle', 'roles': {'ADMIN', 'AUTOR'}},
}


def entrar(navegador, rol):
    navegador.get(f'{BASE}/login')
    esperar = WebDriverWait(navegador, 90)
    email = esperar.until(EC.visibility_of_element_located((By.ID, 'correo')))
    email.send_keys(EMAILS[rol])
    navegador.find_element(By.ID, 'contrasena').send_keys(PASSWORD)
    captcha = esperar.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[role="checkbox"]')))
    if captcha.get_attribute('aria-checked') != 'true':
        captcha.click()
    esperar.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))).click()
    esperar.until(lambda d: '/login' not in d.current_url)
    esperar.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))


def abrir_listado(navegador, rol='admin'):
    entrar(navegador, rol)
    esperar = WebDriverWait(navegador, 90)
    # Navegación dentro de React: evita el 404 que puede producir la ruta SPA directa.
    def enlace_usuarios(d):
        enlaces = d.find_elements(By.XPATH, '//a[contains(@href,"/gestion/usuarios") and not(contains(@href,"/nuevo"))]')
        enlaces += d.find_elements(By.XPATH, '//button[contains(normalize-space(.), "Consultar usuarios")]')
        return next((e for e in enlaces if e.is_displayed() and e.is_enabled()), False)
    try:
        esperar.until(enlace_usuarios).click()
    except Exception as exc:
        raise AssertionError(
            f'No aparece una opción navegable para consultar usuarios desde el panel del rol {rol}. '
            f'URL: {navegador.current_url}; texto: {navegador.find_element(By.TAG_NAME, "body").text[:600]!r}'
        ) from exc
    esperar.until(EC.visibility_of_element_located((By.ID, 'titulo-listado-usuarios')))
    assert '/gestion/usuarios' in navegador.current_url, f'Ruta inesperada: {navegador.current_url}'
    assert navegador.find_element(By.ID, 'titulo-listado-usuarios').text.strip() == 'Listado de usuarios'

    # El encabezado se muestra antes de recibir los datos desde el backend.
    # Esperar a que desaparezca el estado de carga Y a que se renderice una
    # cuenta QA conocida; un listado vacío no debe darse por cargado.
    selector_listado = 'section[aria-labelledby="titulo-listado-usuarios"]'

    def usuarios_cargados(d):
        secciones = d.find_elements(By.CSS_SELECTOR, selector_listado)
        if not secciones:
            return False
        seccion = secciones[0]
        texto = seccion.text.lower()
        if 'cargando usuarios' in texto or 'cargando…' in texto or 'cargando...' in texto:
            return False
        if not seccion.find_elements(By.XPATH, './/p[normalize-space()="admin@pruebas.co"]'):
            return False
        return seccion

    try:
        return WebDriverWait(navegador, 120, poll_frequency=0.5).until(usuarios_cargados)
    except Exception as exc:
        estado = navegador.find_element(By.TAG_NAME, 'body').text[:800]
        raise AssertionError(
            'El listado no terminó de cargar los usuarios QA en 120 segundos. '
            f'URL: {navegador.current_url}. Contenido visible: {estado!r}'
        ) from exc


def fila_por_correo(listado, correo):
    """Obtiene la fila visual usando correo exacto (sin clases CSS generadas)."""
    xpath = './/p[normalize-space()="%s"]/ancestor::div[contains(concat(" ",normalize-space(@class)," ")," grid ")][1]' % correo
    filas = listado.find_elements(By.XPATH, xpath)
    assert filas, f'No se encontró una fila con el correo {correo}'
    return filas[0]


def datos_fila(fila):
    texto = fila.text
    roles = {
    t.text.strip().upper()
    for t in fila.find_elements(By.XPATH, './/span')
    if t.text.strip().upper() in {'ADMIN', 'COMITE', 'AUTOR'}
}
    return texto, roles
def test_hu002_cp01_administrador_consulta_usuarios(navegador):
    listado = abrir_listado(navegador, 'admin')
    assert listado.is_displayed()
    assert 'Listado de usuarios' in listado.text


def test_hu002_cp02_comite_consulta_usuarios(navegador):
    listado = abrir_listado(navegador, 'comite')
    assert listado.is_displayed()
    assert 'Listado de usuarios' in listado.text


def test_hu002_cp03_muestra_campos_de_usuarios(navegador):
    listado = abrir_listado(navegador)
    texto = listado.text
    for campo in ('Nombre', 'Correo electrónico', 'Institución', 'Roles'):
        assert campo.lower() in texto.lower(), f'No aparece el encabezado: {campo}'
    for correo, esperado in USUARIOS.items():
        fila = fila_por_correo(listado, correo)
        texto_fila, _ = datos_fila(fila)
        assert esperado['nombre'] in texto_fila
        assert correo in texto_fila
        assert esperado['institucion'] in texto_fila


def test_hu002_cp04_identifica_roles(navegador):
    listado = abrir_listado(navegador)
    for correo, esperado in USUARIOS.items():
        fila = fila_por_correo(listado, correo)
        _, roles = datos_fila(fila)
        assert roles == esperado['roles'], f'{correo}: se esperaban {esperado["roles"]}, se encontraron {roles}'


def test_hu002_cp05_datos_coinciden_con_registros_qa(navegador):
    """Contraste con cuentas QA conocidas; no constituye verificación directa de base de datos."""
    listado = abrir_listado(navegador)
    for correo, esperado in USUARIOS.items():
        texto_fila, roles = datos_fila(fila_por_correo(listado, correo))
        assert esperado['nombre'] in texto_fila
        assert correo in texto_fila
        assert esperado['institucion'] in texto_fila
        assert roles == esperado['roles']


def test_hu002_cp06_autor_no_accede_listado(navegador):
    """CA-012: el rol AUTOR no puede abrir el listado administrativo.

    A diferencia de los reportes históricos del Sprint 1, este caso se ejecuta.
    Un 404, un acceso autorizado por error o una navegación ambigua son fallos
    que se documentan, no motivos para aprobar artificialmente el escenario.
    """
    entrar(navegador, 'autor')
    espera = WebDriverWait(navegador, 30)

    # El panel de autor no debe ofrecer una entrada al listado administrativo.
    enlaces = navegador.find_elements(
        By.XPATH, '//a[contains(@href,"/gestion/usuarios") and not(contains(@href,"/nuevo"))]'
    )
    assert not any(e.is_displayed() for e in enlaces), (
        'El panel de autor muestra un enlace al listado administrativo de usuarios.'
    )

    # Intento directo: es la misma comprobación de acceso usada en HU-006/HU-030.
    navegador.get(f'{BASE}/gestion/usuarios')

    # Esperar a que la app decida el destino: puede redirigir asíncronamente.
    try:
        espera.until(lambda d: (
            '/gestion/usuarios' not in d.current_url
            or bool(d.find_elements(By.ID, 'titulo-listado-usuarios'))
            or '404' in d.title.lower()
            or '404' in d.find_element(By.TAG_NAME, 'body').text[:300].lower()
        ))
    except Exception:
        pass  # Se evalúa el estado final con aserciones claras abajo.

    url_final = navegador.current_url
    texto = navegador.find_element(By.TAG_NAME, 'body').text
    assert '404' not in navegador.title.lower() and not ('404' in texto[:300] and 'not found' in texto[:500].lower()), (
        f'La navegación al listado administrativo devolvió un 404. URL: {url_final}'
    )
    assert '/gestion/usuarios' not in url_final, (
        f'El usuario AUTOR permanece en la ruta administrativa: {url_final}'
    )
    assert '/autor' in url_final, (
        f'Se esperaba redirección al panel de autor. URL final: {url_final}'
    )
    assert not navegador.find_elements(By.ID, 'titulo-listado-usuarios'), (
        'Se mostró el listado de usuarios a pesar de iniciar sesión como AUTOR.'
    )
    assert 'admin@pruebas.co' not in texto.lower(), (
        'El usuario AUTOR pudo ver información del listado administrativo.'
    )


def test_hu002_cp07_no_expone_credenciales_en_interfaz(navegador):
    listado = abrir_listado(navegador)
    texto = listado.text.lower()
    for termino in ('contraseña', 'password', 'token', 'hash', 'secret', PASSWORD.lower()):
        assert termino not in texto, f'La interfaz presenta información potencialmente sensible: {termino}'
    # Los datos públicos del listado sí deben estar visibles.
    assert 'admin@pruebas.co' in texto


def test_hu002_cp08_solo_usuarios_habilitados(navegador):
    """Comprueba que la cuenta QA deshabilitada no figure entre las cuentas consultables."""
    listado = abrir_listado(navegador)
    correos_visibles = {
        e.text.strip().lower()
        for e in listado.find_elements(By.CSS_SELECTOR, 'p')
        if '@' in e.text
    }
    assert 'admin@pruebas.co' in correos_visibles, (
        'No aparece la cuenta habilitada de referencia admin@pruebas.co en el listado.'
    )
    assert 'deshabilitado@pruebas.co' not in correos_visibles, (
        'El listado incluye deshabilitado@pruebas.co, una cuenta que debe estar deshabilitada.'
    )


# CA-010 (filtros) y CA-011 (sin coincidencias) se verifican en HU-003;
# no se duplican como pruebas independientes de HU-002.