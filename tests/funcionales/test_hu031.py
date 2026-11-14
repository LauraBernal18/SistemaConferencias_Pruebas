import uuid
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sgc_helpers import BASE, PASSWORD, body, login, open_login, visible_text


def new_email():
    return f'qa.autor.{uuid.uuid4().hex[:12]}@example.com'


def open_registration(d):
    # Usar enlace interno para evitar 404 en recarga profunda de SPA
    open_login(d)
    WebDriverWait(d, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="/registro-autor"]'))).click()
    WebDriverWait(d, 30).until(EC.visibility_of_element_located((By.NAME, 'nombre')))


def fill(d, correo=None, **changes):
    data = dict(nombre='María Fernanda', apellido='López', correo=correo or new_email(),
                institucion='Universidad del Valle', contrasena=PASSWORD, confirmarContrasena=PASSWORD)
    data.update(changes)
    for name, value in data.items():
        item = d.find_element(By.NAME, name)
        item.clear()
        if value:
            item.send_keys(value)
    return data


def submit(d):
    d.find_element(By.XPATH, '//button[@type="submit" and normalize-space()="Crear cuenta de autor"]').click()


def success(d):
    visible_text(d, '¡Tu cuenta ha sido creada correctamente!', 90)
    assert 'Ya puedes iniciar sesión como autor con el correo que registraste.' in body(d)
    assert 'Ir a iniciar sesión' in body(d)


def test_hu031_cp01_acceso_registro(navegador):
    open_registration(navegador)
    assert 'Información del autor' in body(navegador)
    for field in ['nombre', 'apellido', 'correo', 'institucion', 'contrasena', 'confirmarContrasena']:
        assert navegador.find_element(By.NAME, field).is_displayed()


def test_hu031_cp02_ingresar_campos(navegador):
    open_registration(navegador)
    data = fill(navegador)
    for field, value in data.items():
        assert navegador.find_element(By.NAME, field).get_attribute('value') == value
    for field in ('contrasena', 'confirmarContrasena'):
        assert navegador.find_element(By.NAME, field).get_attribute('type') == 'password'


def test_hu031_cp03_institucion_vacia(navegador):
    open_registration(navegador)
    fill(navegador, institucion='')
    submit(navegador)
    visible_text(navegador, 'Ingresa tu institución')
    assert '¡Tu cuenta ha sido creada correctamente!' not in body(navegador)


def test_hu031_cp04_correo_invalido(navegador):
    open_registration(navegador)
    fill(navegador, correo='correo-invalido')
    submit(navegador)
    visible_text(navegador, 'Ingresa un correo electrónico válido.')
    assert '¡Tu cuenta ha sido creada correctamente!' not in body(navegador)


def test_hu031_cp05_registro_nuevo(navegador, evidencia):
    open_registration(navegador)
    email = new_email()
    fill(navegador, correo=email)
    submit(navegador)
    success(navegador)
    evidencia('EXITO_REGISTRO')
    # Hacer clic en enlace interno de confirmación evita 404 al entrar por URL directa
    WebDriverWait(navegador, 20).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Ir a iniciar sesión'))).click()
    WebDriverWait(navegador, 30).until(EC.visibility_of_element_located((By.ID, 'correo')))
    navegador.find_element(By.ID, 'correo').send_keys(email)
    navegador.find_element(By.ID, 'contrasena').send_keys(PASSWORD)
    navegador.find_element(By.CSS_SELECTOR, '[role="checkbox"]').click()
    WebDriverWait(navegador, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))).click()
    visible_text(navegador, 'Panel de autor', 90)


def test_hu031_cp06_correo_duplicado(navegador):
    open_registration(navegador)
    fill(navegador, correo='autor@pruebas.co')
    submit(navegador)
    visible_text(navegador, 'Ya existe una cuenta con este correo', 90)
    assert '¡Tu cuenta ha sido creada correctamente!' not in body(navegador)


@pytest.mark.skip(reason='HU031-CP07: requiere prueba técnica de API con envío de rol manipulado y verificación autorizada del backend')
def test_hu031_cp07_rol_privilegiado():
    pass


@pytest.mark.skip(reason='HU031-CP08: verificar hash seguro en backend/BD con acceso autorizado; no demostrable mediante Selenium')
def test_hu031_cp08_hash():
    pass


def test_hu031_cp09_mensaje_registro_exitoso(navegador, evidencia):
    open_registration(navegador)
    fill(navegador)
    submit(navegador)
    success(navegador)
    evidencia('EXITO')


def test_hu031_cp10_contrasenas_distintas(navegador):
    open_registration(navegador)
    fill(navegador, confirmarContrasena='Diferente123')
    submit(navegador)
    visible_text(navegador, 'Las contraseñas no coinciden.')
    assert '¡Tu cuenta ha sido creada correctamente!' not in body(navegador)
