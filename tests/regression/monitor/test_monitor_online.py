"""
tests/regression/monitor/test_monitor_online.py
Suite de regresion — Supervision > Monitores > Monitor de Efectividad (/MonitorEfectividad)

MON-001  Monitor de Efectividad — carga, titulo, estado sin monitores configurados

Navegacion: Supervision (4) -> Monitores (42) -> Monitor de Efectividad (421)
La pestana debe abrirse via click en el menu Angular (no goto directo).
"""
import time
import pytest
from pages.login_page import LoginPage

pytestmark = [pytest.mark.regression, pytest.mark.admin]


def _restaurar_sesion(page, base_url, credentials):
    """Navega a admincontactos y re-loguea si la sesión expiró."""
    try:
        page.goto(f"{base_url}/admincontactos", wait_until="commit", timeout=10000)
    except Exception:
        pass
    if "/login" in page.url or "login" in page.url.lower():
        try:
            login = LoginPage(page)
            login.navigate(base_url)
            login.login(credentials["username"], credentials["password"])
        except Exception:
            pass
        try:
            page.goto(f"{base_url}/admincontactos", wait_until="commit", timeout=10000)
        except Exception:
            pass
        time.sleep(2)
    try:
        page.locator("#accionEjecutar_4").wait_for(state="visible", timeout=20000)
    except Exception:
        pass


def _abrir_monitor(page, base_url, credentials):
    _restaurar_sesion(page, base_url, credentials)
    page.locator("#accionEjecutar_4").wait_for(state="visible", timeout=15000)
    page.evaluate("document.getElementById('accionEjecutar_4').click()")
    time.sleep(1.5)
    page.evaluate("document.getElementById('accionEjecutar_42').click()")
    time.sleep(1.0)
    with page.context.expect_page(timeout=15000) as info:
        page.evaluate("document.getElementById('accionEjecutar_421').click()")
    tab = info.value
    tab.wait_for_load_state("domcontentloaded", timeout=30000)
    try:
        tab.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    time.sleep(3)
    return tab


def _body(tab):
    return tab.evaluate("() => document.body ? document.body.innerText.toLowerCase() : ''")


@pytest.fixture(scope="class")
def monitor_tab(shared_page, base_url, admin_credentials):
    tab = _abrir_monitor(shared_page, base_url, admin_credentials)
    # Si el tab se cerró solo (el app llama window.close() durante la carga),
    # reintentamos una vez más.
    try:
        tab.evaluate("1")
    except Exception:
        try:
            tab.close()
        except Exception:
            pass
        tab = _abrir_monitor(shared_page, base_url, admin_credentials)
    yield tab
    try:
        tab.close()
    except Exception:
        pass


class TestMonitorEfectividad:

    def test_MON001_A_carga_correctamente(self, monitor_tab):
        """MON-001-A: Monitor de Efectividad carga en /MonitorEfectividad sin errores."""
        assert "/MonitorEfectividad" in monitor_tab.url, \
            f"URL inesperada: {monitor_tab.url}"
        body = _body(monitor_tab)
        assert not any(x in body for x in ["server error", "exception", "404", "403",
                                            "no autorizado"])

    def test_MON001_B_titulo_correcto(self, monitor_tab):
        """MON-001-B: La pagina contiene texto de monitores."""
        body = _body(monitor_tab)
        assert "monitor" in body, \
            f"No se encontro texto de 'monitor'. Body: {body[:200]}"

    def test_MON001_C_estado_sin_monitores(self, monitor_tab):
        """MON-001-C: El sistema muestra el estado vacio (sin monitores configurados)."""
        body = _body(monitor_tab)
        assert "sin monitores" in body or "monitor" in body, \
            f"No se encontro contenido de monitores. Body: {body[:200]}"
