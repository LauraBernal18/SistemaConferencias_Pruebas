# HU-007 · Recuperar contraseña · casos HU007-CP01 a CP13 (matriz MT - HU007 del Drive)
# Pantalla: inicio de sesión → «¿Olvidaste tu contraseña?» → RecuperarContrasena.jsx
#   Paso 1: correo → «Enviar PIN al correo»
#   Paso 2: PIN de 6 dígitos + nueva contraseña + confirmación → «Guardar nueva contraseña»
#   Paso 3: «¡Listo!» con el mensaje del servidor
# El PIN y la contraseña nueva se envían juntos: el sistema no tiene un paso aparte
# solo para validar el PIN (CA-046 y CA-048 se comprueban con ese mismo envío).
#
# Cuidados:
# - El backend permite solo 3 solicitudes de PIN por hora desde el mismo equipo
#   (password_recovery_request = 3/hour). Por eso todas las pruebas comparten UN navegador
#   y UNA sola solicitud de PIN por ejecución.
# - Se usa una cuenta de autor nueva para no cambiar la contraseña de las cuentas fijas.
# - Para los casos que necesitan el PIN real (CP04, CP05, CP07, CP10, CP12 y CP13) hay que
#   leer el correo. Hay dos formas:
#     a) $env:SGC_CORREO_PIN = "tu_correo@gmail.com" y $env:SGC_PIN_MANUAL = "1", y correr pytest con -s:
#        la prueba usa ese correo y pide escribir el PIN que llegó.
#     b) Solo en el entorno local: SGC_PIN_LOG = archivo donde el backend imprime los correos (consola).
#   Sin ninguna de las dos, esos casos quedan Bloqueados (skip) con el motivo.

import os
import re
import time

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from sgc_helpers import PASSWORD, body, login, open_login
from sgc_articulos import id_unico
from sgc_sprint2 import cerrar_sesion
import sgc_api as api

MENSAJE_SOLICITUD = 'Si el correo está registrado, recibirás un PIN de recuperación.'
PIN_INVALIDO = 'El PIN no es válido o ha vencido. Solicita uno nuevo.'
NO_COINCIDEN = 'Las contraseñas no coinciden.'
EXITO = 'Tu contraseña se actualizó correctamente.'
NUEVA = 'NuevaClave2026!'


# ---------------------------------------------------------------------------
# Un solo navegador para todo el archivo (una sola solicitud de PIN)
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def _navegador_modulo():
    from conftest import service
    opciones = webdriver.ChromeOptions()
    opciones.add_argument('--start-maximized')
    if os.getenv('HEADLESS') == '1':
        for argumento in ('--headless=new', '--window-size=1366,900', '--no-sandbox', '--disable-dev-shm-usage'):
            opciones.add_argument(argumento)
    driver = webdriver.Chrome(service=service, options=opciones)
    driver.set_page_load_timeout(100)
    yield driver
    driver.quit()


@pytest.fixture
def navegador(_navegador_modulo):
    """Reemplaza el navegador de conftest.py solo en este archivo: todas las pruebas usan el mismo."""
    return _navegador_modulo


@pytest.fixture(scope='module')
def cuenta():
    """Cuenta en la que se recupera la contraseña."""
    manual = os.getenv('SGC_CORREO_PIN')
    identificador = id_unico()
    correo = manual or f'qa.recuperar.{identificador}@example.com'
    try:
        api.pedir('POST', '/auth/registro-autor/', datos={
            'first_name': 'Recuperar', 'last_name': f'Contraseña {identificador}', 'email': correo,
            'password': PASSWORD, 'institucion': 'Universidad del Valle'})
        creada = True
    except AssertionError:
        if not manual:
            raise
        creada = False  # el correo propio ya tenía cuenta: no se conoce su contraseña anterior
    return {'correo': correo, 'creada': creada, 'manual': bool(manual), 'pin': None}


def _pin_del_correo(cuenta):
    """Devuelve el PIN que llegó al correo de la cuenta, o deja el caso Bloqueado si no hay cómo leerlo."""
    if cuenta['pin']:
        return cuenta['pin']
    if cuenta['manual'] and os.getenv('SGC_PIN_MANUAL') == '1':
        cuenta['pin'] = input(f"\nEscribe el PIN que llegó a {cuenta['correo']}: ").strip()
        return cuenta['pin']
    archivo = os.getenv('SGC_PIN_LOG')
    if archivo and os.path.exists(archivo):
        texto = open(archivo, encoding='utf-8', errors='replace').read()
        bloques = [b for b in texto.split('Content-Type: text/plain') if cuenta['correo'] in b]
        encontrados = re.findall(r'Tu PIN de recuperación es (\d{6})', bloques[-1]) if bloques else []
        if encontrados:
            cuenta['pin'] = encontrados[-1]
            return cuenta['pin']
    pytest.skip('Bloqueado: no hay acceso al correo de la cuenta de prueba para leer el PIN '
                '(configurar SGC_CORREO_PIN y SGC_PIN_MANUAL, ver el encabezado del archivo).')


