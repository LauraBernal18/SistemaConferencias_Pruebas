import uuid
from datetime import datetime, timedelta
from contextlib import contextmanager
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from sgc_helpers import BASE, body, click_text, login, react_value, visible_text

QA = 'Conferencia de Pruebas QA · 2027'
MAIN = 'Congreso de Pruebas · 2027'
STAGES = ['POSTULACION','EVALUACION','VERSIONES_CORREGIDAS','PRESENTACION','DOCUMENTOS_FINALES']
NEW_DATES = {
    'POSTULACION': ('2026-11-08T16:07','2026-12-13T16:07'),
    'EVALUACION': ('2026-12-14T16:07','2027-01-03T16:07'),
    'VERSIONES_CORREGIDAS': ('2027-01-04T16:07','2027-01-18T16:07'),
    'PRESENTACION': ('2027-01-19T16:07','2027-01-28T16:07'),
    'DOCUMENTOS_FINALES': ('2027-01-29T16:07','2027-02-12T16:07'),
}


def wait_config_ready(d, timeout=100):
    """Espera la carga asíncrona real de fechas y líneas, no solo el selector."""
    def ready(driver):
        page = body(driver)
        if 'Cargando plazos y líneas temáticas' in page:
            return False
        required = ('POSTULACION-inicio', 'EVALUACION-inicio',
                    'nombre-linea', 'descripcion-linea')
        return all(driver.find_elements(By.ID, name) for name in required)

    try:
        WebDriverWait(d, timeout, poll_frequency=0.5).until(ready)
    except Exception as exc:
        selected = d.find_elements(By.ID, 'conferencia-configuracion')
        selected_name = Select(selected[0]).first_selected_option.text if selected else '(sin selector)'
        raise AssertionError(
            f'No terminó de cargar la configuración de {selected_name} '
            f'en {timeout}s. Texto visible: {body(d)[:650]!r}'
        ) from exc


def open_config(d):
    # Navegar por interfaz, no URL directa: Vercel puede responder 404.
    click_text(d, 'Configurar fechas y líneas temáticas')
    WebDriverWait(d, 30).until(
        EC.visibility_of_element_located((By.ID, 'conferencia-configuracion'))
    )
    wait_config_ready(d)


def select_conference(d, name):
    selector = WebDriverWait(d, 30).until(
        EC.presence_of_element_located((By.ID, 'conferencia-configuracion'))
    )
    options = Select(selector).options
    matches = [opt for opt in options if opt.text.strip() == name]
    assert matches, f'No existe la conferencia {name}. Opciones: {[o.text for o in options]}'

    current = Select(selector).first_selected_option.text.strip()
    if current != name:
        # Durante cambios/cargas, algunas opciones pueden estar deshabilitadas.
        WebDriverWait(d, 100, poll_frequency=0.5).until(
            lambda driver: next((o.is_enabled() for o in
                Select(driver.find_element(By.ID, 'conferencia-configuracion')).options
                if o.text.strip() == name), False)
        )
        Select(d.find_element(By.ID, 'conferencia-configuracion')).select_by_visible_text(name)

    WebDriverWait(d, 30).until(lambda driver:
        Select(driver.find_element(By.ID, 'conferencia-configuracion'))
        .first_selected_option.text.strip() == name)
    wait_config_ready(d)


def setup(d, who='admin', conf=QA):
    login(d, who)
    open_config(d)
    select_conference(d, conf)
    

def dates(d):
    return {f'{stage}-{kind}': d.find_element(By.ID, f'{stage}-{kind}').get_attribute('value')
            for stage in STAGES for kind in ('inicio','fin')}

def set_date(d, stage, kind, value):
    react_value(d, d.find_element(By.ID, f'{stage}-{kind}'), value)


def set_dates(d, mapping):
    for key, value in mapping.items():
        stage, kind = key.rsplit('-', 1)
        set_date(d, stage, kind, value)


def save_dates(d):
    click_text(d, 'Guardar fechas límite')


def refresh_config(d, conf=QA):
    # Seleccionar otra conferencia y regresar, sin recargar directamente la ruta SPA
    alternate = MAIN if conf == QA else QA
    select_conference(d, alternate)
    select_conference(d, conf)


def line_card(d, name):
    return WebDriverWait(d, 20).until(EC.visibility_of_element_located((By.XPATH, f'//article[.//h3[normalize-space()="{name}"]]')))


def line_snapshot(d):
    wait_config_ready(d)
    return {e.find_element(By.TAG_NAME, 'h3').text: e.text for e in d.find_elements(By.CSS_SELECTOR, 'article')}


