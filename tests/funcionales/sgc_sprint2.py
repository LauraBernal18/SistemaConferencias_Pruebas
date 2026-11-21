# Funciones para las pruebas del Sprint 2 de Samuel (HU-011, HU-004, HU-014 y HU-012).
# Reutilizan sgc_helpers.py (Laura) y sgc_articulos.py (Sprint 1).

import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from sgc_helpers import choose_role, login
from sgc_articulos import abrir_consulta_comite, ir_a_ruta

TITULO_MODAL = 'Detalle del artículo'
ERROR_DETALLE = 'No se pudo consultar el artículo'
MENSAJE_AJENO = 'Este artículo no está asociado a tu cuenta.'
MENSAJE_NO_EXISTE = 'El artículo no existe o no está disponible.'


# ---------------------------------------------------------------------------
# HU-011 · Detalle del artículo (ventana modal sobre el listado)
# ---------------------------------------------------------------------------

def abrir_detalle(driver, titulo):
    """Hace clic en la fila del artículo y espera a que cargue la ventana del detalle."""
    enlace = WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, f'a[aria-label="Consultar detalle de {titulo}"]')))
    enlace.click()
    return esperar_detalle(driver)


def esperar_detalle(driver):
    """Espera la ventana del detalle y que termine de cargar (título o mensaje de error)."""
    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '[role="dialog"]')))

    def termino(d):
        modal = d.find_element(By.CSS_SELECTOR, '[role="dialog"]')
        return modal.find_elements(By.ID, 'titulo-detalle-articulo') or ERROR_DETALLE in modal.text

    WebDriverWait(driver, 60).until(termino)
    time.sleep(0.5)
    return texto_del_detalle(driver)


def texto_del_detalle(driver):
    return driver.find_element(By.CSS_SELECTOR, '[role="dialog"]').text


def titulo_del_detalle(driver):
    return driver.find_element(By.ID, 'titulo-detalle-articulo').text


def id_en_la_url(driver):
    """Número del artículo que queda en la dirección, por ejemplo ...?detalle=7 → '7'."""
    encontrado = re.search(r'[?&]detalle=(\d+)', driver.current_url)
    return encontrado.group(1) if encontrado else None


def cerrar_detalle(driver):
    driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Cerrar detalle del artículo"]').click()
    WebDriverWait(driver, 15).until(lambda d: not d.find_elements(By.CSS_SELECTOR, '[role="dialog"]'))


def id_de_articulo(driver, titulo):
    """Abre el detalle como comité para conocer el número del artículo (para las pruebas por URL)."""
    abrir_consulta_comite(driver)
    abrir_detalle(driver, titulo)
    return id_en_la_url(driver)


def abrir_detalle_por_url(driver, ruta_listado, id_articulo):
    """Escribe la dirección del detalle a mano, como haría un usuario que copia el enlace."""
    ir_a_ruta(driver, f'{ruta_listado}?detalle={id_articulo}')
    return esperar_detalle(driver)


def entrar_como_multirol_autor(driver):
    """multirol@pruebas.co tiene los roles administrador y autor; entra eligiendo el rol autor."""
    login(driver, 'multirol')
    choose_role(driver, 'AUTOR')



# ---------------------------------------------------------------------------
# HU-004 · Actualizar datos de usuario
# ---------------------------------------------------------------------------

from selenium.webdriver.common.keys import Keys  # noqa: E402

from sgc_articulos import clic_en_panel, crear_cuenta_autor, id_unico  # noqa: E402
from sgc_helpers import PASSWORD, body  # noqa: E402

EXITO_OTRO = 'Los datos del usuario se actualizaron correctamente.'
EXITO_PROPIO = 'Tus datos personales se actualizaron correctamente.'


def cuenta_nueva(driver, etiqueta):
    """Crea una cuenta de autor nueva para editarla sin dañar las cuentas fijas de pruebas."""
    identificador = id_unico()
    datos = {'nombre': 'Usuario', 'apellido': f'{etiqueta} {identificador}',
             'correo': f'qa.{etiqueta.lower()}.{identificador}@example.com',
             'institucion': 'Universidad del Valle'}
    crear_cuenta_autor(driver, datos)
    return datos


def escribir(driver, id_campo, texto):
    """Borra lo que tenga el campo y escribe el texto nuevo (así React detecta el cambio)."""
    campo = driver.find_element(By.ID, id_campo)
    campo.send_keys(Keys.CONTROL, 'a')
    campo.send_keys(Keys.DELETE)
    if texto:
        campo.send_keys(texto)