# ---------------------------------------------------------------------------
# Funciones de la pantalla
# ---------------------------------------------------------------------------

def _casillas_pin(navegador):
    return navegador.find_elements(By.CSS_SELECTOR, 'input[aria-label^="Dígito "]')


def _escribir_pin(navegador, pin):
    casillas = _casillas_pin(navegador)
    for casilla in casillas:
        casilla.send_keys('\b')
    casillas[0].click()
    casillas[0].send_keys(pin)
    time.sleep(0.4)


def _escribir_claves(navegador, clave, confirmacion=None):
    for id_campo, valor in (('nueva-contrasena', clave), ('confirmar-contrasena', confirmacion or clave)):
        campo = navegador.find_element(By.ID, id_campo)
        campo.clear()
        campo.send_keys(valor)


def _boton_guardar(navegador):
    return navegador.find_element(By.XPATH, '//button[@type="submit"][contains(normalize-space(), "Guardar nueva contraseña")]')


def _alerta(navegador):
    alertas = navegador.find_elements(By.CSS_SELECTOR, 'section[aria-labelledby="titulo-recuperacion"] [role="alert"]')
    return alertas[0].text if alertas else ''


def _esperar_alerta(navegador, texto, timeout=60):
    WebDriverWait(navegador, timeout).until(lambda d: texto in _alerta(d))


# ---------------------------------------------------------------------------
# Casos (se ejecutan en orden sobre el mismo navegador)
# ---------------------------------------------------------------------------

def test_hu007_cp01_acceso_a_recuperacion(navegador, evidencia, cuenta):
    """CA-042: desde el inicio de sesión se abre «Recupera tu acceso» con el campo de correo."""
    open_login(navegador)
    navegador.find_element(By.XPATH, '//button[contains(normalize-space(), "¿Olvidaste tu contraseña?")]').click()
    WebDriverWait(navegador, 20).until(EC.visibility_of_element_located((By.ID, 'correo-recuperacion')))
    texto = body(navegador)
    assert 'Recupera tu acceso' in texto and 'Enviar PIN al correo' in texto
    evidencia('EXITO')


def test_hu007_cp03_validacion_del_correo(navegador, evidencia, cuenta):
    """CA-043: sin correo o con un correo mal escrito no se puede enviar la solicitud."""
    campo = navegador.find_element(By.ID, 'correo-recuperacion')
    boton = navegador.find_element(By.XPATH, '//button[@type="submit"][contains(normalize-space(), "Enviar PIN")]')
    for valor in ('', 'qa.correo-sin-arroba'):
        campo.clear()
        if valor:
            campo.send_keys(valor)
        boton.click()
        time.sleep(1)
        mensaje = navegador.execute_script('return arguments[0].validationMessage', campo)
        assert mensaje, f'El navegador debía impedir el envío con «{valor}»'
        assert navegador.find_elements(By.ID, 'correo-recuperacion') and not _casillas_pin(navegador)
    evidencia('EXITO')


def test_hu007_cp02_solicitud_de_recuperacion(navegador, evidencia, cuenta):
    """CA-042 y CA-043: con el correo de una cuenta registrada se envía la solicitud y se pide el PIN."""
    campo = navegador.find_element(By.ID, 'correo-recuperacion')
    campo.clear()
    campo.send_keys(cuenta['correo'])
    navegador.find_element(By.XPATH, '//button[@type="submit"][contains(normalize-space(), "Enviar PIN")]').click()
    WebDriverWait(navegador, 90).until(lambda d: MENSAJE_SOLICITUD in body(d) or _alerta(d))
    assert MENSAJE_SOLICITUD in body(navegador), _alerta(navegador)
    assert len(_casillas_pin(navegador)) == 6
    evidencia('EXITO')


def test_hu007_cp06_ingreso_del_pin(navegador, evidencia, cuenta):
    """CA-045: el formulario recibe los 6 dígitos del PIN (y no acepta letras)."""
    _escribir_pin(navegador, '12a3456')
    valores = ''.join(c.get_attribute('value') for c in _casillas_pin(navegador))
    assert valores == '123456', valores
    evidencia('EXITO')


def test_hu007_cp09_sin_pin_completo_no_cambia(navegador, evidencia, cuenta):
    """CA-046 a CA-048: mientras el PIN no esté completo no se puede guardar la contraseña nueva."""
    _casillas_pin(navegador)[5].send_keys('\b')
    time.sleep(0.4)
    _escribir_claves(navegador, NUEVA)
    assert not _boton_guardar(navegador).is_enabled()
    evidencia('EXITO')


