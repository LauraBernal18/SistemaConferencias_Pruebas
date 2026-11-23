# Funciones para las pruebas de HU-001, HU-008, HU-009, HU-010 y HU-032 (Samuel).
# Usan las funciones de sgc_helpers.py (login, body, click_text...) que hizo Laura.

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from sgc_helpers import BASE, PASSWORD, body, click_text, login, visible_text

ROOT = Path(__file__).resolve().parents[2]

# Archivo donde se guardan los artículos y cuentas que se crean para HU-009, HU-010 y HU-032
ARCHIVO_DATOS = ROOT / 'datos_generados.json'

CONGRESO = 'Congreso de Pruebas · 2027'
QA = 'Conferencia de Pruebas QA · 2027'
LINEAS_CONGRESO = ['Inteligencia artificial', 'Ingeniería de software', 'Bases de datos', 'Ciberseguridad']
# Líneas del enunciado que usa el entorno de pruebas desde el 22/11 (commit 4ce89e8)
LINEAS_CONGRESO_ENUNCIADO = ['Sistemas Inteligentes', 'Tecnologías en Informática', 'Educación en Informática',
                             'Sistemas de Software', 'Software en la práctica']
RESUMEN = 'Propuesta de prueba para validar el registro de artículos en el sistema.'
PALABRAS = 'pruebas, selenium, calidad'
SIN_RESULTADOS = 'No se encontraron artículos con esos filtros'


def id_unico():
    """Fecha y hora, por ejemplo 20261114-093015. Así los títulos y correos nunca se repiten."""
    return datetime.now().strftime('%Y%m%d-%H%M%S')


def anotar_id(hu, identificador):
    """Anota el ID de la corrida en reportes/ids_usados.txt (sirve para la columna «Datos Usados»)."""
    carpeta = ROOT / 'reportes'
    carpeta.mkdir(exist_ok=True)
    with open(carpeta / 'ids_usados.txt', 'a', encoding='utf-8') as archivo:
        archivo.write(f'{datetime.now():%Y-%m-%d %H:%M}  {hu}  ID_UNICO={identificador}\n')


# ---------------------------------------------------------------------------
# Sesión y navegación
# ---------------------------------------------------------------------------

def cambiar_usuario(driver, quien):
    """Cierra la sesión actual (borra el sessionStorage) e inicia sesión con otra cuenta."""
    driver.get(BASE)
    driver.execute_script('window.sessionStorage.clear(); window.localStorage.clear();')
    login(driver, quien)


def ir_a_ruta(driver, ruta):
    """Cambia de pantalla dentro de la aplicación (como si el usuario escribiera la ruta),
    sin recargar la página."""
    driver.execute_script(
        "window.history.pushState({}, '', arguments[0]); window.dispatchEvent(new PopStateEvent('popstate'));",
        ruta)
    time.sleep(1.5)


def clic_en_panel(driver, texto):
    """Clic en un enlace del panel. El panel tiene una animación de entrada,
    por eso se espera un segundo antes del clic."""
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.XPATH, f'//a[normalize-space()="{texto}"]')))
    time.sleep(1)
    click_text(driver, texto)


# El 22/11 el entorno de pruebas cambió a las líneas temáticas del enunciado (commit 4ce89e8, SDGC-195).
# Las pruebas del Sprint 1 se diseñaron y ejecutaron con las líneas anteriores, así que si la línea
# pedida ya no existe se usa su equivalente nueva (misma descripción en preparar_entorno_pruebas.py).
LINEAS_EQUIVALENTES = {
    'Ingeniería de software': 'Sistemas de Software',
    'Inteligencia artificial': 'Sistemas Inteligentes',
    'Bases de datos': 'Tecnologías en Informática',
}


def contiene_linea(texto, linea):
    """True si el texto muestra la línea temática o su equivalente después del 22/11."""
    texto = texto.upper()
    return linea.upper() in texto or LINEAS_EQUIVALENTES.get(linea, linea).upper() in texto


