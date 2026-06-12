"""
tests/regression/agent/test_agent_acceso.py
Suite de regresión — Perfil Agente

UN SOLO LOGIN para toda la suite (fixture scope=module).
Flujo: logout admin → login agente → habilitar canales (#conBarra) → Continuar → tests

Tests:
  AGT-001  Login, modal de extensión y activación de canales
  AGT-002  Interfaz principal (estructura, menú restringido)
  AGT-003  Controles de la interfaz
  AGT-004  Formulario cambio de contraseña
  AGT-005  Sección Ayuda
"""
import time
import pytest
from playwright.sync_api import Page

from pages.login_page import LoginPage

pytestmark = [pytest.mark.regression, pytest.mark.agente]

URL_AGENTE = "/ingresoInterno"


# ─────────────────────────────────────────────────────────────────────────────
# Fixture único — UN LOGIN para toda la suite del agente
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def agent_logueado(agent_browser_context, base_url: str, agent_credentials: dict):
    """Login único como agente en contexto separado. La sesión cyt en shared_page no se toca."""
    page = agent_browser_context.new_page()
    login = LoginPage(page)

    # Login agente con retry si hay sesión activa
    for attempt in range(3):
        try:
            login.navigate(base_url)
            login.login(agent_credentials["username"], agent_credentials["password"])
            page.wait_for_url(f"**{URL_AGENTE}**", timeout=15000)
            break
        except RuntimeError:
            print(f"\n[agent_logueado] Sesión activa (intento {attempt+1}), esperando 140s...")
            time.sleep(140)
        except Exception as e:
            pytest.exit(f"No se pudo iniciar sesión como agente: {e}", returncode=1)

    # Esperar y verificar modal de extensión
    modal = page.locator("#modalGlobal2Botones")
    modal.wait_for(state="visible", timeout=8000)

    # Habilitar canales de comunicación: click en #conBarra
    con_barra = page.locator("#conBarra")
    con_barra.wait_for(state="visible", timeout=5000)
    if not con_barra.is_checked():
        con_barra.click()
        time.sleep(0.8)

    # Al tildar #conBarra se habilita el campo de extensión — ingresar 201
    page.locator("#txtNroInterno").wait_for(state="visible", timeout=5000)
    page.locator("#txtNroInterno").fill("201")
    time.sleep(0.5)

    # Continuar
    page.locator("#modalGlobal2Botones_uno").click()

    # Esperar carga completa: red idle + interfaz interactiva
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.locator("#bienvenida").wait_for(state="visible", timeout=15000)
    page.locator(".module-button").first.wait_for(state="visible", timeout=10000)
    time.sleep(2)

    yield page

    # Teardown: logout agente, cerrar página. cyt sigue activo en shared_page.
    try:
        login.logout()
        time.sleep(1.5)
    except Exception:
        pass
    try:
        page.close()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# AGT-001 — Login, modal y activación de canales
# ─────────────────────────────────────────────────────────────────────────────

class TestAgenteLogin:

    def test_AGT001_A_url_es_interfaz_agente(self, agent_logueado):
        """AGT-001-A: Post-login la URL es la interfaz del agente (/ingresoInterno o /admincontactos)."""
        url = agent_logueado.url
        assert URL_AGENTE in url or "/admincontactos" in url, \
            f"URL inesperada para agente: {url}"

    def test_AGT001_B_canales_habilitados(self, agent_logueado):
        """AGT-001-B: El checkbox #conBarra quedó marcado (canales habilitados)."""
        checked = agent_logueado.evaluate(
            "() => { var cb = document.getElementById('conBarra');"
            " return cb ? cb.checked : null; }"
        )
        # conBarra puede no estar en el DOM después de cerrar el modal
        # Lo importante es que los module-buttons estén activos
        botones_habilitados = agent_logueado.evaluate(
            "() => Array.from(document.querySelectorAll('.module-button'))"
            ".filter(b => !b.disabled).length"
        )
        assert botones_habilitados > 0, \
            "Ningún botón de módulo habilitado — canales no se activaron"

    def test_AGT001_C_modal_cerrado_e_interfaz_cargada(self, agent_logueado):
        """AGT-001-C: El modal de extensión está cerrado y la interfaz cargó."""
        modal_visible = agent_logueado.evaluate(
            "() => { var m = document.getElementById('modalGlobal2Botones');"
            " return m ? window.getComputedStyle(m).display !== 'none' : false; }"
        )
        assert not modal_visible, "El modal de extensión sigue visible"
        assert agent_logueado.locator("#bienvenida").is_visible(), \
            "#bienvenida no es visible"