def test_hu007_cp11_contrasena_insegura(navegador, evidencia, cuenta):
    """CA-049: una contraseña que no cumple las reglas se rechaza con el motivo y no se cambia nada.
    También se revisa que la confirmación tenga que coincidir."""
    _escribir_pin(navegador, '000000')
    _escribir_claves(navegador, NUEVA, NUEVA + 'x')
    _boton_guardar(navegador).click()
    _esperar_alerta(navegador, NO_COINCIDEN)
    evidencia('NO_COINCIDEN')
    # Menos de 8 caracteres: el formulario no deja enviarla
    _escribir_claves(navegador, '12345')
    _boton_guardar(navegador).click()
    time.sleep(1)
    campo = navegador.find_element(By.ID, 'nueva-contrasena')
    assert navegador.execute_script('return arguments[0].validationMessage', campo)
    evidencia('CORTA')
    # 8 dígitos: pasa el formulario, pero el servidor la rechaza por insegura
    _escribir_claves(navegador, '12345678')
    _boton_guardar(navegador).click()
    WebDriverWait(navegador, 60).until(lambda d: 'contraseña' in _alerta(d).lower() and NO_COINCIDEN not in _alerta(d))
    motivo = _alerta(navegador)
    assert 'demasiado común' in motivo or 'completamente numérica' in motivo, motivo
    assert 'Recupera tu acceso' in body(navegador)
    evidencia('EXITO')


def test_hu007_cp08_pin_incorrecto(navegador, evidencia, cuenta):
    """CA-047: con un PIN distinto al enviado, el sistema lo informa y no cambia la contraseña."""
    _escribir_pin(navegador, '000000')
    _escribir_claves(navegador, NUEVA)
    _boton_guardar(navegador).click()
    _esperar_alerta(navegador, PIN_INVALIDO)
    assert 'Recupera tu acceso' in body(navegador)
    evidencia('EXITO')


def test_hu007_cp04_pin_enviado_al_correo(navegador, evidencia, cuenta):
    """CA-044: el sistema generó un PIN de 6 dígitos y lo envió al correo registrado de la cuenta."""
    pin = _pin_del_correo(cuenta)
    assert re.fullmatch(r'\d{6}', pin), pin
    evidencia('EXITO')


def test_hu007_cp05_pin_solo_de_su_cuenta(navegador, evidencia, cuenta):
    """CA-044 y CA-050: el PIN de esta cuenta no sirve para cambiar la contraseña de otra cuenta.
    Se intenta por la API con autor@pruebas.co (así no se pierde el paso del PIN en el navegador).
    En CP12 se comprueba además que las cuentas fijas siguen entrando con su contraseña."""
    pin = _pin_del_correo(cuenta)
    with pytest.raises(AssertionError) as rechazo:
        api.pedir('POST', '/auth/restablecer-contrasena/', datos={
            'email': 'autor@pruebas.co', 'pin': pin, 'password': NUEVA})
    assert 'El PIN no es válido o ha vencido' in str(rechazo.value), str(rechazo.value)
    evidencia('EXITO')


def test_hu007_cp07_cp10_cp13_pin_correcto_y_nueva_contrasena(navegador, evidencia, cuenta):
    """CA-046, CA-048, CA-049 y CA-051: con el PIN correcto y una contraseña válida se actualiza
    y el sistema confirma que la recuperación fue exitosa."""
    pin = _pin_del_correo(cuenta)
    if not _casillas_pin(navegador):
        pytest.skip('Bloqueado: se perdió el paso del PIN (no se pide otro para no superar el límite de 3 por hora).')
    _escribir_pin(navegador, pin)
    _escribir_claves(navegador, NUEVA)
    _boton_guardar(navegador).click()
    WebDriverWait(navegador, 60).until(lambda d: EXITO in body(d) or _alerta(d))
    assert EXITO in body(navegador) and '¡Listo!' in body(navegador), _alerta(navegador)
    evidencia('EXITO')


def test_hu007_cp12_contrasena_queda_en_su_cuenta(navegador, evidencia, cuenta):
    """CA-048 y CA-050: la cuenta entra con la contraseña nueva, ya no con la anterior,
    y las demás cuentas no cambian."""
    if not cuenta['pin']:
        pytest.skip('Bloqueado: depende de CP07 (no se pudo leer el PIN).')
    cerrar_sesion(navegador)
    login(navegador, cuenta['correo'], NUEVA)
    evidencia('NUEVA')
    if cuenta['creada']:
        cerrar_sesion(navegador)
        login(navegador, cuenta['correo'], PASSWORD, expected=False)
        WebDriverWait(navegador, 60).until(lambda d: 'Correo o contraseña incorrectos.' in body(d))
        evidencia('ANTERIOR_RECHAZADA')
    for fija in ('autor', 'comite'):
        cerrar_sesion(navegador)
        login(navegador, fija)
    evidencia('EXITO')