def elegir_opcion(driver, id_select, texto_parcial):
    """Elige en un <select> la opción cuyo texto contiene texto_parcial y devuelve el texto elegido."""
    lista = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, id_select)))
    opciones = lista.find_elements(By.XPATH, f'.//option[contains(., "{texto_parcial}")]')
    if not opciones and texto_parcial in LINEAS_EQUIVALENTES:
        opciones = lista.find_elements(By.XPATH, f'.//option[contains(., "{LINEAS_EQUIVALENTES[texto_parcial]}")]')
    if not opciones:
        raise AssertionError(f'No existe la opción «{texto_parcial}» en {id_select}')
    opciones[0].click()
    time.sleep(0.8)
    return opciones[0].text.strip()


def textos_de_opciones(driver, id_select):
    lista = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, id_select)))
    return [opcion.text.strip() for opcion in lista.find_elements(By.TAG_NAME, 'option')]


def texto_del_titulo(driver):
    return WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.TAG_NAME, 'h1'))).text


# ---------------------------------------------------------------------------
# Artículos (HU-008)
# ---------------------------------------------------------------------------

def abrir_formulario_articulo(driver):
    """Desde la sesión del autor, abre «Registrar un artículo» y espera las convocatorias."""
    ir_a_ruta(driver, '/autor')
    clic_en_panel(driver, 'Registrar un artículo')
    WebDriverWait(driver, 90).until(EC.visibility_of_element_located((By.ID, 'titulo-articulo')))
    WebDriverWait(driver, 90).until(lambda d: len(textos_de_opciones(d, 'linea-tematica')) > 0)


def llenar_articulo(driver, titulo='', resumen='', palabras_clave='', linea=None,
                    coautores=None, responsable=None):
    """Llena el formulario sin enviarlo.
    coautores: lista de diccionarios con nombres, apellidos, email e institucion.
    responsable: 0 = quien registra, 1 = primer coautor, 2 = segundo coautor."""
    elegir_opcion(driver, 'convocatoria', 'Congreso de Pruebas')
    if linea:
        elegir_opcion(driver, 'linea-tematica', linea)

    for id_campo, valor in (('titulo-articulo', titulo), ('resumen-articulo', resumen),
                            ('palabras-clave', palabras_clave)):
        campo = driver.find_element(By.ID, id_campo)
        campo.clear()
        if valor:
            campo.send_keys(valor)

    for numero, coautor in enumerate(coautores or [], start=1):
        driver.find_element(By.XPATH, '//button[contains(., "Agregar autor")]').click()
        time.sleep(0.4)
        for campo in ('nombres', 'apellidos', 'email', 'institucion'):
            driver.find_element(By.NAME, f'autores.{numero}.{campo}').send_keys(coautor[campo])

    if responsable is not None:
        radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
        driver.execute_script('arguments[0].click()', radios[responsable])


def enviar_articulo(driver):
    boton = driver.find_element(By.XPATH, '//button[@type="submit" and contains(., "Registrar propuesta")]')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", boton)
    time.sleep(0.5)
    boton.click()


def mensaje_registro(titulo):
    return f'El artículo "{titulo}" se registró correctamente.'


def registrar_articulo(driver, **datos):
    """Abre el formulario, lo llena, lo envía y espera el mensaje de éxito."""
    abrir_formulario_articulo(driver)
    llenar_articulo(driver, **datos)
    enviar_articulo(driver)
    visible_text(driver, mensaje_registro(datos['titulo']), 90)
    return mensaje_registro(datos['titulo'])


def coautores_de_prueba(identificador):
    return [
        {'nombres': 'Carlos', 'apellidos': 'Ramírez', 'email': f'qa.coautor1.{identificador}@example.com',
         'institucion': 'Universidad Icesi'},
        {'nombres': 'Ana', 'apellidos': 'Torres', 'email': f'qa.coautor2.{identificador}@example.com',
         'institucion': 'Pontificia Universidad Javeriana Cali'},
    ]


# ---------------------------------------------------------------------------
# Listados (HU-009, HU-010 y HU-032)
# ---------------------------------------------------------------------------