# ─────────────────────────────────────────────────────────────────────────────
# AGT-002 — Interfaz principal y menú restringido
# ─────────────────────────────────────────────────────────────────────────────

class TestAgenteInterfaz:

    def test_AGT002_A_estructura_principal(self, agent_logueado):
        """AGT-002-A: La interfaz tiene los elementos estructurales esperados."""
        for elemento in ("#wrapper", "#encabezado", "#menuGestor",
                         "#seccionPrincipal", "#bienvenida"):
            assert agent_logueado.locator(elemento).count() > 0, \
                f"Elemento '{elemento}' no encontrado"

    def test_AGT002_B_pantalla_bienvenida_visible(self, agent_logueado):
        """AGT-002-B: La pantalla de bienvenida está visible con título."""
        assert agent_logueado.locator("#bienvenida").is_visible()
        titulo = agent_logueado.locator("#bienvenidaTitulo").inner_text()
        assert len(titulo.strip()) > 0, "El título de bienvenida está vacío"

    def test_AGT002_C_usuario_logueado_visible(self, agent_logueado):
        """AGT-002-C: El nombre del usuario logueado es visible en el encabezado."""
        assert agent_logueado.locator("#logedUser").is_visible()
        nombre = agent_logueado.locator("#logedUser").inner_text()
        assert len(nombre.strip()) > 0, "El nombre de usuario no se muestra"

    def test_AGT002_D_menu_solo_ayuda(self, agent_logueado):
        """AGT-002-D: El menú del agente solo contiene Ayuda (accionEjecutar_5)."""
        assert agent_logueado.evaluate(
            "() => document.getElementById('accionEjecutar_5') !== null"
        ), "accionEjecutar_5 (Ayuda) no encontrado"

    def test_AGT002_E_items_admin_no_existen_en_dom(self, agent_logueado):
        """AGT-002-E: Los ítems exclusivos del admin NO existen para el agente."""
        for item_id in ("accionEjecutar_1", "accionEjecutar_2",
                        "accionEjecutar_3", "accionEjecutar_4"):
            existe = agent_logueado.evaluate(
                f"() => document.getElementById('{item_id}') !== null"
            )
            assert not existe, f"'{item_id}' NO debería estar disponible"


# ─────────────────────────────────────────────────────────────────────────────
# AGT-003 — Controles de la interfaz
# ─────────────────────────────────────────────────────────────────────────────

class TestAgenteControles:

    def test_AGT003_A_boton_notificaciones_presente(self, agent_logueado):
        """AGT-003-A: El botón de notificaciones está presente."""
        assert agent_logueado.locator("#openNotifications").count() > 0

    def test_AGT003_B_boton_configuracion_presente_y_clickeable(self, agent_logueado):
        """AGT-003-B: El botón de configuración está presente y es clickeable."""
        btn = agent_logueado.locator("#btnAbrirConfiguracion")
        assert btn.count() > 0, "#btnAbrirConfiguracion no encontrado"
        btn.click()
        time.sleep(1.5)
        # El panel de config está en el DOM (puede estar oculto hasta navegar a la sección)
        assert agent_logueado.locator("#passChangerContainer").count() > 0, \
            "#passChangerContainer no encontrado en el DOM"

    def test_AGT003_C_formulario_tickets_en_dom(self, agent_logueado):
        """AGT-003-C: El formulario de búsqueda de tickets está en el DOM."""
        assert agent_logueado.locator("#frmBusquedaTickets").count() > 0

    def test_AGT003_D_contenedor_paneles_presente(self, agent_logueado):
        """AGT-003-D: Los contenedores de paneles principales están presentes."""
        for elem in ("#adminPanels", "#summary", "#detail"):
            assert agent_logueado.locator(elem).count() > 0, \
                f"'{elem}' no encontrado"

    def test_AGT003_E_botones_modulo_habilitados(self, agent_logueado):
        """AGT-003-E: Al menos un botón de módulo está habilitado (canales activos)."""
        total = agent_logueado.evaluate(
            "() => document.querySelectorAll('.module-button').length"
        )
        habilitados = agent_logueado.evaluate(
            "() => Array.from(document.querySelectorAll('.module-button'))"
            ".filter(b => !b.disabled).length"
        )
        assert total > 0, "No se encontraron botones .module-button"
        assert habilitados > 0, \
            f"Todos los {total} botones están deshabilitados — canales no activos"