def add_line(d, name, description):
    d.find_element(By.ID, 'nombre-linea').send_keys(name)
    d.find_element(By.ID, 'descripcion-linea').send_keys(description)
    click_text(d, 'Agregar línea temática')
    visible_text(d, f'La línea temática «{name}» se guardó correctamente.', 90)
    assert 'Habilitada' in line_card(d, name).text


def edit_line(d, name, description):
    line_card(d, name).find_element(By.XPATH, './/button[normalize-space()="Editar"]').click()
    field = WebDriverWait(d, 10).until(EC.visibility_of_element_located((By.ID, 'descripcion-linea')))
    field.clear(); field.send_keys(description)
    # Botón guardar puede cambiar al modo edición: no inventamos el texto; localizamos submit del formulario de líneas.
    form = d.find_element(By.ID, 'nombre-linea').find_element(By.XPATH, './ancestor::form')
    form.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    visible_text(d, f'La línea temática «{name}» se guardó correctamente.', 90)
    assert description in line_card(d, name).text


def deactivate(d, name):
    card = line_card(d, name)
    if 'Desactivada' in card.text:
        return
    card.find_element(By.XPATH, './/button[normalize-space()="Desactivar"]').click()
    visible_text(d, f'La línea temática «{name}» se desactivó correctamente.', 90)
    assert 'Desactivada' in line_card(d, name).text
    

@pytest.mark.parametrize('who', ['admin', 'comite'])
    
def test_hu030_cp01_usuarios_autorizados(navegador, who):
    setup(navegador, who)
    assert 'Configuración de conferencia' in body(navegador)
    assert 'Fechas límite' in body(navegador)
    assert 'Líneas temáticas' in body(navegador)


def test_hu030_cp02_guardar_cinco_plazos(navegador, evidencia):
    setup(navegador)
    original = dates(navegador)
    try:
        set_dates(navegador, {f'{s}-{k}': v[i] for s, v in NEW_DATES.items() for i, k in enumerate(('inicio','fin'))})
        save_dates(navegador)
        visible_text(navegador, 'Los cinco plazos de la conferencia se guardaron correctamente.', 90)
        refresh_config(navegador)
        actual = dates(navegador)
        for stage, (start, end) in NEW_DATES.items():
            assert actual[f'{stage}-inicio'] == start
            assert actual[f'{stage}-fin'] == end
        evidencia('EXITO')
    finally:
        # Restaurar incluso cuando la aserción falle
        set_dates(navegador, original)
        save_dates(navegador)
        visible_text(navegador, 'Los cinco plazos de la conferencia se guardaron correctamente.', 90)
        refresh_config(navegador)
        assert dates(navegador) == original, 'No se restauraron los plazos originales'


def test_hu030_cp03_fin_antes_inicio(navegador):
    setup(navegador)
    original = dates(navegador)
    set_date(navegador, 'EVALUACION', 'inicio', '2026-12-20T10:00')
    set_date(navegador, 'EVALUACION', 'fin', '2026-12-19T10:00')
    save_dates(navegador)
    visible_text(navegador, 'La fecha de fin de «Evaluación por el comité científico» debe ser posterior a su fecha de inicio.')
    refresh_config(navegador)
    assert dates(navegador) == original


def test_hu030_cp04_orden_incorrecto(navegador):
    setup(navegador)
    original = dates(navegador)
    set_date(navegador, 'EVALUACION', 'inicio', '2026-12-12T16:07')
    save_dates(navegador)
    visible_text(navegador, '«Evaluación por el comité científico» debe iniciar después de que termine «Postulación de artículos».')
    refresh_config(navegador)
    assert dates(navegador) == original
    
def test_hu030_cp05_crear_editar_desactivar(navegador, evidencia):
    setup(navegador)
    name = f'Computación en la nube QA_{uuid.uuid4().hex[:8]}'
    add_line(navegador, name, 'Arquitecturas y servicios de computación en la nube')
    try:
        edit_line(navegador, name, 'Arquitecturas, servicios y seguridad en la nube')
        evidencia('EXITO_EDICION')
    finally:
        deactivate(navegador, name)
    assert 'Desactivada' in line_card(navegador, name).text


def test_hu030_cp06_consultar_lineas(navegador):
    setup(navegador)
    for name in ('Ciencia de datos','Interacción humano-computador','Redes y comunicaciones'):
        assert 'Habilitada' in line_card(navegador, name).text
    assert 'Desactivada' in line_card(navegador, 'prueba').text


