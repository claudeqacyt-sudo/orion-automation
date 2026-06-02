"""
explorar_secciones_supervisor.py  (v9 — deep content inspection de cada seccion)

Objetivo: para cada seccion hoja del supervisor, abrir la nueva pestana,
esperar carga completa, y capturar TODO el contenido interactivo:
  - Titulos / headings
  - Selectores / dropdowns (id, opciones)
  - Inputs / textareas (id, placeholder, label asociado)
  - Botones (id, texto)
  - Tablas (id, headers, cantidad de filas)
  - Mensajes de estado / texto destacado
  - Cualquier otro elemento visible relevante
"""
import time
import os
os.makedirs("reports/screenshots", exist_ok=True)

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")
def info(m): print("  " + str(m))
def shot(pg, name):
    path = f"reports/screenshots/{name}.png"
    try:
        pg.screenshot(path=path, full_page=True)
        info("Screenshot: " + path)
    except Exception as e:
        info("Shot error: " + str(e))


NOMBRE_SUP   = "QASupervisor"
APELLIDO_SUP = "TestAuto"
EMAIL_SUP    = "qa.supervisor@test.com"

SECCIONES = [
    ("accionEjecutar_213", "Vinculos a Sistemas Externos",  "accionEjecutar_2", "accionEjecutar_21"),
    ("accionEjecutar_221", "Respuestas Rapidas",            "accionEjecutar_2", "accionEjecutar_22"),
    ("accionEjecutar_262", "Ver Importaciones",             "accionEjecutar_2", "accionEjecutar_26"),
    ("accionEjecutar_271", "Tipos de Tickets",              "accionEjecutar_2", "accionEjecutar_27"),
    ("accionEjecutar_281", "Busquedas Automaticas",         "accionEjecutar_2", "accionEjecutar_28"),
    ("accionEjecutar_5",   "Ayuda",                         None,               None),
]


def _en_viewport(page, element_id):
    return page.evaluate(f"""
        () => {{
            const el = document.getElementById('{element_id}');
            if (!el) return false;
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
        }}
    """)


def _preparar_menu(page, abuelo, padre, hoja_id):
    if abuelo is None:
        return True
    page.locator(f"#{abuelo}").click()
    time.sleep(1.0)
    if padre:
        page.locator(f"#{padre}").click()
        time.sleep(1.0)
    return _en_viewport(page, hoja_id)


def _esperar_carga_completa(page, timeout=20000):
    """
    Espera carga completa de la pagina:
    1. domcontentloaded
    2. networkidle (no mas requests por 500ms)
    3. Verificar que el body tenga texto real (>100 chars)
    """
    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout)
    except Exception:
        pass
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    # Extra wait para que Angular/jQuery termine de renderizar
    time.sleep(2)


