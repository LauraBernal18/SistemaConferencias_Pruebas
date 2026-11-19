import os
import re

from datetime import datetime
from pathlib import Path

import pytest
from selenium import webdriver
from pathlib import Path
from selenium.webdriver.chrome.service import Service

ROOT = Path(__file__).resolve().parents[1]
ruta_driver = (
    Path(__file__).resolve().parent.parent
    / "drivers"
    / "chromedriver.exe"
)
service = Service(executable_path=str(ruta_driver))


@pytest.fixture
def navegador():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(
    service=service,
    options=options
    )
    driver.set_page_load_timeout(100)
    yield driver
    driver.quit()


def _save_image(driver, item_name, suffix):
    match = re.search(r'hu(\d{3})', item_name, re.I)
    hu = 'HU' + match.group(1) if match else 'GENERAL'
    sprint_2 = {
    'HU002', 'HU003', 'HU004', 'HU007',
    'HU011', 'HU012', 'HU014', 'HU015'
    }

    sprint = 'Sprint_2' if hu in sprint_2 else 'Sprint_1'

    folder = ROOT / 'evidencias' / sprint / hu
    folder.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[^\w.-]+', '_', item_name)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    path = folder / f'{safe}_{suffix}_{stamp}.png'
    try:
        driver.save_screenshot(str(path))
        return str(path.relative_to(ROOT))
    except Exception:
        return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == 'call' and report.failed:
        driver = item.funcargs.get('navegador')
        if driver:
            path = _save_image(driver, item.name, 'FALLO')
            if path:
                report.sections.append(('Captura de fallo', path))


@pytest.fixture
def evidencia(navegador, request):
    def guardar(etiqueta='EXITO'):
        return _save_image(navegador, request.node.name, etiqueta)
    return guardar
