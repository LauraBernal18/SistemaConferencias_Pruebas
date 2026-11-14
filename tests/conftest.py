from pathlib import Path
import pytest

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    driver = item.funcargs.get("navegador")
    if driver is None:
        return
    folder = Path("evidencias") / "Sprint_1" / "HU030"
    folder.mkdir(parents=True, exist_ok=True)
    name = item.name.replace("/", "_").replace("\\", "_")
    try:
        driver.save_screenshot(str(folder / f"{name}_FALLO.png"))
    except Exception:
        pass