def esperar_listado(driver):
    """Espera a que el listado cargue: filas o un mensaje de vacío."""
    time.sleep(0.8)

    def cargo(d):
        # Hasta el 21/11 el título iba en <span title>; desde el commit d771167 (SDGC-192)
        # va en el enlace «Consultar detalle de …». Se aceptan las dos formas.
        if d.find_elements(By.CSS_SELECTOR, 'span[title], a[aria-label^="Consultar detalle de "]'):
            return True
        texto = body(d)
        return (SIN_RESULTADOS in texto or 'No hay artículos registrados' in texto
                or 'Todavía no tienes artículos registrados' in texto)

    WebDriverWait(driver, 90).until(cargo)


def xpath_titulo(titulo):
    """Elemento con el título del artículo en el listado (forma anterior y actual de la interfaz)."""
    return f'(//span[@title="{titulo}"] | //a[@aria-label="Consultar detalle de {titulo}"])'


def fila_de_articulo(driver, titulo):
    """Texto de la fila del artículo, o None si no aparece."""
    filas = driver.find_elements(
        By.XPATH, f'{xpath_titulo(titulo)}/ancestor::div[contains(@class,"grid")][1]')
    if not filas:
        return None
    return re.sub(r'\s+', ' ', filas[0].text)


def visibles(driver, titulos):
    """Dice cuáles de los artículos preparados se ven: {'ing1': True, 'bd': False, ...}"""
    return {clave: fila_de_articulo(driver, titulo) is not None for clave, titulo in titulos.items()}


def abrir_consulta_comite(driver):
    login(driver, 'comite')
    clic_en_panel(driver, 'Consultar artículos')
    esperar_listado(driver)


def abrir_mis_articulos(driver, quien='autor'):
    login(driver, quien)
    clic_en_panel(driver, 'Mis artículos')
    esperar_listado(driver)


def filtrar(driver, linea, estado):
    elegir_opcion(driver, 'filtro-linea', linea)
    esperar_listado(driver)
    elegir_opcion(driver, 'filtro-estado', estado)
    esperar_listado(driver)


def encabezado_del_listado(driver):
    return driver.find_element(By.XPATH, '//span[normalize-space()="Título"]/parent::div').text.upper()


# ---------------------------------------------------------------------------
# Cuentas
# ---------------------------------------------------------------------------

def crear_cuenta_autor(driver, datos):
    """Crea una cuenta desde «Regístrate como autor» (HU-031)."""
    driver.get(BASE)
    driver.execute_script('window.sessionStorage.clear(); window.localStorage.clear();')
    driver.get(BASE)
    clic_en_panel(driver, 'Regístrate como autor')
    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.NAME, 'nombre'))).send_keys(datos['nombre'])
    driver.find_element(By.NAME, 'apellido').send_keys(datos['apellido'])
    driver.find_element(By.NAME, 'correo').send_keys(datos['correo'])
    driver.find_element(By.NAME, 'institucion').send_keys(datos['institucion'])
    driver.find_element(By.NAME, 'contrasena').send_keys(PASSWORD)
    driver.find_element(By.NAME, 'confirmarContrasena').send_keys(PASSWORD)
    driver.find_element(By.XPATH, '//button[@type="submit"]').click()
    visible_text(driver, '¡Tu cuenta ha sido creada correctamente!', 90)


# ---------------------------------------------------------------------------
# Datos previos para HU-009, HU-010 y HU-032 (como init-testing-data.js del taller)
# ---------------------------------------------------------------------------