def test_hu030_cp07_configuraciones_aisladas(navegador):
    setup(navegador, conf=MAIN)
    main_dates, main_lines = dates(navegador), line_snapshot(navegador)
    select_conference(navegador, QA)
    qa_dates, qa_lines = dates(navegador), line_snapshot(navegador)
    assert main_dates != qa_dates
    assert 'Bases de datos' in main_lines
    assert 'Ciencia de datos' in qa_lines
    assert 'Ciencia de datos' not in main_lines
    assert 'Bases de datos' not in qa_lines


def test_hu030_cp08_cambios_solo_qa(navegador, evidencia):
    setup(navegador, conf=MAIN)
    main_snapshot = (dates(navegador), line_snapshot(navegador))
    select_conference(navegador, QA)
    name = 'Ciencia de datos'
    original_description = line_card(navegador, name).find_element(By.TAG_NAME, 'p').text
    changed = original_description + ' [QA temporal]'
    try:
        edit_line(navegador, name, changed)
        select_conference(navegador, MAIN)
        assert (dates(navegador), line_snapshot(navegador)) == main_snapshot
        evidencia('EXITO')
    finally:
        select_conference(navegador, QA)
        edit_line(navegador, name, original_description)
        assert original_description in line_card(navegador, name).text


def reset_session(d):
    """Cierra la sesión de pruebas entre roles sin navegar a rutas SPA internas."""
    d.get(BASE)
    d.execute_script('window.localStorage.clear(); window.sessionStorage.clear();')
    d.delete_all_cookies()
    d.get(BASE)
    
def open_article_form(d):
    """Navega desde el panel del autor: evita el 404 al abrir una ruta SPA directamente."""
    click_text(d, 'Registrar un artículo', 30)
    WebDriverWait(d, 40).until(EC.visibility_of_element_located((By.ID, 'titulo-articulo')))
    WebDriverWait(d, 90).until(lambda driver:
        len(Select(driver.find_element(By.ID, 'convocatoria')).options) > 0)


def choose_qa_article(d, allow_unavailable=False):
    selector = Select(d.find_element(By.ID, 'convocatoria'))
    qa = [opt for opt in selector.options
          if opt.text.strip() == 'Conferencia de Pruebas QA - 2027']
    if not qa or not qa[0].is_enabled():
        if allow_unavailable:
            return False  # La convocatoria vencida ya no admite selección en la interfaz.
        raise AssertionError('No se puede seleccionar la conferencia QA durante su plazo vigente')
    selector.select_by_visible_text('Conferencia de Pruebas QA - 2027')
    WebDriverWait(d, 90).until(lambda driver: 'Ciencia de datos' in
        [opt.text.strip() for opt in Select(driver.find_element(By.ID, 'linea-tematica')).options])
    Select(d.find_element(By.ID, 'linea-tematica')).select_by_visible_text('Ciencia de datos')
    return True


def fill_article(d, title):
    d.find_element(By.ID, 'titulo-articulo').send_keys(title)
    d.find_element(By.ID, 'resumen-articulo').send_keys(
        'Propuesta de prueba QA para comprobar el control de plazos de postulación.')
    d.find_element(By.ID, 'palabras-clave').send_keys('QA, automatización, plazos')
    # Los campos del autor registrador se autocompletan y son readonly.
    assert d.find_element(By.ID, 'autor-email-autor-registrador').get_attribute('value')
    assert d.find_element(By.ID, 'autor-nombres-autor-registrador').get_attribute('readonly') is not None