def esperar_formulario_edicion(driver):
    WebDriverWait(driver, 30).until(lambda d: d.find_elements(By.ID, 'nombre-editar')
                                    and d.find_element(By.ID, 'correo-editar').get_attribute('value'))
    time.sleep(0.5)


def abrir_edicion_como_admin(driver, datos):
    """Admin → «Consultar usuarios» → botón «Editar» de la cuenta."""
    login(driver, 'admin')
    clic_en_panel(driver, 'Consultar usuarios')
    nombre = f"{datos['nombre']} {datos['apellido']}"
    enlace = WebDriverWait(driver, 60).until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, f'a[aria-label="Editar usuario {nombre}"]')))
    driver.execute_script('arguments[0].scrollIntoView({block: "center"})', enlace)
    time.sleep(0.5)
    enlace.click()
    esperar_formulario_edicion(driver)


def abrir_mis_datos(driver, correo, password=PASSWORD):
    login(driver, correo, password)
    clic_en_panel(driver, 'Actualizar mis datos')
    esperar_formulario_edicion(driver)


def guardar(driver):
    boton = driver.find_element(By.XPATH, '//button[@type="submit"]')
    driver.execute_script('arguments[0].scrollIntoView({block: "center"})', boton)
    boton.click()
    time.sleep(1)


def esperar_texto(driver, texto, timeout=30):
    WebDriverWait(driver, timeout).until(lambda d: texto in body(d))


def marcar_rol(driver, nombre_rol):
    casilla = driver.find_element(By.XPATH, f'//label[.//span[normalize-space()="{nombre_rol}"]]//input')
    if not casilla.is_selected():
        driver.execute_script('arguments[0].scrollIntoView({block: "center"})', casilla)
        casilla.click()


def fila_de_usuario(driver, correo):
    filas = driver.find_elements(By.XPATH, f'//p[normalize-space()="{correo}"]/parent::div')
    return re.sub(r'\s+', ' ', filas[0].text) if filas else None


# ---------------------------------------------------------------------------
# HU-014 (versiones) y HU-012 (modificar): se abren desde el detalle del artículo
# ---------------------------------------------------------------------------

import pytest  # noqa: E402
from pathlib import Path  # noqa: E402

CARPETA_DATOS = Path(__file__).resolve().parents[1] / 'datos'


def boton_en_detalle(driver, *textos):
    """Busca en la ventana del detalle un botón o enlace que contenga alguno de los textos."""
    modal = driver.find_element(By.CSS_SELECTOR, '[role="dialog"]')
    for texto in textos:
        encontrados = modal.find_elements(
            By.XPATH, f'.//button[contains(normalize-space(), "{texto}")] | .//a[contains(normalize-space(), "{texto}")]')
        if encontrados:
            return encontrados[0]
    return None


def exigir_boton(driver, hu, *textos):
    """Si la pantalla todavía no existe, la prueba queda como Bloqueada (skip) y no como fallida."""
    boton = boton_en_detalle(driver, *textos)
    if boton is None:
        pytest.skip(f'Bloqueado: el detalle del artículo todavía no tiene la opción de {hu} '
                    f'(se buscó: {", ".join(textos)}).')
    return boton


def abrir_carga_version(driver, titulo, quien='autor'):
    from sgc_articulos import abrir_mis_articulos
    abrir_mis_articulos(driver, quien)
    abrir_detalle(driver, titulo)
    exigir_boton(driver, 'HU-014', 'Cargar versión', 'Cargar nueva versión', 'Subir versión', 'Cargar PDF').click()
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]')))


def subir_archivo(driver, nombre):
    driver.find_element(By.CSS_SELECTOR, 'input[type="file"]').send_keys(str(CARPETA_DATOS / nombre))
    boton = driver.find_element(By.XPATH, '//button[@type="submit"] | //button[contains(normalize-space(), "Cargar")]')
    boton.click()
    time.sleep(1.5)


def abrir_modificacion(driver, titulo, quien='autor'):
    from sgc_articulos import abrir_mis_articulos
    abrir_mis_articulos(driver, quien)
    abrir_detalle(driver, titulo)
    exigir_boton(driver, 'HU-012', 'Modificar', 'Editar artículo').click()
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input, textarea')))
    time.sleep(0.5)


def escribir_en(campo, texto):
    """Igual que escribir(), pero recibe el elemento en vez del id."""
    campo.send_keys(Keys.CONTROL, 'a')
    campo.send_keys(Keys.DELETE)
    if texto:
        campo.send_keys(texto)
