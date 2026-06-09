"""
tests/regression/supervision/test_notificar_usuarios.py
Suite de regresion — Supervision > Notificar Usuarios (/MensajesUsuarios)

FIX: La pagina usa SignalR long-polling que bloquea a Playwright indefinidamente.
Solucion: page.route("**/signalr/**") que responde inmediatamente al long-poll.
El fixture espera a que Angular este completamente inicializado en admincontactos
ANTES de instalar el route e ir a MensajesUsuarios.
"""
import time
import pytest
from playwright.sync_api import Page, Route

pytestmark = [pytest.mark.regression, pytest.mark.admin]

BASE_PATH = "/MensajesUsuarios"

# ── Selectores ─────────────────────────────────────────────────────────────
PANEL          = "#panelMensajesProgramados"
FORM           = "#frmMessageData"
ASUNTO         = "#txtAsunto"
MENSAJE        = "#txaMensaje"
RADIO_AHORA    = "#rdbAhora"
RADIO_OTRO     = "#rdbOtroMomento"
DATETIME_OTRO  = "#datetimeOtroMomento"
SELECT_CLIENTE = "#cmbCliente"
LISTA_USUARIOS = "#listadoUsuarios"
BTN_ENVIAR     = "#btnGuardarMensaje"
TABLA_HISTORIAL = "#tblMensajesProgramados"
BTN_REFRESH    = "#btnRefreshTable"
MODAL_OK       = "#modalGlobalGenericoInfo_btnOK"
MENU_SUPERVISION = "#accionEjecutar_4"

# Timeout global para los tests NTF (el servidor puede estar lento en runs largos)
T = 25000


def _signalr_fix(route: Route):
    """Responde inmediatamente al long-poll de SignalR para evitar el cuelgue."""
    if "/signalr/poll" in route.request.url:
        route.fulfill(status=200,
                      body='{"C":"","M":[]}',
                      content_type="application/json; charset=utf-8")
    else:
        route.continue_()


def _navegar_ntf(page: Page, base_url: str) -> None:
    """Navega a /MensajesUsuarios (SignalR ya interceptado) y espera el panel."""
    try:
        page.goto(f"{base_url}{BASE_PATH}", wait_until="commit", timeout=10000)
    except Exception:
        pass
    # Esperar que Angular muestre el modal de error O cargue el panel directamente.
    # wait_for_function: polling JS puro, no sufre los 500ms de slow_mo por CDP call.
    try:
        page.wait_for_function(
            """() => {
                var modal = document.getElementById('modalGlobalGenericoInfo');
                var panel = document.getElementById('panelMensajesProgramados');
                var modalVisible = modal && (modal.className || '').indexOf('in') >= 0;
                var panelVisible = panel && panel.offsetParent !== null;
                return modalVisible || panelVisible;
            }""",
            timeout=20000
        )
    except Exception:
        pass
    # Cerrar modal via evaluate() — un solo CDP call, no afectado por slow_mo
    try:
        page.evaluate(
            "() => { var b = document.getElementById('modalGlobalGenericoInfo_btnOK'); if (b) b.click(); }"
        )
    except Exception:
        pass
    # Esperar el panel con offsetParent (CSS visible) hasta 30s
    try:
        page.wait_for_function(
            "() => { var p = document.getElementById('panelMensajesProgramados'); return p && p.offsetParent !== null; }",
            timeout=30000
        )
    except Exception:
        pass


@pytest.fixture(scope="class", autouse=True)
def ntf_navegacion(shared_page: Page, base_url: str):
    """Navega una vez a /MensajesUsuarios para toda la clase y hace cleanup al final."""
    # Paso 1: Ir a admincontactos SIN el intercept y esperar Angular completo.
    # Esto garantiza que la sesion este estable antes de instalar el route.
    # Critico cuando la suite llega aqui tras un re-login (fixture supervisor_logueado).
    try:
        shared_page.goto(f"{base_url}/admincontactos", wait_until="commit", timeout=10000)
    except Exception:
        pass
    try:
        shared_page.locator(MENU_SUPERVISION).wait_for(state="visible", timeout=15000)
    except Exception:
        pass

    # Paso 2: Instalar el intercept DESPUES de que admincontactos cargo completamente.
    shared_page.route("**/signalr/**", _signalr_fix)
    try:
        _navegar_ntf(shared_page, base_url)
        yield
    finally:
        # unroute siempre — evita cuelgue en logout() si el setup fallo
        try:
            shared_page.unroute("**/signalr/**")
        except Exception:
            pass
        try:
            shared_page.goto(f"{base_url}/admincontactos",
                             wait_until="commit", timeout=10000)
        except Exception:
            pass


