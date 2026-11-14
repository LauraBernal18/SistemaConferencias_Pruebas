# HU-001 · Crear usuario · casos del diseño HU001-CP01 a CP12
# Pantalla: Panel → «Crear usuario» (/gestion/usuarios/nuevo), solo Administrador y Comité.
# Las cuentas creadas usan correos únicos (ID) y NO se borran después.

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from sgc_helpers import PASSWORD, body, login, visible_text
from sgc_articulos import anotar_id, cambiar_usuario, clic_en_panel, id_unico, ir_a_ruta

ID = id_unico()
anotar_id('HU-001', ID)

ROL_ADMIN = 'Administrador del sistema'
ROL_COMITE = 'Miembro del comité científico'
ROL_AUTOR = 'Autor'


def abrir_crear_usuario(navegador, quien):
    login(navegador, quien)
    clic_en_panel(navegador, 'Crear usuario')
    WebDriverWait(navegador, 30).until(EC.visibility_of_element_located((By.ID, 'nombre-usuario')))


def roles_ofrecidos(navegador):
    etiquetas = navegador.find_elements(By.XPATH, '//section[@aria-labelledby="roles-usuario"]//label')
    return [etiqueta.text.strip() for etiqueta in etiquetas]


def llenar_usuario(navegador, nombre, apellido, correo, institucion, roles, contrasena=PASSWORD):
    campos = {
        'nombre-usuario': nombre,
        'apellido-usuario': apellido,
        'correo-usuario': correo,
        'institucion-usuario': institucion,
        'contrasena-usuario-input': contrasena,
        'confirmar-contrasena-usuario': contrasena,
    }
    for id_campo, valor in campos.items():
        campo = navegador.find_element(By.ID, id_campo)
        campo.clear()
        if valor:
            campo.send_keys(valor)
    for rol in roles:
        navegador.find_element(
            By.XPATH, f'//section[@aria-labelledby="roles-usuario"]//label[normalize-space()="{rol}"]').click()


def enviar_usuario(navegador):
    boton = navegador.find_element(By.XPATH, '//button[@type="submit" and contains(., "Crear usuario")]')
    navegador.execute_script("arguments[0].scrollIntoView({block: 'center'})", boton)
    boton.click()


def mensaje_exito(nombre, apellido, correo, rol):
    return f'La cuenta de {nombre} {apellido} ({correo}) se creó correctamente con el rol: {rol}.'


def crear_y_verificar(navegador, quien, nombre, apellido, correo, institucion, rol):
    abrir_crear_usuario(navegador, quien)
    llenar_usuario(navegador, nombre, apellido, correo, institucion, [rol])
    enviar_usuario(navegador)
    visible_text(navegador, mensaje_exito(nombre, apellido, correo, rol), 90)


def test_hu001_cp01_admin_abre_formulario(navegador, evidencia):
    abrir_crear_usuario(navegador, 'admin')
    assert 'Datos de la nueva cuenta' in body(navegador)
    assert roles_ofrecidos(navegador) == [ROL_ADMIN, ROL_COMITE, ROL_AUTOR]
    evidencia('EXITO')


def test_hu001_cp02_comite_abre_formulario(navegador, evidencia):
    abrir_crear_usuario(navegador, 'comite')
    assert 'Datos de la nueva cuenta' in body(navegador)
    assert roles_ofrecidos(navegador) == [ROL_COMITE, ROL_AUTOR]
    evidencia('EXITO')


def test_hu001_cp03_autor_sin_acceso(navegador, evidencia):
    login(navegador, 'autor')
    assert 'Crear usuario' not in [e.text for e in navegador.find_elements(By.TAG_NAME, 'a')]
    ir_a_ruta(navegador, '/gestion/usuarios/nuevo')
    assert navegador.current_url.endswith('/autor'), navegador.current_url
    assert not navegador.find_elements(By.ID, 'nombre-usuario')
    evidencia('EXITO')


def test_hu001_cp04_admin_crea_administrador(navegador, evidencia):
    correo = f'qa.admin.{ID}@example.com'
    crear_y_verificar(navegador, 'admin', 'Andrea', 'Gómez', correo, 'Universidad del Valle', ROL_ADMIN)
    evidencia('EXITO')
    # La cuenta nueva entra al Panel de administrador
    cambiar_usuario(navegador, correo)
    visible_text(navegador, 'Panel de administrador', 90)
    evidencia('INGRESO')


def test_hu001_cp05_admin_crea_comite(navegador, evidencia):
    correo = f'qa.comite.{ID}@example.com'
    crear_y_verificar(navegador, 'admin', 'Carlos', 'Ruiz', correo, 'Universidad del Valle', ROL_COMITE)
    evidencia('EXITO')


def test_hu001_cp06_admin_crea_autor(navegador, evidencia):
    correo = f'qa.autor.admin.{ID}@example.com'
    crear_y_verificar(navegador, 'admin', 'Diana', 'Pérez', correo, 'Universidad Icesi', ROL_AUTOR)
    evidencia('EXITO')
    cambiar_usuario(navegador, correo)
    visible_text(navegador, 'Panel de autor', 90)
    evidencia('INGRESO')


def test_hu001_cp07_comite_crea_comite(navegador, evidencia):
    correo = f'qa.comite2.{ID}@example.com'
    crear_y_verificar(navegador, 'comite', 'Esteban', 'Mora', correo, 'Universidad del Valle', ROL_COMITE)
    evidencia('EXITO')


def test_hu001_cp08_comite_crea_autor(navegador, evidencia):
    correo = f'qa.autor.comite.{ID}@example.com'
    crear_y_verificar(navegador, 'comite', 'Felipe', 'Castro', correo, 'Universidad Javeriana Cali', ROL_AUTOR)
    evidencia('EXITO')


def test_hu001_cp09_comite_no_puede_crear_administrador(navegador, evidencia):
    """En la pantalla del comité no aparece el rol Administrador (el backend también lo rechaza)."""
    abrir_crear_usuario(navegador, 'comite')
    assert ROL_ADMIN not in roles_ofrecidos(navegador)
    assert 'Administrador' not in ' '.join(roles_ofrecidos(navegador))
    evidencia('EXITO')


def test_hu001_cp10_apellido_vacio(navegador, evidencia):
    abrir_crear_usuario(navegador, 'admin')
    llenar_usuario(navegador, 'Diana', '', f'qa.vacio.{ID}@example.com', 'Universidad Icesi', [ROL_AUTOR])
    enviar_usuario(navegador)
    visible_text(navegador, 'Revisa los campos indicados antes de crear el usuario.', 15)
    assert 'Ingresa el apellido.' in body(navegador)
    evidencia('EXITO')


def test_hu001_cp11_correo_invalido(navegador, evidencia):
    abrir_crear_usuario(navegador, 'admin')
    llenar_usuario(navegador, 'Diana', 'Pérez', f'qa.autor.{ID}@example', 'Universidad Icesi', [ROL_AUTOR])
    enviar_usuario(navegador)
    visible_text(navegador, 'Revisa los campos indicados antes de crear el usuario.', 15)
    assert 'Ingresa un correo electrónico válido, sin espacios.' in body(navegador)
    evidencia('EXITO')


def test_hu001_cp12_mensaje_exito(navegador, evidencia):
    correo = f'qa.exito.{ID}@example.com'
    crear_y_verificar(navegador, 'admin', 'Hugo', 'León', correo, 'Universidad del Valle', ROL_AUTOR)
    # El formulario queda limpio para crear otra cuenta
    assert navegador.find_element(By.ID, 'correo-usuario').get_attribute('value') == ''
    evidencia('EXITO')
