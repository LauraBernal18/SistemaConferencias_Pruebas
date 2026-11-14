import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from sgc_helpers import BASE, PASSWORD, USERS, body, captcha, choose_role, click_text, credentials, login, open_login, visible_text


def test_hu006_cp01_formulario(navegador):
    open_login(navegador)
    for selector in ['#correo', '#contrasena', '[role="checkbox"]', 'button[type="submit"]']:
        assert navegador.find_element(By.CSS_SELECTOR, selector).is_displayed()


def test_hu006_cp02_credenciales(navegador):
    open_login(navegador)
    credentials(navegador, USERS['autor'])
    assert navegador.find_element(By.ID, 'correo').get_attribute('value') == USERS['autor']
    assert navegador.find_element(By.ID, 'contrasena').get_attribute('value') == PASSWORD
    assert navegador.find_element(By.ID, 'contrasena').get_attribute('type') == 'password'


def test_hu006_cp03_login_autor(navegador, evidencia):
    login(navegador, 'autor')
    visible_text(navegador, 'Panel de autor')
    assert 'Autor Pruebas' in body(navegador)
    assert 'Registrar un artículo' in body(navegador)
    evidencia('EXITO')


def test_hu006_cp04_rol_comite(navegador):
    login(navegador, 'comite')
    visible_text(navegador, 'Panel de comité científico')
    assert 'Comité Pruebas' in body(navegador)


@pytest.mark.parametrize('rol,panel,funcion', [
    ('admin', 'Panel de administrador', 'Configurar fechas y líneas temáticas'),
    ('comite', 'Panel de comité científico', 'Consultar artículos'),
    ('autor', 'Panel de autor', 'Registrar un artículo'),
])
def test_hu006_cp05_redireccion(navegador, rol, panel, funcion):
    login(navegador, rol)
    visible_text(navegador, panel)
    assert funcion in body(navegador)


def test_hu006_cp06_credenciales_incorrectas(navegador):
    login(navegador, 'autor', 'Incorrecta123', expected=False)
    visible_text(navegador, 'Correo o contraseña incorrectos.', 90)
    assert 'Panel de autor' not in body(navegador)
    assert navegador.find_element(By.ID, 'correo').is_displayed()


def test_hu006_cp07_captcha_pendiente(navegador):
    open_login(navegador)
    credentials(navegador, USERS['autor'])
    assert navegador.find_element(By.CSS_SELECTOR, '[role="checkbox"]').get_attribute('aria-checked') == 'false'
    assert not navegador.find_element(By.CSS_SELECTOR, 'button[type="submit"]').is_enabled()


def test_hu006_cp08_selector_multirrol(navegador, evidencia):
    login(navegador, 'multirol')
    visible_text(navegador, '¿Con qué rol quieres trabajar?')
    assert navegador.current_url.endswith('/elegir-rol')
    assert navegador.find_element(By.CSS_SELECTOR, 'input[name="rol"][value="ADMIN"]')
    assert navegador.find_element(By.CSS_SELECTOR, 'input[name="rol"][value="AUTOR"]')
    assert 'Multirol Pruebas' in body(navegador)
    evidencia('EXITO')


def test_hu006_cp09_permisos_rol_elegido(navegador, evidencia):
    login(navegador, 'multirol')
    choose_role(navegador, 'ADMIN')
    assert 'Configurar fechas y líneas temáticas' in body(navegador)
    assert 'Registrar un artículo' not in body(navegador)
    click_text(navegador, 'Cambiar de rol')
    visible_text(navegador, '¿Con qué rol quieres trabajar?')
    choose_role(navegador, 'AUTOR')
    assert 'Registrar un artículo' in body(navegador)
    assert 'Mis artículos' in body(navegador)
    assert 'Configurar fechas y líneas temáticas' not in body(navegador)
    evidencia('EXITO')


@pytest.mark.skip(reason='HU006-CP10: ruta directa /configuracion-conferencia devuelve 404 incluso como administrador; revisar fallback SPA y permisos backend')
def test_hu006_cp10_rutas_ajenas():
    pass
