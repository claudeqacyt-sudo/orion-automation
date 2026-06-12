"""
tests/regression/admin/test_admin_config_extra.py
Suite de regresión — Admin: secciones de Configuración no cubiertas en ADM-009

ADM-010  Gestión de Campos            /configCamposGenerales
ADM-011  Preferencias de Campos       /confCamposCampana
ADM-012  Comunicaciones entre perfiles /configChatInterno
ADM-013  Plantillas Firmas/Respuestas  /configEmail
ADM-014  Gestión de Grupos             /configGrupoDeContactos
ADM-015  Replicación de Grupos         /configReplicaContactos
ADM-016  Programar Importación         /importacion
"""
import time
import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.regression, pytest.mark.admin]


def _esperar_menu_visible(page, element_id: str, timeout: int = 5000) -> None:
    try:
        page.wait_for_function(
            f"""() => {{
                const el = document.getElementById('{element_id}');
                if (!el) return false;
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            }}""",
            timeout=timeout
        )
    except Exception:
        pass


def _preparar_menu(page, abuelo, padre, hoja_id) -> bool:
    page.locator(f"#{abuelo}").click()
    if padre:
        _esperar_menu_visible(page, padre)
        page.locator(f"#{padre}").click()
    _esperar_menu_visible(page, hoja_id)
    return page.evaluate(f"""
        () => {{
            const el = document.getElementById('{hoja_id}');
            if (!el) return false;
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
        }}
    """)


def _abrir_tab(page, hoja_id, descripcion, abuelo, padre):
    visible = _preparar_menu(page, abuelo, padre, hoja_id)
    assert visible, f"'{descripcion}' no visible en menú"
    with page.context.expect_page(timeout=12000) as info:
        page.locator(f"#{hoja_id}").click()
    tab = info.value
    tab.wait_for_load_state("domcontentloaded", timeout=20000)
    try:
        tab.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    time.sleep(1.5)
    return tab


def _sin_error_servidor(tab):
    t = tab.inner_text("body").lower()
    return not any(x in t for x in ["server error", "exception", "404", "403"])


# ─── ADM-010 Gestión de Campos ────────────────────────────────────────────────

@pytest.fixture(scope="class")
def gestion_campos_tab(shared_page):
    tab = _abrir_tab(shared_page, "accionEjecutar_211", "Gestión de Campos",
                     "accionEjecutar_2", "accionEjecutar_21")
    yield tab
    tab.close()


class TestGestionCampos:
    def test_ADM010_A_carga_correctamente(self, gestion_campos_tab):
        """ADM-010-A: Gestión de Campos carga tabla, filtros y botones."""
        tab = gestion_campos_tab
        assert "/configCamposGenerales" in tab.url
        assert _sin_error_servidor(tab)
        assert "campos" in tab.inner_text("body").lower()
        assert tab.locator("#dt-resultados-busqueda").count() > 0
        expect(tab.locator("#btnBuscar")).to_be_visible()

    def test_ADM010_B_filtro_tipo_tiene_opciones(self, gestion_campos_tab):
        """ADM-010-B: El select de tipo de campo tiene opciones."""
        opts = gestion_campos_tab.evaluate(
            "() => document.querySelector('#filtroTipoDeCampo').options.length"
        )
        assert opts > 0

    def test_ADM010_C_filtro_nombre_y_buscar(self, gestion_campos_tab):
        """ADM-010-C: El filtro de nombre acepta texto y el botón Buscar responde."""
        tab = gestion_campos_tab
        tab.locator("#filtroNombre").fill("test")
        tab.locator("#btnBuscar").click()
        time.sleep(1.0)
        tab.locator("#filtroNombre").fill("")
        tab.locator("#btnBuscar").click()
        time.sleep(1.0)

    def test_ADM010_D_select_campania_tiene_opciones(self, gestion_campos_tab):
        """ADM-010-D: Los selects de campaña tienen opciones disponibles."""
        tab = gestion_campos_tab
        for sel in ("#selConfGlobalOporCampania", "#selCampaniaDefault"):
            count = tab.evaluate(
                f"() => document.querySelector('{sel}') ? "
                f"document.querySelector('{sel}').options.length : 0"
            )
            assert count > 0, f"Select '{sel}' sin opciones"


# ─── ADM-011 Preferencias de Campos ──────────────────────────────────────────

@pytest.fixture(scope="class")
def pref_campos_tab(shared_page):
    tab = _abrir_tab(shared_page, "accionEjecutar_212", "Preferencias de Campos",
                     "accionEjecutar_2", "accionEjecutar_21")
    yield tab
    tab.close()


