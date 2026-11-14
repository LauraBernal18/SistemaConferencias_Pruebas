import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

BASE = os.getenv('SGC_URL', 'https://conferencia-cientifica-ds1-git-develop-ds-6.vercel.app').rstrip('/')
PASSWORD = os.getenv('SGC_TEST_PASSWORD', 'Prueba12345')
USERS = {
    'admin': 'admin@pruebas.co',
    'comite': 'comite@pruebas.co',
    'autor': 'autor@pruebas.co',
    'multirol': 'multirol@pruebas.co',
}


def body(driver):
    return driver.find_element(By.TAG_NAME, 'body').text


def visible_text(driver, value, timeout=90):
    WebDriverWait(driver, timeout).until(lambda d: value in body(d))
    return body(driver)


def open_login(driver):
    # Ruta interna puede dar 404 en recarga directa en Vercel: iniciar desde raíz
    driver.get(BASE)
    try:
        WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, 'correo')))
    except Exception:
        driver.get(BASE + '/login')
        WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, 'correo')))


def credentials(driver, email, password=PASSWORD):
    email_box = driver.find_element(By.ID, 'correo')
    password_box = driver.find_element(By.ID, 'contrasena')
    email_box.clear(); email_box.send_keys(email)
    password_box.clear(); password_box.send_keys(password)


def captcha(driver):
    toggle = driver.find_element(By.CSS_SELECTOR, '[role="checkbox"]')
    if toggle.get_attribute('aria-checked') != 'true':
        toggle.click()
    WebDriverWait(driver, 10).until(lambda d: d.find_element(By.CSS_SELECTOR, '[role="checkbox"]').get_attribute('aria-checked') == 'true')


def login(driver, who='admin', password=PASSWORD, expected=True):
    open_login(driver)
    credentials(driver, USERS.get(who, who), password)
    captcha(driver)
    WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))).click()
    if expected:
        WebDriverWait(driver, 90).until(lambda d: 'Cerrar sesión' in body(d) or '¿Con qué rol quieres trabajar?' in body(d))


def choose_role(driver, role):
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, f'input[name="rol"][value="{role}"]')))
    input_el = driver.find_element(By.CSS_SELECTOR, f'input[name="rol"][value="{role}"]')
    # input sr-only dentro del label: clicar label para evento React
    input_el.find_element(By.XPATH, './ancestor::label').click()
    WebDriverWait(driver, 10).until(lambda d: d.find_element(By.CSS_SELECTOR, f'input[name="rol"][value="{role}"]').is_selected())
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    visible_text(driver, 'Panel de ' + ('administrador' if role == 'ADMIN' else 'autor'))


def click_text(driver, text, timeout=20):
    el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, f'//button[normalize-space()="{text}"] | //a[normalize-space()="{text}"]')))
    el.click()


def react_value(driver, element, value):
    # Setter nativo provoca evento input detectable por React; no se depende del formato visual MM/DD.
    driver.execute_script('''
        const el=arguments[0], v=arguments[1];
        const proto=el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto,'value').set.call(el,v);
        el.dispatchEvent(new Event('input',{bubbles:true}));
        el.dispatchEvent(new Event('change',{bubbles:true}));
    ''', element, value)
    assert element.get_attribute('value') == value
