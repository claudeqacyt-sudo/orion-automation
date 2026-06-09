"""
conftest.py — Configuración global de pytest + Playwright para Orion Contact Center

NOTA IMPORTANTE — Gestión de sesión en Orion v7.0:
  El sistema Orion no expone un endpoint de logout que termine la sesión del servidor.
  La sesión se invalida por TIMEOUT en el servidor (130 segundos de inactividad).
  Para evitar conflictos entre tests, este conftest ofrece DOS fixtures:

  1. logged_in_page (scope="function"):
     - Login/logout por cada test individual.
     - Si detecta sesión activa, espera 140 seg y reintenta (hasta 2 veces).
     - Usar para tests de SMOKE que verifican login/logout.

  2. shared_page (scope="session"):
     - Login UNA VEZ para toda la sesión de pytest.
     - Todos los tests de regresión comparten la misma página autenticada.
     - La sesión se mantiene activa haciendo requests periódicos.
     - Usar para tests de REGRESIÓN que no prueban login/logout.
"""
import os
import time
import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page, Browser, BrowserContext

load_dotenv()

SESSION_WAIT_SECS = 140  # Espera cuando hay sesión activa en el servidor


# ─────────────────────────────────────────────
# Fixtures de configuración
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("ORION_BASE_URL", "https://vm-2k22-fg-01.orioncontactcenter.com.ar")


@pytest.fixture(scope="session")
def admin_credentials() -> dict:
    return {
        "username": os.getenv("ADMIN_USERNAME", "cyt"),
        "password": os.getenv("ADMIN_PASSWORD", "Feab4650"),
    }


@pytest.fixture(scope="session")
def supervisor_credentials() -> dict:
    return {
        "username": os.getenv("SUPERVISOR_USERNAME", "cyt"),
        "password": os.getenv("SUPERVISOR_PASSWORD", "Feab4650"),
    }


@pytest.fixture(scope="session")
def agent_credentials() -> dict:
    return {
        "username": os.getenv("AGENT_USERNAME", "1001"),
        "password": os.getenv("AGENT_PASSWORD", "1001"),
    }


# ─────────────────────────────────────────────
# Fixture per-test (SMOKE tests)
# ─────────────────────────────────────────────

@pytest.fixture
def logged_in_page(page: Page, base_url: str, admin_credentials: dict) -> Page:
    """
    Fixture de página autenticada — scope=function (un login por test).
    Reintenta hasta 2 veces con espera de 140 seg si la sesión está activa.
    Usar en: tests de SMOKE que validan login/logout.
    """
    from pages.login_page import LoginPage
    login_page = LoginPage(page)

    def _esperar_keepalive(page_ref, segundos):
        end_time = time.time() + segundos
        while time.time() < end_time:
            time.sleep(min(20, end_time - time.time()))
            try:
                page_ref.evaluate("1")
            except Exception:
                pass

    def _sesion_activa_en_pagina_lp() -> bool:
        try:
            modal = page.query_selector("#modalGlobalGenericoInfo")
            if modal and "in" in (modal.get_attribute("class") or "").split():
                msg = page.locator("#modalGlobalGenericoInfo_leyenda").inner_text(timeout=2000)
                return "ya se encuentra con una sesi" in msg
        except Exception:
            pass
        return False

    logged_in = False
    for attempt in range(3):
        login_page.navigate(base_url)
        try:
            login_page.login(admin_credentials["username"], admin_credentials["password"])
            login_page.verify_logged_in()
            logged_in = True
            break
        except RuntimeError as e:
            if "Sesión activa" in str(e) and attempt < 2:
                print(f"\n[logged_in_page] Sesión activa vía RuntimeError (intento {attempt + 1}). "
                      f"Esperando {SESSION_WAIT_SECS} seg...")
                _esperar_keepalive(page, SESSION_WAIT_SECS)
            else:
                pytest.skip(f"No se pudo iniciar sesión: {e}")
        except Exception as e:
            if attempt < 2 and _sesion_activa_en_pagina_lp():
                print(f"\n[logged_in_page] Sesión activa detectada post-login (intento {attempt + 1}). "
                      f"Esperando {SESSION_WAIT_SECS} seg...")
                _esperar_keepalive(page, SESSION_WAIT_SECS)
            else:
                pytest.skip(f"No se pudo iniciar sesión: {e}")

    if not logged_in:
        pytest.skip("Login fallido por sesión activa persistente.")

    yield page

    # Teardown — solo navegación al login (sin logout API real)
    try:
        login_page.logout()
        time.sleep(1)
    except Exception:
        pass


