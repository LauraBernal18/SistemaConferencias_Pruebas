# Llamadas directas a la API del backend para preparar datos de prueba (Sprint 2).
# Se usan solo para dejar listo lo que la interfaz no permite crear o lo que tomaría
# muchos pasos (cuentas del comité, artículos y fechas de la conferencia QA).
# Las verificaciones de las pruebas se siguen haciendo con Selenium desde la interfaz.
# Solo usa la biblioteca estándar de Python (no hay que instalar nada).

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from sgc_helpers import BASE, PASSWORD, USERS

if 'localhost' in BASE or '127.0.0.1' in BASE:
    API = os.getenv('SGC_API', 'http://localhost:8000/api').rstrip('/')
else:
    API = os.getenv('SGC_API', 'https://conferencia-cientifica-ds1-pruebas.onrender.com/api').rstrip('/')

# El entorno de pruebas acepta este token en lugar del CAPTCHA real
TOKEN_CAPTCHA = os.getenv('SGC_CAPTCHA_TOKEN', 'token-de-prueba')


def pedir(metodo, ruta, token=None, datos=None):
    """Hace la petición y devuelve el JSON de la respuesta. Si falla, muestra el error del servidor."""
    cuerpo = json.dumps(datos).encode('utf-8') if datos is not None else None
    peticion = urllib.request.Request(API + ruta, data=cuerpo, method=metodo)
    peticion.add_header('Content-Type', 'application/json')
    peticion.add_header('Accept', 'application/json')
    if token:
        peticion.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(peticion, timeout=120) as respuesta:
            texto = respuesta.read().decode('utf-8')
    except urllib.error.HTTPError as error:
        detalle = error.read().decode('utf-8', 'replace')
        raise AssertionError(f'{metodo} {ruta} respondió {error.code}: {detalle}') from None
    return json.loads(texto) if texto else {}


def token_de(quien):
    """Inicia sesión por la API (admin, comite, autor o un correo) y devuelve el token de acceso."""
    correo = USERS.get(quien, quien)
    datos = pedir('POST', '/auth/login/', datos={
        'email': correo, 'password': PASSWORD, 'captcha_token': TOKEN_CAPTCHA})
    return datos['access']


def convocatorias(token_autor):
    """Conferencias activas con sus líneas, como las ve el autor al registrar un artículo."""
    return pedir('GET', '/articulos/contexto/', token_autor)['convocatorias']


def buscar_convocatoria(lista, inicio_nombre):
    for conv in lista:
        if conv['nombre'].startswith(inicio_nombre):
            return conv
    raise AssertionError(f'No existe la convocatoria «{inicio_nombre}»')


def id_linea(convocatoria, *nombres):
    """Id de la primera línea habilitada cuyo nombre esté en nombres (o la primera, si no se dan)."""
    lineas = convocatoria['lineas_tematicas']
    for nombre in nombres:
        for linea in lineas:
            if linea['nombre'] == nombre:
                return linea['id'], linea['nombre']
    return lineas[0]['id'], lineas[0]['nombre']


def crear_usuario(token_admin, nombre, apellido, correo, roles, institucion='Universidad del Valle'):
    return pedir('POST', '/usuarios/', token_admin, {
        'first_name': nombre, 'last_name': apellido, 'email': correo, 'password': PASSWORD,
        'institucion': institucion, 'roles': roles})


def crear_articulo(token_autor, id_conferencia, linea, titulo, coautores=None):
    datos = pedir('POST', '/articulos/', token_autor, {
        'id_conferencia': id_conferencia, 'id_linea': linea, 'titulo': titulo,
        'resumen': 'Propuesta de prueba para la asignación de evaluadores.',
        'palabras_clave': 'pruebas, evaluadores, selenium', 'coautores': coautores or []})
    return datos['id_articulo']


def plazos(token_admin, id_conferencia):
    return pedir('GET', f'/conferencias/{id_conferencia}/plazos/', token_admin)


def plazo_de(lista, tipo):
    for plazo in lista:
        if plazo['tipo_plazo'] == tipo:
            return plazo
    raise AssertionError(f'La conferencia no tiene el plazo {tipo}')


def cambiar_plazo(token_admin, id_conferencia, id_plazo, inicio, fin):
    return pedir('PATCH', f'/conferencias/{id_conferencia}/plazos/{id_plazo}/', token_admin, {
        'fecha_inicio': inicio.isoformat(), 'fecha_fin': fin.isoformat()})


def fecha(texto):
    return datetime.fromisoformat(texto.replace('Z', '+00:00'))


def ahora():
    return datetime.now(timezone.utc).replace(microsecond=0)


__all__ = ['API', 'ahora', 'buscar_convocatoria', 'cambiar_plazo', 'convocatorias', 'crear_articulo',
           'crear_usuario', 'fecha', 'id_linea', 'pedir', 'plazo_de', 'plazos', 'timedelta', 'token_de']
