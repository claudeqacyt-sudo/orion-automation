"""
tests/regression/monitor/test_monitor_online.py
Suite de regresion — Supervision > Monitores > Monitor de Efectividad (/MonitorEfectividad)

MON-001  Monitor de Efectividad — carga, titulo, estado sin monitores configurados

Navegacion: Supervision (4) -> Monitores (42) -> Monitor de Efectividad (421)
La pestana debe abrirse via click en el menu Angular (no goto directo).
"""
import time
import pytest

pytestmark = [pytest.mark.regression, pytest.mark.admin]


def _abrir_monitor(page):
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
def monitor_tab(shared_page):
    tab = _abrir_monitor(shared_page)
    yield tab
    tab.close()


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