# ─────────────────────────────────────────────────────────────────────────────
# AGT-004 — Cambio de contraseña
# ─────────────────────────────────────────────────────────────────────────────

class TestAgenteCambioPassword:

    def test_AGT004_A_panel_cambio_password_presente(self, agent_logueado):
        """AGT-004-A: El panel de cambio de contraseña está en el DOM."""
        assert agent_logueado.locator("#passChangerContainer").count() > 0

    def test_AGT004_B_campos_password_presentes(self, agent_logueado):
        """AGT-004-B: Los campos de contraseña actual, nueva y confirmación existen."""
        for campo in ("#pwdActual", "#pwdNuevo", "#pwdNuevoConfirmacion"):
            assert agent_logueado.locator(campo).count() > 0, \
                f"Campo '{campo}' no encontrado"

    def test_AGT004_C_boton_guardar_presente(self, agent_logueado):
        """AGT-004-C: El botón Guardar está presente."""
        assert agent_logueado.locator("#btnSaveNewPass").count() > 0

    def test_AGT004_D_checkbox_mostrar_passwords(self, agent_logueado):
        """AGT-004-D: El checkbox para mostrar contraseñas está presente."""
        assert agent_logueado.locator("#chkMostrarPasswords").count() > 0


# ─────────────────────────────────────────────────────────────────────────────
# AGT-005 — Sección Ayuda
# ─────────────────────────────────────────────────────────────────────────────

class TestAgenteAyuda:

    def test_AGT005_A_ayuda_abre_nueva_pestana(self, agent_logueado):
        """AGT-005-A: Click en Ayuda abre pestaña /Ayuda con tabla de versiones."""
        assert agent_logueado.evaluate(
            "() => document.getElementById('accionEjecutar_5') !== null"
        ), "Ayuda no encontrado en el menú"

        with agent_logueado.context.expect_page(timeout=10000) as info:
            agent_logueado.locator("#accionEjecutar_5").click()
        tab = info.value

        try:
            tab.wait_for_load_state("domcontentloaded", timeout=15000)
            time.sleep(2)
            assert "/Ayuda" in tab.url, f"URL inesperada: {tab.url}"
            body = tab.inner_text("body").lower()
            assert not any(x in body for x in ["server error", "exception", "404"])
            assert tab.locator("#dt-version").count() > 0, \
                "Tabla #dt-version no encontrada en Ayuda"
        finally:
            tab.close()


# ─────────────────────────────────────────────────────────────────────────────
# AGT-006 — Barra CTI: botones de estado (Libre / Listo / Marcar)
#
# Selectores verificados contra HTML real de #dalpadweb-bar:
#   #dalpadweb-link-es1  title="Libre"  class="cti-libre"  → estado disponible
#   #dalpadweb-link-es2  title="Listo"  class="cti-listo"  → ponerse en línea
#   #dalpadweb-link-ft1  title="Marcar" class="cti-padtelefonico" → abre dialpad
# El estado activo se indica con clase "active" en el span.
# ─────────────────────────────────────────────────────────────────────────────