def crear_datos_previos(driver):
    """Crea 2 cuentas de autor y 4 artículos con títulos únicos, y los guarda en datos_generados.json."""
    identificador = id_unico()
    datos = {
        'id': identificador,
        'base': BASE,
        'creado': datetime.now().isoformat(timespec='seconds'),
        'autora2': {'nombre': 'María Fernanda', 'apellido': 'López',
                    'correo': f'qa.autor.{identificador}@example.com', 'institucion': 'Universidad del Valle'},
        'sin_articulos': {'nombre': 'Juan', 'apellido': 'Pérez',
                          'correo': f'qa.autor2.{identificador}@example.com', 'institucion': 'Universidad Icesi'},
        'titulos': {
            'ing1': f'QA HU008 {identificador} – Pruebas automatizadas en aplicaciones web',
            'ing2': f'QA HU008 {identificador} – Resultado',
            'ia': f'QA HU008 {identificador} – Varios autores',
            'bd': f'QA HU009 {identificador} – Modelado de datos',
        },
    }
    titulos = datos['titulos']

    crear_cuenta_autor(driver, datos['autora2'])
    crear_cuenta_autor(driver, datos['sin_articulos'])

    cambiar_usuario(driver, 'autor')
    registrar_articulo(driver, titulo=titulos['ing1'], resumen=RESUMEN, palabras_clave=PALABRAS,
                       linea='Ingeniería de software')
    registrar_articulo(driver, titulo=titulos['ing2'], resumen=RESUMEN, palabras_clave=PALABRAS,
                       linea='Ingeniería de software')
    registrar_articulo(driver, titulo=titulos['ia'], resumen=RESUMEN, palabras_clave=PALABRAS,
                       linea='Inteligencia artificial', coautores=coautores_de_prueba(identificador),
                       responsable=1)

    cambiar_usuario(driver, datos['autora2']['correo'])
    registrar_articulo(driver, titulo=titulos['bd'], resumen='Propuesta de prueba sobre modelado de datos.',
                       palabras_clave='bases de datos, modelado', linea='Bases de datos')

    with open(ARCHIVO_DATOS, 'w', encoding='utf-8') as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
    anotar_id('Datos previos HU-009/010/032', identificador)
    return datos


def datos_siguen_en_el_sistema(driver, datos):
    """Revisa que la cuenta y el artículo de María Fernanda sigan existiendo.
    Si la base de datos de pruebas se reinició (por ejemplo, con un nuevo despliegue en Render),
    ya no existen y hay que crearlos otra vez."""
    try:
        cambiar_usuario(driver, datos['autora2']['correo'])
        clic_en_panel(driver, 'Mis artículos')
        esperar_listado(driver)
        return fila_de_articulo(driver, datos['titulos']['bd']) is not None
    except Exception:
        return False


# Se guardan aquí para no crearlos otra vez en el mismo pytest (HU-009, HU-010 y HU-032 los comparten)
_datos_de_esta_corrida = None


@pytest.fixture(scope='session')
def datos_previos():
    """Devuelve los artículos y cuentas de prueba.
    Si existe datos_generados.json del mismo entorno y esos datos siguen en el sistema, los reutiliza.
    Si no (o si se pide con $env:SGC_NUEVOS_DATOS="1"), los crea de nuevo."""
    global _datos_de_esta_corrida
    if _datos_de_esta_corrida:
        return _datos_de_esta_corrida

    # Navegador propio solo para revisar o preparar los datos
    from conftest import service  # el mismo chromedriver que usa conftest.py
    from selenium import webdriver
    opciones = webdriver.ChromeOptions()
    opciones.add_argument('--start-maximized')
    if os.getenv('HEADLESS') == '1':
        opciones.add_argument('--headless=new')
        opciones.add_argument('--window-size=1366,900')
        opciones.add_argument('--no-sandbox')
        opciones.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=opciones)
    try:
        if ARCHIVO_DATOS.exists() and os.getenv('SGC_NUEVOS_DATOS') != '1':
            with open(ARCHIVO_DATOS, encoding='utf-8') as archivo:
                datos = json.load(archivo)
            if datos.get('base') == BASE and datos_siguen_en_el_sistema(driver, datos):
                _datos_de_esta_corrida = datos
                return datos
            print('Los datos de datos_generados.json ya no están en el sistema: se crean otra vez.')
        _datos_de_esta_corrida = crear_datos_previos(driver)
        return _datos_de_esta_corrida
    finally:
        driver.quit()
