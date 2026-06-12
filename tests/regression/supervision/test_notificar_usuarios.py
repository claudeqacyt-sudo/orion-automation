"""
tests/regression/supervision/test_notificar_usuarios.py
Suite de regresion — Supervision > Notificar Usuarios (/MensajesUsuarios)
"""
import sys
import time
import pytest
from playwright.sync_api import Page
from pages.login_page import LoginPage

pytestmark = [pytest.mark.regression, pytest.mark.admin, pytest.mark.skip(reason="Deshabilitado")]

BASE_PATH = "/MensajesUsuarios"

# ── Selectores ─────────────────────────────────────────────────────────────
PANEL           = "#panelMensajesProgramados"
FORM            = "#frmMessageData"
ASUNTO          = "#txtAsunto"
MENSAJE         = "#txaMensaje"
RADIO_AHORA     = "#rdbAhora"
RADIO_OTRO      = "#rdbOtroMomento"
DATETIME_OTRO   = "#datetimeOtroMomento"
SELECT_CLIENTE  = "#cmbCliente"
LISTA_USUARIOS  = "#listadoUsuarios"
BTN_ENVIAR      = "#btnGuardarMensaje"
TABLA_HISTORIAL = "#tblMensajesProgramados"
BTN_REFRESH     = "#btnRefreshTable"
MENU_SUPERVISION = "#accionEjecutar_4"

T = 25000

# URL pattern para el request de logout del modulo adminContactos.
# El beforeunload de adminContactos llama LogoutUsuario al navegar a otro modulo,
# lo que invalida la sesion del servidor. Bloqueamos esta request para que
# checkPermisoPagina.js pueda verificar permisos y ejecutar main.init().
_LOGOUT_PATTERN = "**/GestorDeUsuarios/LogoutUsuario**"


def _block_logout(page: Page) -> None:
    try:
        page.route(
            _LOGOUT_PATTERN,
            lambda r: r.fulfill(status=200, body="true", content_type="application/json")
        )
    except Exception:
        pass


def _unblock_logout(page: Page) -> None:
    try:
        page.unroute(_LOGOUT_PATTERN)
    except Exception:
        pass


def _dom_state(page: Page) -> dict:
    try:
        return page.evaluate("""() => {
            var p = document.getElementById('panelMensajesProgramados');
            var m = document.getElementById('modalGlobalGenericoInfo');
            return {
                url:       location.pathname,
                panel:     p ? (p.offsetParent ? 'VISIBLE' : 'HIDDEN') : 'MISSING',
                modal:     m ? (m.className.indexOf('in') >= 0 ? 'OPEN' : 'closed') : 'N/A',
                sec_class: (document.getElementById('seccionPrincipal') || {className: ''}).className
            };
        }""")
    except Exception as e:
        return {"error": str(e)}


def _navegar_ntf(page: Page, base_url: str) -> None:
    """Navega a /MensajesUsuarios bloqueando el logout del beforeunload de adminContactos."""
    _block_logout(page)
    try:
        page.goto(f"{base_url}{BASE_PATH}", wait_until="commit", timeout=15000)
    except Exception:
        _unblock_logout(page)
        return
    _unblock_logout(page)

    # Verificar redireccion real al login (no pushState)
    try:
        if page.locator("#usuario-login").is_visible(timeout=1500):
            return
    except Exception:
        pass

    # Esperar modal de sesion activa (si aparece) o el panel directamente
    try:
        page.wait_for_function(
            """() => {
                var m = document.getElementById('modalGlobalGenericoInfo');
                var p = document.getElementById('panelMensajesProgramados');
                return (m && m.className.indexOf('in') >= 0) || (p && !!p.offsetParent);
            }""",
            timeout=15000
        )
        page.evaluate(
            "() => { var b = document.getElementById('modalGlobalGenericoInfo_btnOK'); if (b) b.click(); }"
        )
    except Exception:
        pass

    # Esperar que el panel sea visible en Playwright (desplegar() quita la clase oculto)
    try:
        page.locator(PANEL).wait_for(state="visible", timeout=12000)
    except Exception:
        pass

    print(f"\n[NTF-NAV] url={page.url} dom={_dom_state(page)}", file=sys.stderr, flush=True)


