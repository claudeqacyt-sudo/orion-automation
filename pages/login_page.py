"""
login_page.py — Page Object para la pantalla de Login de Orion Contact Center
Selectores verificados contra HTML real de Orion v7.0 (vm-2k22-er-01.orioncontactcenter.com.ar)
"""
import re
import time
from playwright.sync_api import Page, expect
from pages.base_page import BasePage


# Texto parcial del modal de sesión activa en Orion v7.0
SESSION_ACTIVE_MSG = "ya se encuentra con una sesi"


class LoginPage(BasePage):
    """Page Object para la pantalla de login."""

    # ── Selectores verificados contra HTML real ──────────────────────
    INPUT_USERNAME   = "#usuario-login"
    INPUT_PASSWORD   = "#pass-login"
    BTN_LOGIN        = "#boton_ingresar"

    # Modal genérico de Orion (errores de login, sesión activa, etc.)
    MODAL_INFO       = "#modalGlobalGenericoInfo"
    MODAL_MSG        = "#modalGlobalGenericoInfo_leyenda"
    MODAL_OK_BTN     = "#modalGlobalGenericoInfo_btnOK"

    # Logout — el link está en el dropdown de usuario
    BTN_LOGOUT       = "#btnLogout"
    USER_DROPDOWN    = ".dropdown-toggle"

    # URL esperada post-login (app SPA que navega a /admincontactos)
    URL_POST_LOGIN   = "/admincontactos"

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate(self, base_url: str):
        """Ir a la página de login."""
        self.page.goto(f"{base_url.rstrip('/')}/login")
        self.wait_for_load()
        self.page.locator(self.INPUT_USERNAME).wait_for(state="visible", timeout=10000)

    def _get_modal_message(self) -> str | None:
        """
        Retorna el texto del modal genérico de Orion si está activo, None si no.
        Maneja excepciones de contexto destruido (navegación en curso).
        """
        try:
            modal = self.page.query_selector(self.MODAL_INFO)
            if not modal:
                return None
            cls = modal.get_attribute("class") or ""
            if "in" not in cls.split():
                return None
            return self.page.locator(self.MODAL_MSG).inner_text(timeout=2000).strip()
        except Exception as e:
            err = str(e).lower()
            if "context was destroyed" in err or "navigation" in err or "target closed" in err:
                return None  # La página está navegando → login exitoso
            raise

    def login(self, username: str, password: str):
        """
        Completar el formulario de login y enviar.

        Comportamientos:
        - Login exitoso  → URL cambia a /admincontactos → retorna normalmente.
        - Sesión activa  → RuntimeError (el test/fixture maneja el retry).
        - Creds inválidas → modal con error → cierra el modal → retorna (sin navegar).
        """
        self.page.locator(self.INPUT_USERNAME).fill(username)
        self.page.locator(self.INPUT_PASSWORD).fill(password)
        self.page.locator(self.BTN_LOGIN).click()

        # Esperar hasta 15 seg a que la URL cambie o aparezca un modal
        deadline = time.time() + 15
        while time.time() < deadline:
            # 1. Verificar si el login fue exitoso (URL cambió)
            try:
                if self.URL_POST_LOGIN in self.page.url:
                    return  # ✅ Login exitoso
            except Exception:
                pass

            # 2. Verificar si apareció un modal
            modal_msg = self._get_modal_message()

            if modal_msg is not None:
                if SESSION_ACTIVE_MSG in modal_msg:
                    # ❌ Sesión activa del mismo usuario
                    raise RuntimeError(
                        f"Sesión activa detectada: {modal_msg}. "
                        "Esperar ~130 seg o cerrar la sesión antes de continuar."
                    )
                else:
                    # ⚠ Otro error (creds incorrectas, usuario no existe, etc.)
                    # El modal informa el error; cerrarlo y retornar
                    try:
                        self.page.locator(self.MODAL_OK_BTN).click(timeout=3000)
                    except Exception:
                        pass
                    return

            time.sleep(0.4)

        # Verificar una última vez (puede que el login tardó más de 15 seg)
        if self.URL_POST_LOGIN in self.page.url:
            return

    def verify_logged_in(self):
        """Verificar que el login fue exitoso (URL contiene /admincontactos)."""
        expect(self.page).to_have_url(
            re.compile(r"/admincontactos"),
            timeout=self.timeout,
        )

    def verify_login_error(self):
        """
        Verificar que el login falló.
        El formulario de login sigue visible (no navegó al dashboard).
        """
        expect(self.page.locator(self.INPUT_USERNAME)).to_be_visible(timeout=10000)
        assert self.URL_POST_LOGIN not in self.page.url, \
            f"Se esperaba fallo de login pero la URL es: {self.page.url}"

    def logout(self):
        """
        Cerrar sesión.

        Estrategia:
        1. Intentar clic real en el .dropdown-toggle (visible) para abrir el menú.
        2. Esperar a que #btnLogout sea visible.
        3. Clic real en #btnLogout (isTrusted=true vía Playwright, no via JS evaluate).
        4. Si la URL no cambia a /login en 10 seg, forzar navegación a /login.
        """
        # Paso 1: Abrir el dropdown del usuario
        try:
            # Tomar el primer .dropdown-toggle visible (menú de usuario con el nombre)
            toggles = self.page.locator(self.USER_DROPDOWN).all()
            for toggle in toggles:
                if toggle.is_visible():
                    toggle.click()
                    time.sleep(0.6)
                    break
        except Exception:
            pass

        # Paso 2: Click real en #btnLogout (con force=True para ignorar visibilidad)
        try:
            self.page.locator(self.BTN_LOGOUT).click(force=True, timeout=5000)
        except Exception:
            pass

        # Paso 3: Esperar a que la URL cambie a /login
        try:
            expect(self.page).to_have_url(re.compile(r"/login"), timeout=8000)
            return
        except Exception:
            pass

        # Paso 4: Si el click no funcionó, intentar navegación directa
        try:
            origin = self.page.evaluate("() => window.location.origin")
            self.page.goto(f"{origin}/login", timeout=15000)
            time.sleep(2)
        except Exception:
            time.sleep(2)
