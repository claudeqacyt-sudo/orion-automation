"""
tests/regression/monitor/test_monitor_online.py
Suite de regresion - Supervision > Monitores > Monitor de Efectividad (/MonitorEfectividad)

Estructura DOM verificada:
  #panelMonitorEfectividad  -> panel principal
  #tituloPrincipal          -> h2 "Monitores de Efectividad"
  #monitorWrapper           -> section de contenido
  .no-monitors              -> h3 mensaje cuando no hay monitores configurados

Estado base del sistema (verificado):
  No hay monitores creados asignados al usuario cyt.
  La pagina muestra: "Sin monitores creados asignados a su usuario"
"""
import pytest
from pages.monitor_page import MonitorNav, MonitorEfectividadPage
pytestmark = pytest.mark.skip(reason="temporalmente desactivado -- foco en tests FRW supervisor")



# ─────────────────────────────────────────────────────────────────────────────
# Fixture de seccion - abre la pestana UNA VEZ para toda la clase
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def monitor_tab(shared_page):
    """
    Abre Monitor de Efectividad una sola vez para todos los tests de la clase.
    Al terminar cierra la pestana.
    """
    nav = MonitorNav(shared_page)
    tab = nav.open_monitor_efectividad()
    page_obj = MonitorEfectividadPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


# ─────────────────────────────────────────────────────────────────────────────
# MON-001 - Monitor de Efectividad
# ─────────────────────────────────────────────────────────────────────────────

class TestMonitorEfectividad:

    # ── MON-001-A ────────────────────────────────────────────────────

    def test_MON001_carga_correctamente(self, monitor_tab):
        """
        MON-001-A: La seccion carga y la URL es correcta.
        Verifica: URL contiene /MonitorEfectividad, panel principal visible.
        """
        page_obj = monitor_tab
        page_obj.verify_page_loaded()

        assert MonitorEfectividadPage.URL_PATH in page_obj.page.url, \
            f"URL incorrecta: {page_obj.page.url}"

        assert page_obj.panel_es_visible(), \
            "#panelMonitorEfectividad no esta visible"

    # ── MON-001-B ────────────────────────────────────────────────────

    def test_MON001_titulo_correcto(self, monitor_tab):
        """
        MON-001-B: El titulo de la pagina es "Monitores de Efectividad".
        """
        page_obj = monitor_tab
        titulo = page_obj.get_titulo()

        assert MonitorEfectividadPage.TITULO_ESPERADO.lower() in titulo.lower(), \
            f"Titulo incorrecto: '{titulo}' " \
            f"(esperado: '{MonitorEfectividadPage.TITULO_ESPERADO}')"

    # ── MON-001-C ────────────────────────────────────────────────────

    def test_MON001_monitor_wrapper_presente(self, monitor_tab):
        """
        MON-001-C: La seccion #monitorWrapper esta presente y visible.
        Es el contenedor principal del monitor; siempre debe existir
        independientemente de si hay monitores configurados o no.
        """
        page_obj = monitor_tab

        assert page_obj.wrapper_es_visible(), \
            "#monitorWrapper no esta visible en la pagina"

    # ── MON-001-D ────────────────────────────────────────────────────

    def test_MON001_estado_vacio_sin_monitores(self, monitor_tab):
        """
        MON-001-D: En el estado base del sistema no hay monitores configurados.
        La pagina debe mostrar el mensaje "Sin monitores creados asignados a su usuario".
        """
        page_obj = monitor_tab

        assert page_obj.tiene_mensaje_sin_monitores(), \
            f"Se esperaba el mensaje '{MonitorEfectividadPage.MSG_SIN_MONITOR_TEXTO}' " \
            f"pero no se encontro en la pagina"

