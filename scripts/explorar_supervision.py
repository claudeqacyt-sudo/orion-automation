"""
Explora el menu Supervision (accionEjecutar_4) y lista todos los sub-items
con su texto, visibilidad y la URL que abre cada uno en nueva pestana.

Ya cubiertos:
  accionEjecutar_43 -> Dashboards
  accionEjecutar_44 -> Frameworks
  accionEjecutar_45 -> Generador de Apps
"""
import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

BASE_URL  = os.getenv("ORION_BASE_URL", "https://VM-2K22-FG-01.orioncontactcenter.com.ar")
USER      = os.getenv("ADMIN_USERNAME", "cyt")
PASSWORD  = os.getenv("ADMIN_PASSWORD", "Feab4650")

CUBIERTOS = {"accionEjecutar_43", "accionEjecutar_44", "accionEjecutar_45"}


def login(page):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.locator("#usuario-login").fill(USER)
    page.locator("#pass-login").fill(PASSWORD)
    page.locator("#boton_ingresar").click()
    page.wait_for_url("**/admincontactos**", timeout=20000)
    time.sleep(2)


def get_supervision_items(page):
    """Abre el menu Supervision y devuelve todos los items hoja visibles."""
    # Click en Supervision (nivel 1)
    page.locator("#accionEjecutar_4").click()
    time.sleep(1.5)

    items = page.evaluate("""
        () => {
            const results = [];
            // Buscar todos los accionEjecutar_4xx (hijos de Supervision)
            document.querySelectorAll('[id^="accionEjecutar_4"]').forEach(el => {
                const id = el.id;
                if (id === 'accionEjecutar_4') return;  // el padre mismo
                const r = el.getBoundingClientRect();
                const visible = r.width > 0 && r.height > 0;
                const text = el.innerText ? el.innerText.trim() : '';
                results.push({ id, text, visible });
            });
            return results;
        }
    """)
    return items


def open_item_tab(page, item_id):
    """Intenta abrir el item en nueva pestana y devuelve la URL resultante."""
    try:
        with page.context.expect_page(timeout=12000) as info:
            page.evaluate(f"document.getElementById('{item_id}').click()")
        tab = info.value
        tab.wait_for_load_state("domcontentloaded", timeout=20000)
        try:
            tab.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            pass
        time.sleep(1.5)
        url = tab.url
        # Intenta obtener el titulo de la pagina
        titulo = ""
        try:
            h = tab.locator("h1, h2, .page-title, #titulo, #tituloSeccion").first
            if h.count() > 0:
                titulo = h.inner_text(timeout=2000).strip()
        except Exception:
            pass
        tab.close()
        return url, titulo
    except Exception as e:
        return f"ERROR: {e}", ""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300,
                                    args=["--start-maximized"])
        ctx     = browser.new_context(no_viewport=True, ignore_https_errors=True)
        page    = ctx.new_page()

        print("Iniciando sesion...")
        login(page)
        print("Sesion iniciada.\n")

        print("Obteniendo items de Supervision...")
        items = get_supervision_items(page)

        print(f"\n{'ID':<25} {'Visible':<8} {'Texto'}")
        print("-" * 70)
        for it in items:
            cubierto = " [CUBIERTO]" if it["id"] in CUBIERTOS else ""
            print(f"{it['id']:<25} {str(it['visible']):<8} {it['text']}{cubierto}")

        # Ahora explorar los que NO estan cubiertos y son visibles
        pendientes = [it for it in items
                      if it["id"] not in CUBIERTOS and it["visible"]]

        print(f"\n\nExplorando {len(pendientes)} items no cubiertos...\n")
        print(f"{'ID':<25} {'Texto':<35} {'URL'}")
        print("-" * 100)

        for it in pendientes:
            # Asegurarse que el menu este abierto
            page.locator("#accionEjecutar_4").click()
            time.sleep(1.0)
            # Si el item tiene padre (submenu de segundo nivel), abrirlo
            item_num = it["id"].replace("accionEjecutar_", "")
            if len(item_num) >= 3:
                padre_id = f"accionEjecutar_{item_num[:2]}"
                try:
                    padre = page.locator(f"#{padre_id}")
                    if padre.count() > 0:
                        padre.click()
                        time.sleep(0.8)
                except Exception:
                    pass

            url, titulo = open_item_tab(page, it["id"])
            path = url.split(BASE_URL)[-1] if BASE_URL in url else url
            print(f"{it['id']:<25} {it['text']:<35} {path}  {titulo}")
            time.sleep(0.5)

        browser.close()
        print("\n\nExploracion completada.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