def _capturar_contenido_completo(page):
    """
    Captura TODOS los elementos interactivos y de contenido de la pagina.
    """
    return page.evaluate("""
        () => {
            const out = {};

            // 1. Titulo de la pagina y headings principales
            out.page_title = document.title;
            const headings = [];
            document.querySelectorAll('h1,h2,h3,h4,h5,.titulo,.page-title,.section-title,.panel-title,.card-title')
                .forEach(el => {
                    if (el.offsetParent !== null || el.offsetHeight > 0) {
                        const txt = el.innerText.trim().replace(/\\s+/g,' ');
                        if (txt) headings.push({tag: el.tagName, text: txt});
                    }
                });
            out.headings = headings;

            // 2. Selectores / dropdowns visibles
            const selects = [];
            document.querySelectorAll('select').forEach(sel => {
                if (sel.offsetParent !== null) {
                    const opts = Array.from(sel.options).map(o => ({
                        value: o.value, text: o.text.trim()
                    }));
                    // Buscar label asociado
                    let labelText = '';
                    if (sel.id) {
                        const lbl = document.querySelector('label[for="' + sel.id + '"]');
                        if (lbl) labelText = lbl.innerText.trim();
                    }
                    selects.push({
                        id:        sel.id || '',
                        name:      sel.name || '',
                        label:     labelText,
                        opciones:  opts.length,
                        opciones_texto: opts.slice(0,10).map(o => o.text).join(' | '),
                        valor_actual: sel.value
                    });
                }
            });
            out.selects = selects;

            // 3. Inputs visibles (text, date, search, number, etc.)
            const inputs = [];
            document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=image]):not([type=checkbox]):not([type=radio])')
                .forEach(inp => {
                    if (inp.offsetParent !== null) {
                        let labelText = '';
                        if (inp.id) {
                            const lbl = document.querySelector('label[for="' + inp.id + '"]');
                            if (lbl) labelText = lbl.innerText.trim();
                        }
                        inputs.push({
                            id:          inp.id || '',
                            type:        inp.type || 'text',
                            placeholder: inp.placeholder || '',
                            label:       labelText,
                            value:       inp.value || ''
                        });
                    }
                });
            out.inputs = inputs;

            // 4. Checkboxes y radios visibles
            const checks = [];
            document.querySelectorAll('input[type=checkbox], input[type=radio]')
                .forEach(chk => {
                    if (chk.offsetParent !== null) {
                        let labelText = '';
                        if (chk.id) {
                            const lbl = document.querySelector('label[for="' + chk.id + '"]');
                            if (lbl) labelText = lbl.innerText.trim();
                        }
                        checks.push({
                            id:      chk.id || '',
                            type:    chk.type,
                            label:   labelText,
                            checked: chk.checked
                        });
                    }
                });
            out.checks = checks;

            // 5. Botones visibles (button + input[type=submit/button/image])
            const botones = [];
            document.querySelectorAll('button, input[type=submit], input[type=button], input[type=image], a.btn, .btn')
                .forEach(btn => {
                    if (btn.offsetParent !== null) {
                        const txt = (btn.innerText || btn.value || btn.title || btn.alt || '').trim().replace(/\\s+/g,' ');
                        if (txt) {
                            botones.push({
                                tag:  btn.tagName,
                                id:   btn.id || '',
                                text: txt.slice(0, 60),
                                type: btn.type || btn.getAttribute('type') || ''
                            });
                        }
                    }
                });
            out.botones = botones;

            // 6. Tablas visibles — headers y filas
            const tablas = [];
            document.querySelectorAll('table').forEach(tbl => {
                if (tbl.offsetParent !== null || tbl.offsetHeight > 0) {
                    const headers = [];
                    const thead = tbl.querySelector('thead tr, tr:first-child');
                    if (thead) {
                        thead.querySelectorAll('th, td').forEach(th => {
                            const txt = th.innerText.trim().replace(/\\s+/g,' ');
                            if (txt) headers.push(txt);
                        });
                    }
                    // Contar filas de datos (tbody)
                    const tbody = tbl.querySelector('tbody');
                    const dataRows = tbody ? tbody.querySelectorAll('tr').length : 0;
                    // Primera fila de datos (si existe)
                    let primeraFila = '';
                    if (tbody) {
                        const firstRow = tbody.querySelector('tr:first-child');
                        if (firstRow) primeraFila = firstRow.innerText.trim().replace(/\\s+/g,' ').slice(0,120);
                    }
                    tablas.push({
                        id:          tbl.id || '',
                        headers:     headers,
                        data_rows:   dataRows,
                        primera_fila: primeraFila
                    });
                }
            });
            out.tablas = tablas;

            // 7. Mensajes / labels de estado / alertas visibles
            const mensajes = [];
            document.querySelectorAll('.alert, .message, .msg, .status, .info-msg, .success, .error, .warning, [id*="msg"], [id*="Msg"], [id*="lbl"]')
                .forEach(el => {
                    if (el.offsetParent !== null) {
                        const txt = el.innerText.trim().replace(/\\s+/g,' ');
                        if (txt && txt.length > 2) {
                            mensajes.push({
                                id:   el.id || '',
                                cls:  el.className.slice(0,40),
                                text: txt.slice(0,150)
                            });
                        }
                    }
                });
            out.mensajes = mensajes;

            // 8. Texto principal del body (sin nav/scripts)
            const body_text = document.body.innerText.trim().replace(/\\s+/g,' ').slice(0, 800);
            out.body_text = body_text;

            return out;
        }
    """)


