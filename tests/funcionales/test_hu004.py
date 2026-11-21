# HU-004 · Actualizar datos de usuario · casos HU004-CP01 a CP10
# Cada prueba crea su propia cuenta de autor para no cambiar las cuentas fijas (admin, comite, autor...).

from selenium.webdriver.common.by import By

from sgc_helpers import BASE, body, login
from sgc_articulos import cambiar_usuario, clic_en_panel, ir_a_ruta
from sgc_sprint2 import (EXITO_OTRO, EXITO_PROPIO, abrir_edicion_como_admin, abrir_mis_datos, cuenta_nueva,
                         escribir, esperar_formulario_edicion, esperar_texto, fila_de_usuario, guardar,
                         marcar_rol)

NUEVA_CLAVE = 'Conferencia#2026'


def test_hu004_cp01_admin_actualiza_datos(navegador, evidencia):
    """El administrador cambia el nombre y la institución de otra cuenta."""
    datos = cuenta_nueva(navegador, 'HU004A')
    abrir_edicion_como_admin(navegador, datos)
    assert 'Editar usuario' in body(navegador)
    escribir(navegador, 'nombre-editar', 'Usuaria Editada')
    escribir(navegador, 'institucion-editar', 'Universidad Icesi')
    guardar(navegador)
    esperar_texto(navegador, EXITO_OTRO)
    evidencia('EXITO')
    # El listado muestra los datos nuevos
    clic_en_panel(navegador, 'Volver')
    esperar_texto(navegador, datos['correo'], 60)
    fila = fila_de_usuario(navegador, datos['correo'])
    assert 'Usuaria Editada' in fila and 'Universidad Icesi' in fila, fila


def test_hu004_cp02_admin_cambia_roles(navegador, evidencia):
    """El administrador le agrega el rol de comité a una cuenta de autor."""
    datos = cuenta_nueva(navegador, 'HU004B')
    abrir_edicion_como_admin(navegador, datos)
    assert 'Roles asignados' in body(navegador)
    marcar_rol(navegador, 'Miembro del comité científico')
    guardar(navegador)
    esperar_texto(navegador, EXITO_OTRO)
    evidencia('EXITO')
    # Al entrar con esa cuenta ahora debe elegir con qué rol trabajar
    cambiar_usuario(navegador, datos['correo'])
    assert '¿Con qué rol quieres trabajar?' in body(navegador)


def test_hu004_cp03_campos_obligatorios(navegador, evidencia):
    """Con nombre, apellido e institución vacíos no se guarda nada."""
    datos = cuenta_nueva(navegador, 'HU004C')
    abrir_edicion_como_admin(navegador, datos)
    for campo in ('nombre-editar', 'apellido-editar', 'institucion-editar'):
        escribir(navegador, campo, '')
    guardar(navegador)
    texto = body(navegador)
    for mensaje in ('Ingresa el nombre.', 'Ingresa el apellido.', 'Ingresa la institución o afiliación.'):
        assert mensaje in texto, mensaje
    assert EXITO_OTRO not in texto
    evidencia('EXITO')


def test_hu004_cp04_correo_invalido(navegador, evidencia):
    """Un correo sin formato válido se rechaza."""
    datos = cuenta_nueva(navegador, 'HU004D')
    abrir_edicion_como_admin(navegador, datos)
    escribir(navegador, 'correo-editar', 'correo sin arroba')
    guardar(navegador)
    assert 'Ingresa un correo electrónico válido, sin espacios.' in body(navegador)
    assert EXITO_OTRO not in body(navegador)
    evidencia('EXITO')


def test_hu004_cp05_correo_repetido(navegador, evidencia):
    """No se puede usar el correo de otra cuenta que ya existe."""
    datos = cuenta_nueva(navegador, 'HU004E')
    abrir_edicion_como_admin(navegador, datos)
    escribir(navegador, 'correo-editar', 'comite@pruebas.co')
    guardar(navegador)
    esperar_texto(navegador, 'Ya existe una cuenta con este correo.')
    assert EXITO_OTRO not in body(navegador)
    evidencia('EXITO')