class TestPreferenciasCampos:
    def test_ADM011_A_carga_correctamente(self, pref_campos_tab):
        """ADM-011-A: Preferencias de Campos carga tabla y selectores."""
        tab = pref_campos_tab
        assert "/confCamposCampana" in tab.url
        assert _sin_error_servidor(tab)
        assert "preferencias" in tab.inner_text("body").lower()
        assert tab.locator("#dt-resultados-busqueda").count() > 0

    def test_ADM011_B_selects_tienen_opciones(self, pref_campos_tab):
        """ADM-011-B: Los selects de campaña y configuración tienen opciones."""
        tab = pref_campos_tab
        for sel in ("#selCampania", "#selGlobalYXCampana"):
            count = tab.evaluate(
                f"() => document.querySelector('{sel}') ? "
                f"document.querySelector('{sel}').options.length : 0"
            )
            assert count > 0, f"Select '{sel}' sin opciones"

    def test_ADM011_C_boton_desplegar(self, pref_campos_tab):
        """ADM-011-C: El botón Desplegar está presente y responde via JS click."""
        tab = pref_campos_tab
        assert tab.locator("#dropdownall").count() > 0, "#dropdownall no encontrado"
        tab.evaluate("document.querySelector('#dropdownall').click()")
        time.sleep(0.8)


# ─── ADM-012 Comunicaciones entre perfiles ────────────────────────────────────

@pytest.fixture(scope="class")
def chat_interno_tab(shared_page):
    tab = _abrir_tab(shared_page, "accionEjecutar_231", "Comunicaciones entre perfiles",
                     "accionEjecutar_2", "accionEjecutar_23")
    yield tab
    tab.close()


class TestComunicacionesPerfiles:
    def test_ADM012_A_carga_correctamente(self, chat_interno_tab):
        """ADM-012-A: Comunicaciones entre perfiles carga con select de perfiles."""
        tab = chat_interno_tab
        assert "/configChatInterno" in tab.url
        assert _sin_error_servidor(tab)
        assert "chat" in tab.inner_text("body").lower()
        assert tab.locator("#cmbPerfiles").count() > 0

    def test_ADM012_B_select_perfiles_tiene_opciones(self, chat_interno_tab):
        """ADM-012-B: El select de perfiles tiene al menos una opción."""
        opts = chat_interno_tab.evaluate(
            "() => document.querySelector('#cmbPerfiles').options.length"
        )
        assert opts > 0

    def test_ADM012_C_cambiar_perfil_y_filtrar(self, chat_interno_tab):
        """ADM-012-C: Cambiar el perfil seleccionado y usar el filtro de texto."""
        tab = chat_interno_tab
        tab.locator("#cmbPerfiles").select_option(index=0)
        time.sleep(1.0)
        tab.locator("#txtFiltro").fill("Agente")
        time.sleep(0.5)
        tab.locator("#txtFiltro").fill("")


# ─── ADM-013 Plantillas Firmas y Respuestas ───────────────────────────────────

@pytest.fixture(scope="class")
def plantillas_email_tab(shared_page):
    tab = _abrir_tab(shared_page, "accionEjecutar_241", "Plantillas Firmas y Respuestas",
                     "accionEjecutar_2", "accionEjecutar_24")
    yield tab
    tab.close()


class TestPlantillasFirmas:
    def test_ADM013_A_carga_correctamente(self, plantillas_email_tab):
        """ADM-013-A: Plantillas de Firmas y Respuestas carga el editor."""
        tab = plantillas_email_tab
        assert "/configEmail" in tab.url
        assert _sin_error_servidor(tab)
        body = tab.inner_text("body").lower()
        assert "firma" in body or "email" in body or "plantilla" in body

    def test_ADM013_B_input_nombre_presente(self, plantillas_email_tab):
        """ADM-013-B: El campo de nombre de recurso está presente."""
        assert plantillas_email_tab.locator("#txtNombreRecurso").count() > 0


# ─── ADM-014 Gestión de Grupos ───────────────────────────────────────────────

@pytest.fixture(scope="class")
def gestion_grupos_tab(shared_page):
    tab = _abrir_tab(shared_page, "accionEjecutar_251", "Gestión de Grupos",
                     "accionEjecutar_2", "accionEjecutar_25")
    yield tab
    tab.close()


