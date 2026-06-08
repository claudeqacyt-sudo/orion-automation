"""
tests/regression/admin/test_admin_dashboards.py
Suite de regresión — Admin: Dashboards y Generador de Apps

ADM-017  Dashboards (Supervisión → Dashboards):
           431 Detallado de Comunicaciones  /Dashboard
           432 Interacciones por canal      /DashboardInteracciones
           433 Nube de Palabras             /DashboardNube
           434 Resultados por campaña       /DashboardResultados
           435 Eficiencia IVR-Bot           /DashboardEficiencia
           436 Plantillas de Whatsapp       /DashboardPlantillasWhatsapp
           437 Agentes                      /DashboardAgentes

ADM-018  Generador de Apps  (port :88)
"""
import time
import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.regression, pytest.mark.admin]


def _abrir_dashboard(page, hoja_id, descripcion):
    """Abre un dashboard: Supervisión → Dashboards → hoja."""
    page.locator("#accionEjecutar_4").click()
    time.sleep(1.0)
    page.locator("#accionEjecutar_43").click()
    time.sleep(1.0)
    visible = page.evaluate(f"""
        () => {{
            const el = document.getElementById('{hoja_id}');
            if (!el) return false;
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
        }}
    """)
    assert visible, f"'{descripcion}' no visible en menú Dashboards"
    with page.context.expect_page(timeout=12000) as info:
        page.evaluate(f"document.getElementById('{hoja_id}').click()")
    tab = info.value
    tab.wait_for_load_state("domcontentloaded", timeout=20000)
    try:
        tab.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    time.sleep(2)
    return tab


def _sin_error(tab):
    t = tab.inner_text("body").lower()
    return not any(x in t for x in ["server error", "exception", "404", "403"])


def _select_opts(tab, sel_id):
    return tab.evaluate(
        f"() => document.querySelector('#{sel_id}') ? "
        f"document.querySelector('#{sel_id}').options.length : 0"
    )


# ─── ADM-017 Dashboards ───────────────────────────────────────────────────────

class TestAdminDashboards:

    def test_ADM017_A_detallado_comunicaciones(self, shared_page):
        """ADM-017-A: Detallado de Comunicaciones carga sin errores."""
        tab = _abrir_dashboard(shared_page, "accionEjecutar_431", "Detallado de Comunicaciones")
        try:
            assert "/Dashboard" in tab.url
            assert _sin_error(tab)
        finally:
            tab.close()

    def test_ADM017_B_interacciones_por_canal(self, shared_page):
        """ADM-017-B: Interacciones por tipo de canal carga sin errores."""
        tab = _abrir_dashboard(shared_page, "accionEjecutar_432", "Interacciones por tipo de canal")
        try:
            assert "/DashboardInteracciones" in tab.url
            assert _sin_error(tab)
        finally:
            tab.close()

    def test_ADM017_C_nube_de_palabras(self, shared_page):
        """ADM-017-C: Nube de Palabras carga con selectores de filtro."""
        tab = _abrir_dashboard(shared_page, "accionEjecutar_433", "Nube de Palabras")
        try:
            assert "/DashboardNube" in tab.url
            assert _sin_error(tab)
            assert "nube" in tab.inner_text("body").lower()
            for sel in ("selectSentido", "selectCampania", "selectModelo", "selectTop"):
                assert _select_opts(tab, sel) > 0, f"Select '{sel}' sin opciones"
            tab.locator("#selectCampania").select_option(index=0)
            time.sleep(0.8)
        finally:
            tab.close()

    def test_ADM017_D_resultados_por_campania(self, shared_page):
        """ADM-017-D: Resultados por campaña carga con selectores y botón de actualización."""
        tab = _abrir_dashboard(shared_page, "accionEjecutar_434", "Resultados por campania")
        try:
            assert "/DashboardResultados" in tab.url
            assert _sin_error(tab)
            for sel in ("selectFecha", "selectCampania", "selectSentido"):
                assert _select_opts(tab, sel) > 0, f"Select '{sel}' sin opciones"
            expect(tab.locator("#btUpdate")).to_be_visible()
            tab.locator("#selectCampania").select_option(index=0)
            time.sleep(0.8)
            tab.locator("#btUpdate").click()
            time.sleep(1.5)
            assert "/DashboardResultados" in tab.url
        finally:
            tab.close()

    def test_ADM017_E_eficiencia_ivr_bot(self, shared_page):
        """ADM-017-E: Eficiencia IVR-Bot carga con selectores y botón de actualización."""
        tab = _abrir_dashboard(shared_page, "accionEjecutar_435", "Eficiencia IVR-Bot")
        try:
            assert "/DashboardEficiencia" in tab.url
            assert _sin_error(tab)
            for sel in ("selectRango", "selectCampania"):
                assert _select_opts(tab, sel) > 0, f"Select '{sel}' sin opciones"
            expect(tab.locator("#btUpdate")).to_be_visible()
            tab.locator("#selectCampania").select_option(index=0)
            time.sleep(0.8)
        finally:
            tab.close()

    def test_ADM017_F_plantillas_whatsapp(self, shared_page):
        """ADM-017-F: Plantillas de Whatsapp carga con selector de campaña."""
        tab = _abrir_dashboard(shared_page, "accionEjecutar_436", "Plantillas de Whatsapp")
        try:
            assert "/DashboardPlantillasWhatsapp" in tab.url
            assert _sin_error(tab)
            expect(tab.locator("#input-group-dropdown-1")).to_be_visible()
            tab.locator("#input-group-dropdown-1").click()
            time.sleep(0.8)
        finally:
            tab.close()

    def test_ADM017_G_agentes(self, shared_page):
        """ADM-017-G: Dashboard Agentes carga con selectores y botón de actualización."""
        tab = _abrir_dashboard(shared_page, "accionEjecutar_437", "Agentes")
        try:
            assert "/DashboardAgentes" in tab.url
            assert _sin_error(tab)
            for sel in ("selectFecha", "selectPromedio"):
                assert _select_opts(tab, sel) > 0, f"Select '{sel}' sin opciones"
            expect(tab.locator("#btUpdate")).to_be_visible()
            tab.locator("#selectFecha").select_option(index=0)
            time.sleep(0.8)
        finally:
            tab.close()


# ─── ADM-018 Generador de Apps ────────────────────────────────────────────────

class TestGeneradorApps:

    def test_ADM018_A_generador_carga_correctamente(self, shared_page):
        """ADM-018-A: Generador de Apps abre en nueva pestaña (port :88) con tabla de tareas."""
        page = shared_page
        page.locator("#accionEjecutar_4").click()
        time.sleep(1.0)
        visible = page.evaluate("""
            () => {
                const el = document.getElementById('accionEjecutar_45');
                if (!el) return false;
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            }
        """)
        assert visible, "Generador de Apps no visible en menú Supervisión"

        with page.context.expect_page(timeout=15000) as info:
            page.locator("#accionEjecutar_45").click()
        tab = info.value
        tab.wait_for_load_state("domcontentloaded", timeout=20000)
        try:
            tab.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        time.sleep(2)

        try:
            assert ":88" in tab.url or "generador" in tab.url.lower(), \
                f"URL inesperada para Generador: {tab.url}"
            assert _sin_error(tab)
            assert tab.locator("#tablaTareas").count() > 0, \
                "Tabla #tablaTareas no encontrada en Generador de Apps"
            tab.locator("#filtroTarea").fill("test")
            time.sleep(0.5)
            tab.locator("#filtroTarea").fill("")
        finally:
            tab.close()
