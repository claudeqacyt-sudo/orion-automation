"""
Explora el contenido de Notificar Usuarios y Monitor de Efectividad en FG-01.
"""
import os, sys, time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE_URL = os.getenv("ORION_BASE_URL")
USER     = os.getenv("ADMIN_USERNAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")


def dump_page(tab, nombre):
    print(f"\n{'='*60}")
    print(f"  {nombre}")
    print(f"  URL: {tab.url}")
    print(f"{'='*60}")

    data = tab.evaluate("""() => {
        function vis(e) { const r=e.getBoundingClientRect(); return r.width>0&&r.height>0; }
        const headings = [...document.querySelectorAll('h1,h2,h3,.page-title,#titulo,#tituloSeccion')]
            .filter(vis).map(e=>e.innerText.trim()).filter(t=>t);
        const inputs = [...document.querySelectorAll('input,select,textarea')]
            .filter(vis).map(e=>({ tag:e.tagName, id:e.id, name:e.name,
                                   type:e.type||'', ph:e.placeholder||'' }));
        const btns = [...document.querySelectorAll('button,a.btn,[class*="btn"]')]
            .filter(vis).map(e=>({ id:e.id, text:e.innerText.trim().substring(0,50) }))
            .filter(e=>e.text).slice(0,25);
        const tables = [...document.querySelectorAll('table,[id*="dt-"],[id*="tabla"]')]
            .filter(vis).map(e=>({ id:e.id, tag:e.tagName }));
        return { headings, inputs, btns, tables };
    }""")

    if data['headings']:
        print(f"\n  HEADINGS: {data['headings']}")
    if data['inputs']:
        print(f"\n  CONTROLES ({len(data['inputs'])}):")
        for inp in data['inputs']:
            print(f"    {inp['tag']:<8} #{inp['id']:<30} type={inp['type']:<12} ph={inp['ph']}")
    if data['btns']:
        print(f"\n  BOTONES ({len(data['btns'])}):")
        for b in data['btns']:
            print(f"    #{b['id']:<30} {b['text']}")
    if data['tables']:
        print(f"\n  TABLAS:")
        for t in data['tables']:
            print(f"    {t['tag']} #{t['id']}")


def main():
    with sync_playwright() as p:
        br  = p.chromium.launch(headless=True, slow_mo=200)
        ctx = br.new_context(viewport={"width":1600,"height":900}, ignore_https_errors=True)
        pg  = ctx.new_page()

        # Login
        pg.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
        pg.locator("#usuario-login").fill(USER)
        pg.locator("#pass-login").fill(PASSWORD)
        pg.locator("#boton_ingresar").click()
        pg.wait_for_url("**/admincontactos**", timeout=20000)
        time.sleep(2)

        # --- 1. Notificar Usuarios ---
        pg.locator("#accionEjecutar_4").click(); time.sleep(1.0)
        with pg.context.expect_page(timeout=12000) as info:
            pg.locator("#accionEjecutar_41").click()
        tab1 = info.value
        tab1.wait_for_load_state("domcontentloaded", timeout=20000)
        time.sleep(2)
        dump_page(tab1, "Notificar Usuarios")
        tab1.close()

        # --- 2. Monitor de Efectividad ---
        pg.locator("#accionEjecutar_4").click(); time.sleep(1.0)
        pg.locator("#accionEjecutar_42").click(); time.sleep(1.0)
        try:
            with pg.context.expect_page(timeout=12000) as info2:
                pg.evaluate("document.getElementById('accionEjecutar_421').click()")
            tab2 = info2.value
            tab2.wait_for_load_state("domcontentloaded", timeout=20000)
            time.sleep(2)
            dump_page(tab2, "Monitor de Efectividad")
            tab2.close()
        except Exception as e:
            print(f"\nMonitor de Efectividad ERROR: {e}")

        br.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