def test_hu004_cp06_usuario_actualiza_sus_datos(navegador, evidencia):
    """El propio usuario cambia sus datos desde «Actualizar mis datos» y no puede tocar sus roles."""
    datos = cuenta_nueva(navegador, 'HU004F')
    abrir_mis_datos(navegador, datos['correo'])
    texto = body(navegador)
    assert 'Actualizar mis datos' in texto
    assert 'Roles asignados' not in texto
    escribir(navegador, 'apellido-editar', f"{datos['apellido']} Editado")
    escribir(navegador, 'institucion-editar', 'Universidad Javeriana Cali')
    guardar(navegador)
    esperar_texto(navegador, EXITO_PROPIO)
    evidencia('EXITO')
    # Al volver a entrar los datos siguen guardados
    cambiar_usuario(navegador, datos['correo'])
    clic_en_panel(navegador, 'Actualizar mis datos')
    esperar_formulario_edicion(navegador)  # espera a que el formulario cargue los datos guardados
    assert navegador.find_element(By.ID, 'institucion-editar').get_attribute('value') == 'Universidad Javeriana Cali'


def test_hu004_cp07_cambiar_contrasena(navegador, evidencia):
    """El usuario cambia su contraseña y después entra con la nueva."""
    datos = cuenta_nueva(navegador, 'HU004G')
    abrir_mis_datos(navegador, datos['correo'])
    escribir(navegador, 'contrasena-editar-input', NUEVA_CLAVE)
    escribir(navegador, 'confirmar-contrasena-editar', NUEVA_CLAVE)
    guardar(navegador)
    esperar_texto(navegador, EXITO_PROPIO)
    evidencia('GUARDADO')
    navegador.get(BASE)
    navegador.execute_script('window.sessionStorage.clear(); window.localStorage.clear();')
    login(navegador, datos['correo'], NUEVA_CLAVE)
    assert 'Cerrar sesión' in body(navegador)
    evidencia('EXITO')


def test_hu004_cp08_contrasena_invalida(navegador, evidencia):
    """Contraseña corta y confirmación distinta se rechazan."""
    datos = cuenta_nueva(navegador, 'HU004H')
    abrir_mis_datos(navegador, datos['correo'])
    escribir(navegador, 'contrasena-editar-input', 'abc12')
    escribir(navegador, 'confirmar-contrasena-editar', 'abc12')
    guardar(navegador)
    assert 'La contraseña debe tener al menos 8 caracteres.' in body(navegador)
    escribir(navegador, 'contrasena-editar-input', NUEVA_CLAVE)
    escribir(navegador, 'confirmar-contrasena-editar', 'Otra#Clave2026')
    guardar(navegador)
    assert 'Las contraseñas no coinciden.' in body(navegador)
    assert EXITO_PROPIO not in body(navegador)
    evidencia('EXITO')


def test_hu004_cp09_autor_no_edita_otras_cuentas(navegador, evidencia):
    """Un autor que escribe la dirección de edición de otra cuenta vuelve a su panel."""
    login(navegador, 'autor')
    ir_a_ruta(navegador, '/gestion/usuarios/1/editar')
    esperar_texto(navegador, 'Panel de autor')
    assert 'Editar usuario' not in body(navegador)
    assert '/gestion/usuarios' not in navegador.current_url
    evidencia('EXITO')


def test_hu004_cp10_cancelar_no_guarda(navegador, evidencia):
    """Si se cambia un dato y se presiona «Cancelar», el cambio no se guarda."""
    datos = cuenta_nueva(navegador, 'HU004J')
    abrir_edicion_como_admin(navegador, datos)
    escribir(navegador, 'institucion-editar', 'Institución que no se debe guardar')
    navegador.find_element(By.XPATH, '//a[normalize-space()="Cancelar"]').click()
    esperar_texto(navegador, datos['correo'], 60)
    fila = fila_de_usuario(navegador, datos['correo'])
    assert 'Universidad del Valle' in fila and 'no se debe guardar' not in fila, fila
    evidencia('EXITO')
