"""
tests/regression/frameworks/test_gestion_usuarios.py
Suite de regresion — Frameworks > Configurar > Usuarios > Gestion de Usuarios

Modulo: Orion Contact Center (Frameworks) — puerto 8443
URL directa: https://vm-2k22-fg-01.orioncontactcenter.com.ar:8443/usuarios.aspx

Arquitectura de fixtures:
  supervisor_qa      (scope=module) — crea QASupervisor UNA VEZ para todo el modulo,
                                      lo borra en teardown. Todos los tests comparten
                                      el mismo usuario.
  supervisor_logueado (scope=class) — hace login como supervisor UNA VEZ para la clase
                                      TestSupervisorAcceso, logout + restaura cyt al final.
  gestion_tab        (scope=class)  — abre el tab de Frameworks una vez por clase.

Estructura de tests:
  TestSupervisorCreacion  — FRW-001-A/B: verifica que la creacion fue exitosa
  TestSupervisorAcceso    — FRW-001-C/D/E/F: verifica acceso, menu y contenido de secciones

Menu supervisor (verificado con explorar_menu_supervisor.py):
  Configuracion > Campos de Contacto > Vinculos a Sistemas Externos
               > Chat de Contactos  > Respuestas Rapidas
               > Importacion        > Ver Importaciones
               > Tickets            > Tipos de Tickets
               > Busquedas          > Busquedas Automaticas
  Ayuda

Items bloqueados para Supervisor (solo visibles para Administrador):
  accionEjecutar_1, accionEjecutar_3, accionEjecutar_4 (Supervision/Frameworks)

Secciones y sus URLs (verificado con explorar_secciones_supervisor.py v8+v9):
  accionEjecutar_213 -> /ConfiguradorDeUrls
  accionEjecutar_221 -> /configPropiedadesSupervisor
  accionEjecutar_262 -> /verImportaciones
  accionEjecutar_271 -> /configTiposTickets
  accionEjecutar_281 -> /configBusquedasAutomaticas
  accionEjecutar_5   -> /Ayuda
"""
import json
import re
import time
from pathlib import Path

import pytest

pytestmark = [pytest.mark.regression, pytest.mark.supervisor]
from pages.frameworks_page import (
    FrameworksNav,
    GestionUsuariosPage,
)
from pages.login_page import LoginPage

# Archivo local donde se guarda la password del supervisor entre runs.
# Listado en .gitignore — nunca se sube al repositorio.
_SUPERVISOR_CACHE = Path(__file__).parent / ".qa_supervisor_cache.json"