# ── Tests ──────────────────────────────────────────────────────────────────

class TestNotificarUsuarios:

    def test_NTF001_A_carga_correctamente(self, shared_page: Page, base_url: str):
        assert "MensajesUsuarios" in shared_page.url
        shared_page.locator(PANEL).wait_for(state="visible", timeout=T)

    def test_NTF001_B_formulario_presente(self, shared_page: Page):
        shared_page.locator(FORM).wait_for(state="visible", timeout=T)
        assert shared_page.locator(ASUNTO).is_visible()
        assert shared_page.locator(MENSAJE).is_visible()

    def test_NTF001_C_radio_ahora_activo_por_defecto(self, shared_page: Page):
        radio = shared_page.locator(RADIO_AHORA)
        radio.wait_for(state="visible", timeout=T)
        assert shared_page.evaluate(
            f"document.querySelector('{RADIO_AHORA}').checked"
        ), "El radio 'Ahora' debe estar seleccionado por defecto"

    def test_NTF001_D_otro_momento_muestra_fecha(self, shared_page: Page):
        otro = shared_page.locator(RADIO_OTRO)
        otro.wait_for(state="visible", timeout=T)
        shared_page.evaluate(f"document.querySelector('{RADIO_OTRO}').click()")
        time.sleep(0.5)
        dt = shared_page.locator(DATETIME_OTRO)
        assert dt.count() > 0, "#datetimeOtroMomento no encontrado en el DOM"
        shared_page.evaluate(f"document.querySelector('{RADIO_AHORA}').click()")

    def test_NTF001_E_select_cliente_tiene_opciones(self, shared_page: Page):
        select = shared_page.locator(SELECT_CLIENTE)
        select.wait_for(state="visible", timeout=T)
        opciones = shared_page.evaluate(
            f"document.querySelector('{SELECT_CLIENTE}').options.length"
        )
        assert opciones > 0, f"El select de cliente no tiene opciones (tiene {opciones})"

    def test_NTF001_F_lista_usuarios_tiene_destinatarios(self, shared_page: Page):
        lista = shared_page.locator(LISTA_USUARIOS)
        lista.wait_for(state="visible", timeout=T)
        items = shared_page.evaluate(
            f"document.querySelector('{LISTA_USUARIOS}').querySelectorAll('option, li, input[type=checkbox]').length"
        )
        assert items > 0, f"La lista de usuarios no tiene destinatarios (tiene {items})"

    def test_NTF001_G_tabla_historial_presente(self, shared_page: Page):
        tabla = shared_page.locator(TABLA_HISTORIAL)
        tabla.wait_for(state="visible", timeout=T)
        assert tabla.is_visible()

    def test_NTF001_H_campos_aceptan_texto(self, shared_page: Page):
        asunto = shared_page.locator(ASUNTO)
        mensaje = shared_page.locator(MENSAJE)
        asunto.wait_for(state="visible", timeout=T)
        asunto.fill("Test automatizado NTF")
        assert asunto.input_value() == "Test automatizado NTF"
        mensaje.fill("Mensaje de prueba automatizado")
        assert mensaje.input_value() == "Mensaje de prueba automatizado"
        asunto.fill("")
        mensaje.fill("")

    def test_NTF001_I_boton_refresh_historial_presente(self, shared_page: Page):
        btn = shared_page.locator(BTN_REFRESH)
        btn.wait_for(state="visible", timeout=T)
        assert btn.is_visible()