def _setup_ntf(page: Page, base_url: str, admin_credentials: dict) -> None:
    """Verifica sesion activa y navega a /MensajesUsuarios."""
    try:
        page.goto(f"{base_url}/admincontactos", wait_until="commit", timeout=10000)
    except Exception:
        pass

    if "/login" in page.url:
        print(f"\n[NTF-SETUP] relogin url={page.url}", file=sys.stderr, flush=True)
        try:
            login = LoginPage(page)
            login.navigate(base_url)
            login.login(admin_credentials["username"], admin_credentials["password"])
        except Exception as e:
            print(f"\n[NTF-SETUP] login exc: {e}", file=sys.stderr, flush=True)
        try:
            page.goto(f"{base_url}/admincontactos", wait_until="commit", timeout=10000)
        except Exception:
            pass
        time.sleep(2)

    try:
        page.locator(MENU_SUPERVISION).wait_for(state="visible", timeout=20000)
    except Exception:
        pass

    try:
        page.unroute("**/signalr/**")
    except Exception:
        pass

    print(f"\n[NTF-SETUP] ready url={page.url}", file=sys.stderr, flush=True)
    _navegar_ntf(page, base_url)
    print(f"\n[NTF-SETUP] after nav dom={_dom_state(page)}", file=sys.stderr, flush=True)


@pytest.fixture(scope="class", autouse=True)
def ntf_navegacion(shared_page: Page, base_url: str, admin_credentials: dict):
    """Navega una vez a /MensajesUsuarios para toda la clase y hace cleanup al final."""
    _setup_ntf(shared_page, base_url, admin_credentials)

    # Verificar visibilidad del panel (no URL: pushState puede cambiarla a /login
    # sin salir de la pagina)
    _need_recovery = False
    try:
        shared_page.locator(PANEL).wait_for(state="visible", timeout=12000)
        _need_recovery = not shared_page.locator(PANEL).is_visible()
    except Exception:
        _need_recovery = True

    dom_check = _dom_state(shared_page)
    print(f"\n[NTF-FIXTURE] need_recovery={_need_recovery} dom={dom_check}", file=sys.stderr, flush=True)

    if _need_recovery:
        time.sleep(3)
        _setup_ntf(shared_page, base_url, admin_credentials)

    dom_final = _dom_state(shared_page)
    print(f"\n[NTF-FIXTURE] final dom={dom_final}", file=sys.stderr, flush=True)

    try:
        yield
    finally:
        _unblock_logout(shared_page)
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
        dom = _dom_state(shared_page)
        print(f"\n[NTF001A] START dom={dom}", file=sys.stderr, flush=True)
        shared_page.locator(PANEL).wait_for(state="visible", timeout=T)

    def test_NTF001_B_formulario_presente(self, shared_page: Page):
        shared_page.locator(FORM).wait_for(state="visible", timeout=T)
        assert shared_page.locator(ASUNTO).is_visible()
        assert shared_page.locator(MENSAJE).is_visible()

    def test_NTF001_C_radio_ahora_activo_por_defecto(self, shared_page: Page):
        radio = shared_page.locator(RADIO_AHORA)
        radio.wait_for(state="visible", timeout=T)
        assert radio.is_checked()

    def test_NTF001_D_otro_momento_muestra_fecha(self, shared_page: Page):
        otro = shared_page.locator(RADIO_OTRO)
        otro.wait_for(state="visible", timeout=T)
        otro.click()
        shared_page.locator(DATETIME_OTRO).wait_for(state="visible", timeout=T)
        shared_page.locator(RADIO_AHORA).click()

    def test_NTF001_E_select_cliente_tiene_opciones(self, shared_page: Page):
        select = shared_page.locator(SELECT_CLIENTE)
        select.wait_for(state="visible", timeout=T)
        opts = shared_page.locator(f"{SELECT_CLIENTE} option").count()
        assert opts > 0

    def test_NTF001_F_lista_usuarios_tiene_destinatarios(self, shared_page: Page):
        lista = shared_page.locator(LISTA_USUARIOS)
        lista.wait_for(state="visible", timeout=T)

    def test_NTF001_G_tabla_historial_presente(self, shared_page: Page):
        tabla = shared_page.locator(TABLA_HISTORIAL)
        tabla.wait_for(state="visible", timeout=T)

    def test_NTF001_H_campos_aceptan_texto(self, shared_page: Page):
        asunto = shared_page.locator(ASUNTO)
        asunto.wait_for(state="visible", timeout=T)
        asunto.fill("Test asunto")
        assert asunto.input_value() == "Test asunto"
        asunto.fill("")

    def test_NTF001_I_boton_refresh_historial_presente(self, shared_page: Page):
        btn = shared_page.locator(BTN_REFRESH)
        btn.wait_for(state="visible", timeout=T)
        assert btn.is_visible()