def test_hu030_cp09_plazos_registro_articulos(navegador, evidencia):
    """Verifica postulación vigente y vencida, con restauración obligatoria de QA.

    Advertencia: crea un artículo de prueba real y modifica temporalmente la
    fecha de cierre de postulación de la conferencia QA.
    """
    d = navegador
    original = None
    dates_changed = False
    positive_title = f'QA plazo vigente {uuid.uuid4().hex[:10]}'
    negative_title = f'QA plazo vencido {uuid.uuid4().hex[:10]}'

    try:
        # Leer el periodo original ANTES de crear artículos.
        setup(d, 'admin', QA)
        original = dates(d)
        start = datetime.fromisoformat(original['POSTULACION-inicio'])
        end = datetime.fromisoformat(original['POSTULACION-fin'])
        now = datetime.now()
        if not start < now < end:
            pytest.skip('CP09 requiere que la postulación de QA esté vigente para la comprobación positiva; '
                        f'periodo actual: {start} a {end}, ahora: {now}. No se modificaron plazos.')

        # Fase 1: una postulación real, dentro del plazo.
        reset_session(d)
        login(d, 'autor')
        open_article_form(d)
        choose_qa_article(d)
        fill_article(d, positive_title)
        click_text(d, 'Registrar propuesta')
        visible_text(d, f'El artículo "{positive_title}" se registró correctamente.', 90)
        assert 'Conferencia de Pruebas QA - 2027' in body(d)
        assert 'Ciencia de datos' in body(d)
        evidencia('PLAZO_VIGENTE_EXITO')

        # Fase 2: cerrar la convocatoria en el pasado y comprobar rechazo.
        reset_session(d)
        setup(d, 'admin', QA)
        expiry = (datetime.now() - timedelta(days=2)).replace(second=0, microsecond=0)
        assert expiry > start, 'No existe margen para configurar un cierre pasado válido.'
        # Activar protección ANTES de intentar guardar: ante errores se intentará restaurar.
        dates_changed = True
        set_date(d, 'POSTULACION', 'fin', expiry.strftime('%Y-%m-%dT%H:%M'))
        save_dates(d)
        visible_text(d, 'Los cinco plazos de la conferencia se guardaron correctamente.', 90)
        refresh_config(d)
        assert dates(d)['POSTULACION-fin'] == expiry.strftime('%Y-%m-%dT%H:%M')

        reset_session(d)
        login(d, 'autor')
        open_article_form(d)
        if not choose_qa_article(d, allow_unavailable=True):
            # Rechazo en interfaz: la conferencia vencida no puede seleccionarse.
            evidencia('PLAZO_VENCIDO_NO_SELECCIONABLE')
        else:
            fill_article(d, negative_title)
            click_text(d, 'Registrar propuesta')
            
            # Si la convocatoria sigue seleccionable, se exige rechazo explícito.
            def expired_response(driver):
                txt = body(driver).lower()
                if ('artículo registrado' in txt or
                    f'el artículo "{negative_title.lower()}" se registró correctamente' in txt):
                    return 'UNEXPECTED_SUCCESS'
                negatives = ('plazo', 'fuera de fecha', 'fecha límite', 'vencid',
                             'cerrad', 'finaliz', 'no está habilitad',
                             'no se puede registrar', 'no se pueden registrar', 'no disponible')
                lines = [line.strip().lower() for line in body(driver).splitlines()]
                errors = [line for line in lines if any(x in line for x in negatives)
                          and not line.startswith('fecha límite:') and line != 'fecha límite']
                return 'REJECTED' if errors else False

            outcome = WebDriverWait(d, 40).until(expired_response)
            assert outcome == 'REJECTED', (
                'El sistema permitió registrar un artículo después del vencimiento. '
                f'Pantalla: {body(d)[:2000]}')
            evidencia('PLAZO_VENCIDO_RECHAZO')
    finally:
        if dates_changed and original is not None:
            try:
                reset_session(d)
                setup(d, 'admin', QA)
                set_date(d, 'POSTULACION', 'fin', original['POSTULACION-fin'])
                save_dates(d)
                visible_text(d, 'Los cinco plazos de la conferencia se guardaron correctamente.', 90)
                refresh_config(d)
                assert dates(d) == original, 'La restauración de fechas QA fue incompleta'
            except Exception as exc:
                pytest.fail(f'URGENTE: revisar/restaurar manualmente plazos de la conferencia QA. '
                            f'Fechas originales: {original}. Error: {exc}')


@pytest.mark.skip(reason='HU030-CP10: Vercel devuelve 404 al navegar directamente a rutas SPA también con administrador; pendiente corregir fallback y verificar permisos')
def test_hu030_cp10_autor_sin_permiso():
    pass

def test_hu030_cp11_mensaje_guardado_linea(navegador, evidencia):
    setup(navegador)
    name = f'Arquitectura de software QA_{uuid.uuid4().hex[:8]}'
    add_line(navegador, name, 'Diseño de sistemas y arquitecturas de software')
    try:
        evidencia('EXITO')
    finally:
        deactivate(navegador, name)


def test_hu030_cp12_fecha_incompleta(navegador):
    setup(navegador)
    original = dates(navegador)
    set_date(navegador, 'EVALUACION', 'inicio', '')
    save_dates(navegador)
    error = 'Completa las fechas de inicio y fin para «Evaluación por el comité científico».'
    visible_text(navegador, error)
    fieldset = navegador.find_element(By.XPATH, '//fieldset[.//input[@id="EVALUACION-inicio"]]')
    assert error in fieldset.text
    refresh_config(navegador)
    assert dates(navegador) == original