def _imprimir_contenido(nombre, datos):
    """Imprime el contenido capturado de forma legible."""
    info(f"Page title: '{datos['page_title']}'")

    if datos['headings']:
        info(f"Headings ({len(datos['headings'])}):")
        for h in datos['headings'][:5]:
            print(f"    <{h['tag']}> {h['text']}")

    if datos['selects']:
        info(f"Selects ({len(datos['selects'])}):")
        for s in datos['selects']:
            print(f"    #{s['id']} [{s['label']}] — {s['opciones']} opciones: {s['opciones_texto'][:80]}")

    if datos['inputs']:
        info(f"Inputs ({len(datos['inputs'])}):")
        for i in datos['inputs']:
            print(f"    #{i['id']} type={i['type']} label='{i['label']}' placeholder='{i['placeholder']}'")

    if datos['checks']:
        info(f"Checkboxes/Radios ({len(datos['checks'])}):")
        for c in datos['checks']:
            print(f"    #{c['id']} [{c['type']}] label='{c['label']}' checked={c['checked']}")

    if datos['botones']:
        info(f"Botones ({len(datos['botones'])}):")
        for b in datos['botones']:
            print(f"    #{b['id']} <{b['tag']}> '{b['text']}'")

    if datos['tablas']:
        info(f"Tablas ({len(datos['tablas'])}):")
        for t in datos['tablas']:
            print(f"    #{t['id']} — headers: {t['headers'][:6]}")
            print(f"           data_rows: {t['data_rows']} — primera fila: '{t['primera_fila'][:80]}'")

    if datos['mensajes']:
        info(f"Mensajes/Labels ({len(datos['mensajes'])}):")
        for m in datos['mensajes']:
            print(f"    #{m['id']} .{m['cls']}: '{m['text'][:100]}'")

    info(f"Body text: {datos['body_text'][:400]}")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers crear/borrar supervisor
# ─────────────────────────────────────────────────────────────────────────────

def _crear_supervisor(shared_page):
    from pages.frameworks_page import FrameworksNav, GestionUsuariosPage
    sep("CREAR / VERIFICAR SUPERVISOR")
    nav = FrameworksNav(shared_page)
    fw  = nav.open_gestion_usuarios()
    if fw.usuario_existe_en_grid(NOMBRE_SUP):
        info("Pre-cleanup: borrando QASupervisor existente...")
        fw.borrar_usuario(NOMBRE_SUP)
        time.sleep(1)
    password = fw.crear_usuario(
        nombre=NOMBRE_SUP, apellido=APELLIDO_SUP,
        nivel=GestionUsuariosPage.NIVEL_SUPERVISOR, email=EMAIL_SUP,
    )
    info(f"Password: {password}")
    fw.page.close()
    return password


def _borrar_supervisor(shared_page):
    from pages.frameworks_page import FrameworksNav
    try:
        nav = FrameworksNav(shared_page)
        fw  = nav.open_gestion_usuarios()
        if fw.usuario_existe_en_grid(NOMBRE_SUP):
            fw.borrar_usuario(NOMBRE_SUP)
            info("Supervisor borrado")
        fw.page.close()
    except Exception as e:
        info(f"Error borrando supervisor: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Test principal
# ─────────────────────────────────────────────────────────────────────────────

def test_explorar_secciones_supervisor(shared_page, base_url, admin_credentials):
    from pages.login_page import LoginPage
    login = LoginPage(shared_page)
    password = None

    try:
        password = _crear_supervisor(shared_page)
        assert password, "No se obtuvo password"

        sep("LOGOUT CYT")
        login.logout()
        time.sleep(2)

        sep(f"LOGIN COMO {NOMBRE_SUP}")
        login.navigate(base_url)
        login.login(NOMBRE_SUP, password)
        time.sleep(3)
        shared_page.locator("#accionEjecutar_2").wait_for(state="visible", timeout=10000)
        shot(shared_page, "sec_00_dashboard")

        # ── Explorar cada seccion en profundidad ──────────────────────────────
        for item_id, nombre, abuelo, padre in SECCIONES:
            sep(f"SECCION: {nombre} (#{item_id})")

            # Preparar menu
            if abuelo:
                listo = _preparar_menu(shared_page, abuelo, padre, item_id)
                if not listo:
                    info(f"ERROR: #{item_id} no visible")
                    continue

            # Click en la hoja — abrir nueva pestana
            try:
                with shared_page.context.expect_page(timeout=8000) as npi:
                    shared_page.locator(f"#{item_id}").click()
                pag = npi.value
            except Exception as e:
                info(f"No abrio nueva pestana: {e}")
                continue

            # Esperar carga completa
            _esperar_carga_completa(pag)
            shot(pag, f"sec_{item_id}")

            # Capturar e imprimir todo el contenido
            datos = _capturar_contenido_completo(pag)
            _imprimir_contenido(nombre, datos)

            pag.close()
            print()

        sep("LOGOUT SUPERVISOR")
        login.logout()
        time.sleep(2)

    finally:
        sep("CLEANUP")
        try:
            login.navigate(base_url)
            login.login(admin_credentials["username"], admin_credentials["password"])
            login.verify_logged_in()
            info("Sesion restaurada como cyt")
        except Exception as e:
            info(f"Error restaurando sesion: {e}")
        if password:
            _borrar_supervisor(shared_page)