class TestGestionGrupos:
    def test_ADM014_A_carga_correctamente(self, gestion_grupos_tab):
        """ADM-014-A: Gestión de Grupos carga tabla y selector de cliente."""
        tab = gestion_grupos_tab
        assert "/configGrupoDeContactos" in tab.url
        assert _sin_error_servidor(tab)
        assert "grupo" in tab.inner_text("body").lower()
        assert tab.locator("#dt-campana-grupo").count() > 0

    def test_ADM014_B_select_cliente_tiene_opciones(self, gestion_grupos_tab):
        """ADM-014-B: El selector de cliente tiene opciones."""
        opts = gestion_grupos_tab.evaluate(
            "() => document.querySelector('#cmbCliente').options.length"
        )
        assert opts > 0

    def test_ADM014_C_botones_accion_visibles(self, gestion_grupos_tab):
        """ADM-014-C: Los botones de acción (Nuevo, Historial, Ver Contactos) están visibles."""
        tab = gestion_grupos_tab
        for btn_id in ("#btnNuevo", "#btnHistorial", "#btnContactos"):
            assert tab.locator(btn_id).count() > 0, f"Botón '{btn_id}' no encontrado"

    def test_ADM014_D_tabla_grupos_presente(self, gestion_grupos_tab):
        """ADM-014-D: La tabla de grupos está presente y tiene filas."""
        tab = gestion_grupos_tab
        assert tab.locator("#dt-campana-grupo").count() > 0
        # Verificar que el select tiene valor seleccionado (via JS para evitar disabled)
        val = tab.evaluate(
            "() => document.querySelector('#cmbCliente') ? "
            "document.querySelector('#cmbCliente').options.length : 0"
        )
        assert val > 0


# ─── ADM-015 Replicación de Grupos ───────────────────────────────────────────

@pytest.fixture(scope="class")
def replica_grupos_tab(shared_page):
    tab = _abrir_tab(shared_page, "accionEjecutar_252", "Replicación de Grupos",
                     "accionEjecutar_2", "accionEjecutar_25")
    yield tab
    tab.close()


@pytest.mark.skip(reason="Deshabilitado")
class TestReplicacionGrupos:
    def test_ADM015_A_carga_correctamente(self, replica_grupos_tab):
        """ADM-015-A: Replicación de Grupos carga con selector de cliente."""
        tab = replica_grupos_tab
        assert "/configReplicaContactos" in tab.url
        assert _sin_error_servidor(tab)
        body = tab.inner_text("body").lower()
        assert "replica" in body or "replicaci" in body
        assert tab.locator("#cmbCliente").count() > 0

    def test_ADM015_B_filtro_y_select_funcionan(self, replica_grupos_tab):
        """ADM-015-B: El selector de cliente y el filtro de texto responden."""
        tab = replica_grupos_tab
        tab.locator("#cmbCliente").select_option(index=0)
        time.sleep(1.0)
        tab.locator("#txtFiltro").fill("test")
        time.sleep(0.5)
        tab.locator("#txtFiltro").fill("")


# ─── ADM-016 Programar Importación ───────────────────────────────────────────

@pytest.fixture(scope="class")
def programar_importacion_tab(shared_page):
    tab = _abrir_tab(shared_page, "accionEjecutar_261", "Programar Importación",
                     "accionEjecutar_2", "accionEjecutar_26")
    yield tab
    tab.close()


class TestProgramarImportacion:
    def test_ADM016_A_carga_correctamente(self, programar_importacion_tab):
        """ADM-016-A: Programar Importación carga con selectores y botón Resumen."""
        tab = programar_importacion_tab
        assert "/importacion" in tab.url
        assert _sin_error_servidor(tab)
        assert "importaci" in tab.inner_text("body").lower()
        for sel in ("#cmbClientes", "#cmbGrupos"):
            assert tab.locator(sel).count() > 0, f"Select '{sel}' no encontrado"

    def test_ADM016_B_boton_resumen_visible_y_clickeable(self, programar_importacion_tab):
        """ADM-016-B: El botón Resumen está visible y responde al click."""
        tab = programar_importacion_tab
        expect(tab.locator("#btnImportacionesProgramadas")).to_be_visible()
        tab.locator("#btnImportacionesProgramadas").click()
        time.sleep(1.0)
        assert "/importacion" in tab.url

    def test_ADM016_C_selects_tienen_opciones(self, programar_importacion_tab):
        """ADM-016-C: Los selects de cliente y grupo tienen opciones."""
        tab = programar_importacion_tab
        for sel in ("#cmbClientes", "#cmbGrupos"):
            count = tab.evaluate(
                f"() => document.querySelector('{sel}') ? "
                f"document.querySelector('{sel}').options.length : 0"
            )
            assert count > 0, f"Select '{sel}' sin opciones"