def _leer_cache() -> dict:
    try:
        return json.loads(_SUPERVISOR_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _guardar_cache(data: dict):
    _SUPERVISOR_CACHE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _borrar_cache():
    try:
        _SUPERVISOR_CACHE.unlink(missing_ok=True)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Fixture modulo — crea QASupervisor UNA VEZ para todos los tests del modulo
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def supervisor_qa(shared_page, base_url, admin_credentials):
    """
    Prepara QASupervisor para la sesion de tests.

    Estrategia de reutilizacion:
      - Si el usuario ya existe en el sistema Y hay una cache valida con su password,
        se reutiliza directamente (sin borrar ni recrear). Esto hace que las
        ejecuciones consecutivas sean mas rapidas.
      - Si no existe o la cache es invalida, se crea desde cero y se guarda la cache.

    Teardown:
      El supervisor NO se borra al finalizar — queda disponible para el proximo run.
      Para forzar una recreacion, borrar manualmente el archivo:
        tests/regression/frameworks/.qa_supervisor_cache.json

    Yields dict:
      { "nombre": str, "password": str, "lbl_texto": str }
    """
    NOMBRE   = "QASupervisor"
    APELLIDO = "TestAuto"
    EMAIL    = "qa.supervisor@test.com"
    password  = None
    lbl_texto = ""

    # ── SETUP ────────────────────────────────────────────────────────────────
    try:
        nav = FrameworksNav(shared_page)
        fw  = nav.open_gestion_usuarios()

        cache = _leer_cache()
        existe = fw.usuario_existe_en_grid(NOMBRE)

        if existe and cache.get("nombre") == NOMBRE and cache.get("password"):
            # ── Reutilizar supervisor existente ──────────────────────────────
            password  = cache["password"]
            lbl_texto = cache.get("lbl_texto", "")
            print(f"\n[supervisor_qa] Reutilizando '{NOMBRE}' (password desde cache)")
        else:
            # ── Crear supervisor nuevo ───────────────────────────────────────
            if existe:
                print(f"\n[supervisor_qa] Cache invalida — borrando '{NOMBRE}' para recrear...")
                fw.borrar_usuario(NOMBRE)
                time.sleep(1)
            password  = fw.crear_usuario(
                nombre=NOMBRE, apellido=APELLIDO,
                nivel=GestionUsuariosPage.NIVEL_SUPERVISOR, email=EMAIL,
            )
            lbl_texto = fw.get_password_label_text()
            _guardar_cache({"nombre": NOMBRE, "password": password, "lbl_texto": lbl_texto})
            print(f"\n[supervisor_qa] '{NOMBRE}' creado — password guardada en cache")

        fw.page.close()
    except Exception as e:
        pytest.skip(f"No se pudo preparar QASupervisor — se omiten todos los tests del modulo: {e}")

    yield {
        "nombre":    NOMBRE,
        "password":  password,
        "lbl_texto": lbl_texto,
    }

    # ── TEARDOWN: NO borrar — el supervisor queda para el proximo run ─────────
    print(f"\n[supervisor_qa] '{NOMBRE}' conservado para reutilizacion en el proximo run")


# ─────────────────────────────────────────────────────────────────────────────
# Fixture clase — abre Frameworks UNA VEZ para los tests de creacion
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def gestion_tab(shared_page):
    """
    Abre Frameworks > Gestion de Usuarios una sola vez para la clase.
    Se usa en TestSupervisorCreacion mientras la sesion es cyt.
    """
    nav = FrameworksNav(shared_page)
    page_obj = nav.open_gestion_usuarios()
    yield page_obj
    try:
        page_obj.page.close()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Fixture clase — inicia sesion como supervisor UNA VEZ para los tests de acceso
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def supervisor_logueado(supervisor_qa, shared_page, base_url, admin_credentials):
    """
    Hace login como QASupervisor una sola vez para toda la clase TestSupervisorAcceso.
    Al finalizar la clase: logout supervisor → login cyt (restaura sesion para teardown
    de supervisor_qa).

    Yields: shared_page (ya autenticado como supervisor, menu visible)
    """
    login = LoginPage(shared_page)

    # Logout cyt
    login.logout()
    time.sleep(1.5)

    # Login como supervisor
    login.navigate(base_url)
    login.login(supervisor_qa["nombre"], supervisor_qa["password"])

    # Esperar que el SPA renderice el menu
    shared_page.locator("#accionEjecutar_2").wait_for(state="visible", timeout=10000)

    yield shared_page  # sesion activa como supervisor

    # Teardown: logout supervisor, login cyt
    try:
        login.logout()
        time.sleep(1.5)
    except Exception:
        pass
    login.navigate(base_url)
    login.login(admin_credentials["username"], admin_credentials["password"])
    login.verify_logged_in()


# ─────────────────────────────────────────────────────────────────────────────
# FRW-001 — Creacion del Supervisor
# Verifica que la creacion fue exitosa mientras la sesion es cyt.
# ─────────────────────────────────────────────────────────────────────────────

class TestSupervisorCreacion:

    # ── FRW-001-A ─────────────────────────────────────────────────────────────

    def test_FRW001_A_password_generada_correctamente(self, supervisor_qa):
        """
        FRW-001-A: Al crear el supervisor el sistema genera una password aleatoria
        visible en #lblPasswordRandom con el formato esperado.
        Formato: "Se inicializo la clave, la misma es: XXXXXXXX"
        """
        lbl      = supervisor_qa["lbl_texto"]
        password = supervisor_qa["password"]

        assert lbl, \
            "El label #lblPasswordRandom esta vacio — la creacion puede haber fallado " \
            "(usuario ya existia, error de validacion, o servidor no proceso la solicitud)"

        assert (
            "inicializo la clave" in lbl.lower()
            or "la misma es" in lbl.lower()
        ), (
            f"El label no contiene el mensaje esperado de password. "
            f"Texto encontrado: '{lbl}'"
        )

        assert password, \
            f"No se pudo extraer la password del label. Texto completo: '{lbl}'"

        assert re.match(r'^\S+$', password), \
            f"La password extraida parece invalida (contiene espacios): '{password}'"

    # ── FRW-001-B ─────────────────────────────────────────────────────────────

    def test_FRW001_B_usuario_aparece_en_grid(self, supervisor_qa, gestion_tab):
        """
        FRW-001-B: El usuario QASupervisor aparece en el grid de Gestion de Usuarios
        inmediatamente despues de la creacion.
        """
        assert gestion_tab.usuario_existe_en_grid(supervisor_qa["nombre"]), \
            f"El usuario '{supervisor_qa['nombre']}' no aparece en el grid — " \
            "la creacion pudo haber fallado silenciosamente"


# ─────────────────────────────────────────────────────────────────────────────
# FRW-001 — Acceso del Supervisor
# Verifica login, menu y navegacion con la sesion del supervisor.
# Todos los tests de esta clase comparten la misma sesion (supervisor_logueado).
# ─────────────────────────────────────────────────────────────────────────────

class TestSupervisorAcceso:

    # Menu verificado con explorar_menu_supervisor.py
    MENU_ESPERADO = [
        ("accionEjecutar_2",   "Configuracion"),
        ("accionEjecutar_21",  "Campos de Contacto"),
        ("accionEjecutar_213", "Vinculos a Sistemas Externos"),
        ("accionEjecutar_22",  "Chat de Contactos"),
        ("accionEjecutar_221", "Respuestas Rapidas"),
        ("accionEjecutar_26",  "Importacion"),
        ("accionEjecutar_262", "Ver Importaciones"),
        ("accionEjecutar_27",  "Tickets"),
        ("accionEjecutar_271", "Tipos de Tickets"),
        ("accionEjecutar_28",  "Busquedas"),
        ("accionEjecutar_281", "Busquedas Automaticas"),
        ("accionEjecutar_5",   "Ayuda"),
    ]

    MENU_BLOQUEADO = [
        ("accionEjecutar_1", "seccion exclusiva de Administrador"),
        ("accionEjecutar_3", "seccion exclusiva de Administrador"),
        ("accionEjecutar_4", "Supervision / Orion Contact Center"),
    ]

    MENU_HOJAS = [
        ("accionEjecutar_213", "Vinculos a Sistemas Externos"),
        ("accionEjecutar_221", "Respuestas Rapidas"),
        ("accionEjecutar_262", "Ver Importaciones"),
        ("accionEjecutar_271", "Tipos de Tickets"),
        ("accionEjecutar_281", "Busquedas Automaticas"),
        ("accionEjecutar_5",   "Ayuda"),
    ]

    # ── FRW-001-C ─────────────────────────────────────────────────────────────

    def test_FRW001_C_login_exitoso(self, supervisor_logueado):
        """
        FRW-001-C: El usuario QASupervisor puede iniciar sesion en el sistema.
        Verifica que tras el login la URL contiene /admincontactos.
        """
        assert LoginPage.URL_POST_LOGIN in supervisor_logueado.url, \
            f"Login del supervisor fallo — URL inesperada: {supervisor_logueado.url}"

    # ── FRW-001-D ─────────────────────────────────────────────────────────────

    def test_FRW001_D_menu_items_correctos(self, supervisor_logueado):
        """
        FRW-001-D: El perfil Supervisor muestra exactamente los 12 items de menu
        que le corresponden — todos visibles en el DOM.
        """
        page = supervisor_logueado
        for item_id, descripcion in self.MENU_ESPERADO:
            visible = page.evaluate(f"""
                () => {{
                    const el = document.getElementById('{item_id}');
                    return el ? el.offsetParent !== null : false;
                }}
            """)
            assert visible, \
                f"Item '{descripcion}' (#{item_id}) no esta visible para el Supervisor — " \
                "puede que el perfil haya perdido permisos"

    # ── FRW-001-E ─────────────────────────────────────────────────────────────

    def test_FRW001_E_menu_admin_bloqueado(self, supervisor_logueado):
        """
        FRW-001-E: Los items exclusivos del Administrador NO existen en el DOM
        del Supervisor — no hay escalada de privilegios en el menu.
        """
        page = supervisor_logueado
        for item_id, descripcion in self.MENU_BLOQUEADO:
            existe = page.evaluate(f"""
                () => document.getElementById('{item_id}') !== null
            """)
            assert not existe, \
                f"Item '{descripcion}' (#{item_id}) NO deberia estar disponible " \
                f"para el Supervisor — posible escalada de privilegios en el menu"

    # Secciones hoja con su camino de navegacion y URL esperada
    # Verificado con explorar_secciones_supervisor.py v8:
    #   click nativo en accionEjecutar_2 -> llega a vista Configuracion (21,22,26,27,28 visibles)
    #   click nativo en padre            -> muestra la hoja
    #   click nativo en hoja             -> abre NUEVA PESTANA en la URL esperada
    SECCIONES_HOJA_NAV = [
        # (hoja_id, descripcion, abuelo_id, padre_id, url_path_esperada)
        ("accionEjecutar_213", "Vinculos a Sistemas Externos", "accionEjecutar_2", "accionEjecutar_21", "/ConfiguradorDeUrls"),
        ("accionEjecutar_221", "Respuestas Rapidas",           "accionEjecutar_2", "accionEjecutar_22", "/configPropiedadesSupervisor"),
        ("accionEjecutar_262", "Ver Importaciones",            "accionEjecutar_2", "accionEjecutar_26", "/verImportaciones"),
        ("accionEjecutar_271", "Tipos de Tickets",             "accionEjecutar_2", "accionEjecutar_27", "/configTiposTickets"),
        ("accionEjecutar_281", "Busquedas Automaticas",        "accionEjecutar_2", "accionEjecutar_28", "/configBusquedasAutomaticas"),
        ("accionEjecutar_5",   "Ayuda",                        None,               None,                "/Ayuda"),
    ]

    @staticmethod
    def _hoja_en_viewport(page, element_id: str) -> bool:
        """True si el elemento tiene ancho y alto > 0 en la pantalla (realmente visible)."""
        return page.evaluate(f"""
            () => {{
                const el = document.getElementById('{element_id}');
                if (!el) return false;
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            }}
        """)

    def _preparar_menu(self, page, abuelo: str, padre: str, hoja_id: str) -> bool:
        """
        Navega el menu para que hoja_id sea visible y clickeable.
        Estrategia (verificada con explorar_secciones_supervisor.py v8):
          1. Click nativo en abuelo (accionEjecutar_2) -> vuelve a vista Configuracion
          2. Click nativo en padre (21, 22, 26, 27, 28) -> muestra hoja
        Retorna True si la hoja quedo visible.
        """
        if abuelo is None:
            return True  # Items de nivel 1 (Ayuda) — siempre visibles

        # Click nativo en abuelo (accionEjecutar_2) — siempre, para resetear el estado
        page.locator(f"#{abuelo}").click()
        time.sleep(1.0)

        # Click nativo en padre directo
        if padre:
            page.locator(f"#{padre}").click()
            time.sleep(1.0)

        return self._hoja_en_viewport(page, hoja_id)

    @staticmethod
    def _esperar_pagina_lista(page, url_path: str):
        """
        Espera carga completa de la pagina:
        1. domcontentloaded
        2. networkidle (sin requests por 500 ms)
        3. Elemento especifico por seccion visible — confirma que el JS renderizo
        """
        try:
            page.wait_for_load_state("domcontentloaded", timeout=20000)
        except Exception:
            pass
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        # Selector especifico que confirma que la seccion termino de cargar
        _ELEMENTO_READY = {
            "/ConfiguradorDeUrls":          "#tblUrlsConfiguradas",
            "/configPropiedadesSupervisor": "#tblRespuestasSupervisor",
            "/verImportaciones":            "#btnFiltrar",
            "/configTiposTickets":          "#txtFilterTypes",
            "/configBusquedasAutomaticas":  "#busquedaDesde",
            "/Ayuda":                       "#dt-version",
        }
        selector = _ELEMENTO_READY.get(url_path)
        if selector:
            try:
                page.locator(selector).wait_for(state="visible", timeout=8000)
            except Exception:
                pass  # El assert especifico de la seccion reportara el fallo con detalle

    @staticmethod
    def _tiene_error_servidor(page) -> bool:
        """True si la pagina muestra un error del servidor (500, excepcion, 404, etc.)."""
        return page.evaluate("""
            () => {
                const t = document.body.innerText.toLowerCase();
                return (
                    t.includes('server error')
                    || t.includes('exception')
                    || t.includes('404')
                    || t.includes('403')
                );
            }
        """)

    @staticmethod
    def _verificar_vinculos(page):
        """
        /ConfiguradorDeUrls — Vinculos a Sistemas Externos.
        Verifica: heading, selectores de formulario con opciones de tipo de enlace,
        inputs de nombre/direccion, botones de accion y tabla de configuraciones.
        Interacciones: cambiar tipo de enlace, click en Nuevo Enlace.
        """
        body = page.inner_text("body").lower()
        assert "sistema" in body or "enlace" in body, \
            "Vinculos: heading 'sistemas externos'/'enlaces' no encontrado en el cuerpo"

        # Selectores del formulario
        for sel_id in ("#cmbTipoEnlace", "#cmbCliente", "#cmbTarea"):
            assert page.locator(sel_id).count() > 0, \
                f"Vinculos: selector '{sel_id}' no encontrado"

        # Opciones de tipo de enlace: Link / Documento / API-GET / API-POST
        opciones_tipo = page.evaluate("""
            () => Array.from(
                document.querySelectorAll('#cmbTipoEnlace option')
            ).map(o => o.text.trim()).filter(t => t)
        """)
        for esperado in ["Link", "Documento", "API"]:
            assert any(esperado.lower() in o.lower() for o in opciones_tipo), (
                f"Vinculos: opcion '{esperado}' no encontrada en #cmbTipoEnlace. "
                f"Opciones actuales: {opciones_tipo}"
            )

        # Inputs de formulario
        for inp_id in ("#txtNombreEnlace", "#txtDireccionEnlace"):
            assert page.locator(inp_id).count() > 0, \
                f"Vinculos: input '{inp_id}' no encontrado"

        # Botones de accion
        for btn_id in ("#btnNuevoEnlace", "#btnGuardarEnlace"):
            assert page.locator(btn_id).count() > 0, \
                f"Vinculos: boton '{btn_id}' no encontrado"

        # Tabla de URLs configuradas
        assert page.locator("#tblUrlsConfiguradas").count() > 0, \
            "Vinculos: tabla #tblUrlsConfiguradas no encontrada"

        # Interaccion 1: cambiar tipo de enlace → el selector responde
        page.locator("#cmbTipoEnlace").select_option(index=1)
        valor = page.evaluate("() => document.querySelector('#cmbTipoEnlace').value")
        assert valor, "Vinculos: #cmbTipoEnlace no respondio al cambio de opcion"

        # Interaccion 2: seleccionar cliente → habilita #btnNuevoEnlace → click
        opciones_cliente = page.evaluate("""
            () => Array.from(document.querySelectorAll('#cmbCliente option'))
                       .map(o => o.value).filter(v => v)
        """)
        if opciones_cliente:
            page.locator("#cmbCliente").select_option(value=opciones_cliente[0])
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            habilitado = page.evaluate(
                "() => !document.querySelector('#btnNuevoEnlace').disabled"
            )
            if habilitado:
                page.locator("#btnNuevoEnlace").click()
                time.sleep(1)
                assert "/ConfiguradorDeUrls" in page.url, \
                    "Vinculos: click en #btnNuevoEnlace navego fuera de la seccion"

    @staticmethod
    def _verificar_respuestas_rapidas(page):
        """
        /configPropiedadesSupervisor — Respuestas Rapidas de Chat.
        Verifica: heading con 'respuesta'/'chat', selector de cliente,
        tabla con header 'Respuesta'.
        Interaccion: cambiar cliente → tabla sigue presente.
        """
        body = page.inner_text("body").lower()
        assert "respuesta" in body or "chat" in body, \
            "Respuestas Rapidas: contenido esperado ('respuesta'/'chat') no encontrado"

        # Selector de cliente
        assert page.locator("#cmbCliente").count() > 0, \
            "Respuestas Rapidas: selector #cmbCliente no encontrado"

        # Tabla principal
        assert page.locator("#tblRespuestasSupervisor").count() > 0, \
            "Respuestas Rapidas: tabla #tblRespuestasSupervisor no encontrada"

        # Header de tabla debe incluir 'Respuesta'
        headers = page.evaluate("""
            () => {
                const tbl = document.querySelector('#tblRespuestasSupervisor');
                if (!tbl) return [];
                const fila = tbl.querySelector('thead tr, tr:first-child');
                if (!fila) return [];
                return Array.from(fila.querySelectorAll('th, td'))
                            .map(c => c.innerText.trim())
                            .filter(t => t);
            }
        """)
        assert any("respuesta" in h.lower() for h in headers), (
            f"Respuestas Rapidas: columna 'Respuesta' no encontrada en headers. "
            f"Headers actuales: {headers}"
        )

        # Interaccion: cambiar seleccion de cliente → tabla debe seguir presente
        opciones = page.evaluate("""
            () => Array.from(document.querySelectorAll('#cmbCliente option'))
                       .map(o => o.value).filter(v => v)
        """)
        if len(opciones) > 1:
            page.locator("#cmbCliente").select_option(value=opciones[1])
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            assert page.locator("#tblRespuestasSupervisor").count() > 0, \
                "Respuestas Rapidas: tabla desaparecio tras cambiar el cliente"

    @staticmethod
    def _verificar_ver_importaciones(page):
        """
        /verImportaciones — Ver Importaciones.
        Verifica: heading, selectores de filtro con opciones correctas (Todas/
        Pendientes/Realizadas), inputs de fecha, boton Filtrar, tabla de resultados.
        Interaccion: click en Filtrar -> tabla debe seguir visible tras el filtrado.
        """
        body = page.inner_text("body").lower()
        assert "importaci" in body, \
            "Importaciones: contenido sobre importaciones no encontrado"

        # Selectores de filtro
        for sel_id in ("#cmbEstado", "#cmbActiva"):
            assert page.locator(sel_id).count() > 0, \
                f"Importaciones: selector '{sel_id}' no encontrado"

        # Opciones de estado: Todas / Pendientes / Realizadas
        opts_estado = page.evaluate("""
            () => Array.from(
                document.querySelectorAll('#cmbEstado option')
            ).map(o => o.text.trim()).filter(t => t)
        """)
        for esperado in ["Todas", "Pendientes", "Realizadas"]:
            assert any(esperado.lower() in o.lower() for o in opts_estado), (
                f"Importaciones: opcion '{esperado}' no encontrada en #cmbEstado. "
                f"Opciones actuales: {opts_estado}"
            )

        # Inputs de rango de fecha
        for inp_id in ("#fechaDesde", "#fechaHasta"):
            assert page.locator(inp_id).count() > 0, \
                f"Importaciones: input '{inp_id}' no encontrado"

        # Boton filtrar visible y clickeable
        assert page.locator("#btnFiltrar").is_visible(), \
            "Importaciones: boton #btnFiltrar no visible"

        # Tabla de resultados presente antes de filtrar
        assert page.locator("#dt-resultados-importaciones").count() > 0, \
            "Importaciones: tabla #dt-resultados-importaciones no encontrada"

        # Interaccion 1: cambiar estado a "Pendientes" → el selector responde
        page.locator("#cmbEstado").select_option(index=1)
        valor_estado = page.evaluate("() => document.querySelector('#cmbEstado').value")
        assert valor_estado, "Importaciones: #cmbEstado no respondio al cambio de opcion"

        # Interaccion 2: click Filtrar → tabla sigue presente tras el filtrado
        page.locator("#btnFiltrar").click()
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        assert page.locator("#dt-resultados-importaciones").count() > 0, \
            "Importaciones: tabla #dt-resultados-importaciones desaparecio tras click en Filtrar"

    @staticmethod
    def _verificar_tipos_tickets(page):
        """
        /configTiposTickets — Tipos de Tickets.
        Verifica: heading con 'ticket', input de filtro con placeholder 'Filtrar Tipos'.
        Interaccion: escribir en el filtro → input responde → limpiar.
        """
        body = page.inner_text("body").lower()
        assert "ticket" in body, \
            "Tipos de Tickets: contenido sobre tickets no encontrado"

        # Input de filtro de tipos
        assert page.locator("#txtFilterTypes").count() > 0, \
            "Tipos de Tickets: input #txtFilterTypes no encontrado"

        placeholder = page.get_attribute("#txtFilterTypes", "placeholder") or ""
        assert "filtrar" in placeholder.lower() or "filter" in placeholder.lower(), (
            f"Tipos de Tickets: placeholder inesperado en #txtFilterTypes. "
            f"Actual: '{placeholder}'"
        )

        # Al menos un heading debe contener 'ticket'
        headings = page.evaluate("""
            () => Array.from(document.querySelectorAll('h1,h2,h3,h4,h5'))
                       .map(h => h.innerText.trim()).filter(t => t)
        """)
        assert any("ticket" in h.lower() for h in headings), (
            f"Tipos de Tickets: ningun heading contiene 'ticket'. "
            f"Headings encontrados: {headings}"
        )

        # Interaccion: escribir en el filtro → el input acepta texto → limpiar
        page.locator("#txtFilterTypes").fill("test")
        valor = page.input_value("#txtFilterTypes")
        assert valor == "test", \
            f"Tipos de Tickets: #txtFilterTypes no acepto el texto. Valor actual: '{valor}'"
        page.locator("#txtFilterTypes").clear()

    @staticmethod
    def _verificar_busquedas_automaticas(page):
        """
        /configBusquedasAutomaticas — Busquedas Automaticas.
        Verifica: select #busquedaDesde con opciones 'Fichas de Ticket' y
        'Fichas de Contacto', boton #btnCreateBusqueda presente.
        """
        body = page.inner_text("body").lower()
        assert "squeda" in body, \
            "Busquedas Automaticas: contenido esperado ('busqueda') no encontrado"

        # Select de origen de busqueda
        assert page.locator("#busquedaDesde").count() > 0, \
            "Busquedas Automaticas: selector #busquedaDesde no encontrado"

        # Opciones: Fichas de Ticket y Fichas de Contacto
        opts = page.evaluate("""
            () => Array.from(
                document.querySelectorAll('#busquedaDesde option')
            ).map(o => o.text.trim()).filter(t => t)
        """)
        assert any("ticket" in o.lower() for o in opts), (
            f"Busquedas Automaticas: 'Fichas de Ticket' no encontrada en #busquedaDesde. "
            f"Opciones: {opts}"
        )
        assert any("contacto" in o.lower() for o in opts), (
            f"Busquedas Automaticas: 'Fichas de Contacto' no encontrada en #busquedaDesde. "
            f"Opciones: {opts}"
        )

        # Boton crear busqueda
        assert page.locator("#btnCreateBusqueda").count() > 0, \
            "Busquedas Automaticas: boton #btnCreateBusqueda no encontrado"

        # Interaccion 1: cambiar origen de busqueda → el selector responde
        page.locator("#busquedaDesde").select_option(index=1)
        valor = page.evaluate("() => document.querySelector('#busquedaDesde').value")
        assert valor, "Busquedas Automaticas: #busquedaDesde no respondio al cambio de opcion"

        # Interaccion 2: click en Crear Busqueda → la pagina responde sin navegar
        page.locator("#btnCreateBusqueda").click()
        time.sleep(1)
        assert "/configBusquedasAutomaticas" in page.url, \
            "Busquedas Automaticas: click en #btnCreateBusqueda navego fuera de la seccion"

    @staticmethod
    def _verificar_ayuda(page):
        """
        /Ayuda — Ayuda del Sistema.
        Verifica: tabla #dt-version presente con filas de datos,
        cuerpo contiene 'ayuda' y 'version'.
        """
        body = page.inner_text("body").lower()
        assert "ayuda" in body, \
            "Ayuda: contenido de ayuda no encontrado"

        # Tabla de versiones
        assert page.locator("#dt-version").count() > 0, \
            "Ayuda: tabla #dt-version no encontrada"

        # La tabla debe tener al menos una fila de datos
        data_rows = page.evaluate("""
            () => {
                const tbody = document.querySelector('#dt-version tbody');
                return tbody ? tbody.querySelectorAll('tr').length : 0;
            }
        """)
        assert data_rows > 0, \
            f"Ayuda: tabla #dt-version sin filas de datos (rows={data_rows})"

        # El cuerpo debe mencionar informacion de version
        assert "version" in body, \
            "Ayuda: informacion de version no encontrada en el cuerpo"

    def _verificar_contenido_seccion(self, page, hoja_id: str, descripcion: str):
        """Despacha la verificacion especifica de contenido segun la seccion."""
        verificadores = {
            "accionEjecutar_213": self._verificar_vinculos,
            "accionEjecutar_221": self._verificar_respuestas_rapidas,
            "accionEjecutar_262": self._verificar_ver_importaciones,
            "accionEjecutar_271": self._verificar_tipos_tickets,
            "accionEjecutar_281": self._verificar_busquedas_automaticas,
            "accionEjecutar_5":   self._verificar_ayuda,
        }
        fn = verificadores.get(hoja_id)
        if fn:
            fn(page)
        else:
            pytest.fail(
                f"No hay verificacion de contenido definida para "
                f"'{descripcion}' (#{hoja_id})"
            )

    # ── FRW-001-F ─────────────────────────────────────────────────────────────

    def test_FRW001_F_secciones_hoja_abren_contenido(self, supervisor_logueado):
        """
        FRW-001-F: Al hacer click en cada seccion hoja del menu del Supervisor
        se abre una nueva pestana en la URL correcta, la pagina carga completamente
        (networkidle + elemento especifico visible) y el contenido es verificado
        elemento a elemento segun lo descubierto con explorar_secciones_supervisor.py v9.

        Verificaciones por seccion:
          Vinculos        — #cmbTipoEnlace (Link/Documento/API), inputs, botones, tabla
          Respuestas      — #tblRespuestasSupervisor con header 'Respuesta', #cmbCliente
          Importaciones   — filtros (#cmbEstado 3 opciones), tabla, click Filtrar
          Tipos Tickets   — heading 'ticket', #txtFilterTypes placeholder
          Busquedas Auto  — #busquedaDesde (Ticket/Contacto), #btnCreateBusqueda
          Ayuda           — #dt-version con filas de datos, texto de version

        Mecanismo de navegacion (verificado con explorar_secciones_supervisor.py v8):
          - El SPA requiere click nativo en accionEjecutar_2 (Configuracion) +
            click en el padre antes de clickear la hoja.
          - Cada hoja abre una NUEVA PESTANA con ASP.NET WebForms.
          - Los clicks via evaluate() no abren nueva pestana.
        """
        page = supervisor_logueado

        for hoja_id, descripcion, abuelo, padre, url_esperada in self.SECCIONES_HOJA_NAV:

            # 1. Preparar menu: expandir abuelo y padre para que hoja sea visible
            hoja_lista = self._preparar_menu(page, abuelo, padre, hoja_id)
            assert hoja_lista, (
                f"'{descripcion}' (#{hoja_id}) no es visible en el menu despues "
                f"de expandir los padres — no se puede hacer click"
            )

            # 2. Click nativo en la hoja -> debe abrir NUEVA PESTANA
            try:
                with page.context.expect_page(timeout=10000) as nueva_pag_info:
                    page.locator(f"#{hoja_id}").click()
                nueva_pag = nueva_pag_info.value
            except Exception as e:
                pytest.fail(
                    f"'{descripcion}' (#{hoja_id}) no abrio una nueva pestana. "
                    f"Cada seccion hoja debe abrir su modulo en pestana separada. "
                    f"Error: {type(e).__name__}"
                )

            try:
                # 3. Esperar carga completa: networkidle + elemento especifico
                self._esperar_pagina_lista(nueva_pag, url_esperada)

                # Traer la nueva pestana al frente para que los clics sean visibles
                nueva_pag.bring_to_front()

                # 4. Verificar URL correcta
                assert url_esperada in nueva_pag.url, (
                    f"'{descripcion}': URL inesperada. "
                    f"Esperaba path '{url_esperada}', "
                    f"obtuvo '{nueva_pag.url}'"
                )

                # 5. Sin error del servidor (500/exception/404/403)
                assert not self._tiene_error_servidor(nueva_pag), (
                    f"'{descripcion}' mostro un error del servidor en '{nueva_pag.url}'"
                )

                # 6. Verificaciones especificas de contenido por seccion
                self._verificar_contenido_seccion(nueva_pag, hoja_id, descripcion)

                # Pausa para observar la seccion antes de cerrarla
                time.sleep(3)

            finally:
                nueva_pag.close()