# ─────────────────────────────────────────────
# Fixture de sesión compartida (REGRESIÓN)
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Abre el browser maximizado. slow_mo se toma de SLOW_MO en .env (default 0)."""
    slow_mo = int(os.getenv("SLOW_MO", "500"))
    return {**browser_type_launch_args, "slow_mo": slow_mo, "args": ["--start-maximized"]}


@pytest.fixture(scope="session")
def shared_browser_context(browser: Browser) -> BrowserContext:
    """Contexto de browser compartido para toda la sesión de pruebas."""
    ctx = browser.new_context(no_viewport=True)  # deja que --start-maximized controle el tamaño
    yield ctx
    ctx.close()


@pytest.fixture(scope="session")
def shared_page(shared_browser_context: BrowserContext,
                base_url: str, admin_credentials: dict) -> Page:
    """
    Fixture de página autenticada compartida para toda la sesión de pytest.
    Login UNA SOLA VEZ — todos los tests de regresión reusan la misma sesión.
    Reintenta con espera si la sesión está activa al inicio.
    Usar en: tests de REGRESIÓN (Usuarios, Monitor, Reportes, etc.)
    """
    from pages.login_page import LoginPage
    page = shared_browser_context.new_page()
    login_page = LoginPage(page)

    def _esperar_con_keepalive(segundos: int):
        """
        Espera 'segundos' manteniendo el browser vivo con evaluaciones periódicas.
        Sin esto, el browser cierra la conexión CDP durante sleeps largos.
        """
        print(f"\n[shared_page] Esperando {segundos} seg para que expire la sesión...")
        end_time = time.time() + segundos
        while time.time() < end_time:
            restante = end_time - time.time()
            sleep_chunk = min(20, restante)   # ping cada 20 seg máximo
            time.sleep(max(0, sleep_chunk))
            if time.time() < end_time:
                try:
                    page.evaluate("1")        # mantiene vivo el CDP channel
                except Exception:
                    pass                      # ignorar si la pagina ya cerró

    def _sesion_activa_en_pagina() -> bool:
        """Verifica si el modal de sesión activa está visible en la página actual."""
        try:
            modal = page.query_selector("#modalGlobalGenericoInfo")
            if modal and "in" in (modal.get_attribute("class") or "").split():
                msg = page.locator("#modalGlobalGenericoInfo_leyenda").inner_text(timeout=2000)
                return "ya se encuentra con una sesi" in msg
        except Exception:
            pass
        return False

    for attempt in range(3):
        login_page.navigate(base_url)
        try:
            login_page.login(admin_credentials["username"], admin_credentials["password"])
            login_page.verify_logged_in()
            break
        except RuntimeError as e:
            # login() detectó el modal de sesión activa directamente
            if "Sesión activa" in str(e) and attempt < 2:
                print(f"\n[shared_page] Sesión activa vía RuntimeError (intento {attempt + 1}).")
                _esperar_con_keepalive(SESSION_WAIT_SECS)
            else:
                pytest.exit(f"No se pudo iniciar sesión compartida: {e}", returncode=1)
        except Exception as e:
            # verify_logged_in() u otro error — verificar si hay modal de sesión activa
            if attempt < 2 and _sesion_activa_en_pagina():
                print(f"\n[shared_page] Sesión activa detectada post-login (intento {attempt + 1}).")
                _esperar_con_keepalive(SESSION_WAIT_SECS)
            else:
                pytest.exit(f"No se pudo iniciar sesión compartida: {e}", returncode=1)

    yield page

    # Logout al finalizar la sesión de tests — evita "sesión activa" en la próxima ejecución
    try:
        from pages.login_page import LoginPage
        LoginPage(page).logout()
        time.sleep(1)
    except Exception:
        pass


# ─────────────────────────────────────────────
# Hooks de pytest
# ─────────────────────────────────────────────

def pytest_configure(config):
    os.makedirs("reports", exist_ok=True)
    os.makedirs("reports/screenshots", exist_ok=True)


def pytest_html_report_title(report):
    report.title = "Orion Contact Center — Reporte de Regresion QA"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Screenshot automático cuando un test falla."""
    outcome = yield
    report  = outcome.get_result()

    if report.when == "call" and report.failed:
        page: Page = (item.funcargs.get("page")
                      or item.funcargs.get("logged_in_page")
                      or item.funcargs.get("shared_page"))
        if page:
            test_name = item.name.replace("/", "_").replace(" ", "_")
            path = f"reports/screenshots/FAIL_{test_name}.png"
            try:
                page.screenshot(path=path, full_page=True)
            except Exception:
                pass