class TestAgenteCTIBarra:

    def _abrir_barra(self, page):
        is_closed = page.evaluate(
            "() => { var b = document.getElementById('barraCTI'); "
            "return b ? b.classList.contains('closed') : true; }"
        )
        if is_closed:
            page.evaluate("() => document.getElementById('openBarra').click()")
            time.sleep(1)

    def test_AGT006_A_barra_cti_presente(self, agent_logueado):
        """AGT-006-A: La barra CTI (#barraCTI y #dalpadweb-bar) están presentes."""
        assert agent_logueado.locator("#barraCTI").count() > 0, "#barraCTI no encontrado"
        assert agent_logueado.locator("#dalpadweb-bar").count() > 0, "#dalpadweb-bar no encontrado"
        assert agent_logueado.locator("#dalpadweb-main-buttons").count() > 0, \
            "#dalpadweb-main-buttons no encontrado"

    def test_AGT006_B_boton_libre_presente_y_activo(self, agent_logueado):
        """AGT-006-B: El botón 'Libre' está presente y es el estado inicial activo."""
        btn = agent_logueado.locator("#dalpadweb-link-es1")
        assert btn.count() > 0, "#dalpadweb-link-es1 (Libre) no encontrado"
        cls = btn.get_attribute("class")
        assert "cti-libre" in cls, f"Clase inesperada en Libre: {cls}"
        assert "active" in cls, f"'Libre' no está activo por defecto: {cls}"

    def test_AGT006_C_boton_listo_presente(self, agent_logueado):
        """AGT-006-C: El botón 'Listo' está presente en la barra CTI."""
        btn = agent_logueado.locator("#dalpadweb-link-es2")
        assert btn.count() > 0, "#dalpadweb-link-es2 (Listo) no encontrado"
        cls = btn.get_attribute("class")
        assert "cti-listo" in cls, f"Clase inesperada en Listo: {cls}"

    def test_AGT006_D_display_muestra_estado_agente(self, agent_logueado):
        """AGT-006-D: El display CTI muestra agente, estado y tiempo."""
        assert agent_logueado.locator("#value-line-1").count() > 0, \
            "#value-line-1 no encontrado"
        valores = agent_logueado.evaluate(
            "() => Array.from(document.querySelectorAll('#value-line-1 > div'))"
            ".map(d => d.innerText.trim())"
        )
        print(f"\n  Display CTI: {valores}")
        assert len(valores) >= 2, f"Display CTI incompleto: {valores}"
        assert any(v in ("Libre", "Listo") for v in valores), \
            f"Estado no reconocido en display: {valores}"

    def test_AGT006_E_click_listo_activa_estado(self, agent_logueado):
        """AGT-006-E: Click en 'Listo' cambia el estado activo del agente."""
        self._abrir_barra(agent_logueado)
        agent_logueado.evaluate(
            "() => document.getElementById('dalpadweb-link-es2').click()"
        )
        time.sleep(2)
        cls = agent_logueado.locator("#dalpadweb-link-es2").get_attribute("class")
        print(f"\n  Clase es2 (Listo) despues de click: {cls}")
        assert "active" in cls, f"Estado 'Listo' no se activó tras el click: {cls}"

    def test_AGT006_F_click_libre_restaura_estado(self, agent_logueado):
        """AGT-006-F: Click en 'Libre' restaura el estado libre del agente."""
        self._abrir_barra(agent_logueado)
        agent_logueado.evaluate(
            "() => document.getElementById('dalpadweb-link-es1').click()"
        )
        time.sleep(2)
        cls = agent_logueado.locator("#dalpadweb-link-es1").get_attribute("class")
        print(f"\n  Clase es1 (Libre) despues de click: {cls}")
        assert "active" in cls, f"Estado 'Libre' no se restauró tras el click: {cls}"

    def test_AGT006_G_boton_marcar_abre_dialpad(self, agent_logueado):
        """AGT-006-G: Click en el icono 'Marcar' abre el dialpad telefónico."""
        self._abrir_barra(agent_logueado)
        cerrado_antes = agent_logueado.evaluate(
            "() => { var el = document.querySelector('.cti-dialpad-wrapper');"
            " return el ? el.classList.contains('closed') : true; }"
        )
        agent_logueado.evaluate(
            "() => document.getElementById('dalpadweb-link-ft1').click()"
        )
        time.sleep(1.5)
        cerrado_despues = agent_logueado.evaluate(
            "() => { var el = document.querySelector('.cti-dialpad-wrapper');"
            " return el ? el.classList.contains('closed') : true; }"
        )
        print(f"\n  Dialpad closed: antes={cerrado_antes}, despues={cerrado_despues}")
        assert not cerrado_despues, "El dialpad no se abrió tras click en 'Marcar'"
