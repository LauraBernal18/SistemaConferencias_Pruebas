
import os

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# HU-030: Configurar fechas y líneas temáticas

URL = os.getenv(
    "TEST_FRONTEND_URL",
    "https://conferencia-cientifica-ds1-git-develop-ds-6.vercel.app"
)
CLAVE = os.getenv("TEST_PASSWORD", "Prueba12345")

USUARIOS = {
    "admin": "admin@pruebas.co",
    "comite": "comite@pruebas.co",
    "autor": "autor@pruebas.co"
}


@pytest.fixture
def navegador():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()


def iniciar_sesion(driver, correo):
    driver.get(f"{URL}/login")
    espera = WebDriverWait(driver, 30)

    espera.until(
        EC.visibility_of_element_located((By.ID, "correo"))
    ).send_keys(correo)

    driver.find_element(
        By.ID, "contrasena"
    ).send_keys(CLAVE)

    captcha = driver.find_element(
        By.CSS_SELECTOR, '[role="checkbox"]'
    )
    captcha.click()

    espera.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[type="submit"]')
        )
    ).click()

    # Espera ampliada por Render.
    WebDriverWait(driver, 90).until(
        lambda d: "Cerrar sesión" in
        d.find_element(By.TAG_NAME, "body").text
    )


def abrir_configuracion(driver):
    driver.get(f"{URL}/configuracion-conferencia")

    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located(
            (By.ID, "conferencia-configuracion")
        )
    )


# CP01: Acceso de administrador y comité

@pytest.mark.parametrize(
    "rol", ["admin", "comite"]
)
def test_hu030_cp01_acceso_autorizado(navegador, rol):
    iniciar_sesion(navegador, USUARIOS[rol])
    abrir_configuracion(navegador)

    contenido = navegador.find_element(
        By.TAG_NAME, "body"
    ).text

    assert "Configuración de conferencia" in contenido
    assert "Fechas límite" in contenido
    assert "Líneas temáticas" in contenido


# CP02: Guardar fechas límite

@pytest.mark.skip(
    reason="Pendiente: requiere conferencia QA para guardar fechas."
)
def test_hu030_cp02_guardar_fechas():
    pass


# CP03: Fecha inválida

@pytest.mark.skip(
    reason="Pendiente: verificar validación sin afectar fechas compartidas."
)
def test_hu030_cp03_fecha_invalida():
    pass


# CP04: Secuencia cronológica incorrecta

@pytest.mark.skip(
    reason="Pendiente: requiere prueba controlada de guardado."
)
def test_hu030_cp04_orden_fechas():
    pass


# CP05: Crear, editar y desactivar línea temática

@pytest.mark.skip(
    reason="Pendiente: requiere datos de prueba aislados y limpieza."
)
def test_hu030_cp05_gestionar_lineas():
    pass


# CP06: Consultar líneas temáticas

def test_hu030_cp06_consultar_lineas(navegador):
    iniciar_sesion(navegador, USUARIOS["admin"])
    abrir_configuracion(navegador)

    selector = navegador.find_element(
        By.ID, "conferencia-configuracion"
    )

    assert "Congreso de Pruebas" in selector.text

    nombres = [
        "Bases de datos",
        "Ciberseguridad",
        "Ingeniería de software",
        "Inteligencia artificial"
    ]

    for nombre in nombres:
        linea = WebDriverWait(navegador, 30).until(
            EC.visibility_of_element_located((
                By.XPATH,
                f"//article[.//h3[normalize-space()='{nombre}']]"
            ))
        )

        assert "Habilitada" in linea.text


# CP07: Configuración independiente

@pytest.mark.skip(
    reason="Pendiente: el entorno solo tiene una conferencia."
)
def test_hu030_cp07_configuraciones_independientes():
    pass


# CP08: Modificar sin afectar otra conferencia

@pytest.mark.skip(
    reason="Pendiente: requiere dos conferencias de prueba."
)
def test_hu030_cp08_modificacion_independiente():
    pass


# CP09: Restricciones según fechas

@pytest.mark.skip(
    reason="Pendiente: requiere pruebas controladas de plazos."
)
def test_hu030_cp09_restricciones_por_fechas():
    pass


# CP10: Autor sin permiso

def test_hu030_cp10_acceso_no_autorizado(navegador):
    iniciar_sesion(navegador, USUARIOS["autor"])

    navegador.get(f"{URL}/configuracion-conferencia")

    # Esperar a que se resuelva la navegación.
    WebDriverWait(navegador, 30).until(
        lambda d: (
            "/configuracion-conferencia" not in d.current_url
            or "Acceso denegado" in
            d.find_element(By.TAG_NAME, "body").text
            or "No autorizado" in
            d.find_element(By.TAG_NAME, "body").text
            or d.find_elements(
                By.ID, "conferencia-configuracion"
            )
        )
    )

    # No debe poder utilizar el formulario de configuración.
    assert not any(
        boton.is_displayed() and boton.is_enabled()
        for boton in navegador.find_elements(
            By.XPATH,
            "//button[normalize-space()='Guardar fechas límite'"
            " or normalize-space()='Agregar línea temática']"
        )
    )


# CP11: Confirmación del guardado

@pytest.mark.skip(
    reason="Pendiente: confirmar mensaje y entorno de escritura seguro."
)
def test_hu030_cp11_guardado_exitoso():
    pass


# CP12: Mensajes de error de fechas

@pytest.mark.skip(
    reason="Pendiente: verificar mensaje exacto y validación."
)
def test_hu030_cp12_errores_configuracion():
    pass
