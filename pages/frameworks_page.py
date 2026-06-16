"""
frameworks_page.py — Page Objects para el modulo Frameworks (Orion Contact Center)
URL base del modulo: https://vm-2k22-fg-01.orioncontactcenter.com.ar:8443
Tecnologia: ASP.NET WebForms (puerto 8443, session separada del gestor principal)

Arquitectura:
  - FrameworksNav  : abre el tab de Orion Contact Center desde el menu principal (puerto 80/443).
  - GestionUsuariosPage : interactua con usuarios.aspx (Configurar > Usuarios > Gestion de Usuarios).

Navegacion verificada:
  1. Desde el menu principal (admincontactos):
     - Click #accionEjecutar_4 (Supervision) → dropdown
     - Click #accionEjecutar_44 (Orion Contact Center) → abre nueva pestana en :8443
  2. Dentro del modulo:
     - URL directa: https://vm-2k22-fg-01.orioncontactcenter.com.ar:8443/usuarios.aspx
     - Via menu hover: Configurar (cy=116) > Usuarios (cy=168) > Gestion de usuarios (cy=168 en sub-menu)

Selectores verificados contra HTML real de Orion v7.0 (vm-2k22-fg-01..., puerto 8443):
  Pagina: usuarios.aspx
    Panel Filtro:
      #ctl00_phContent_txtFechaDesde        — Fecha Desde
      #ctl00_phContent_txtFechaHasta        — Fecha Hasta
      #ctl00_phContent_txtUltimoIngreso     — Ultimo Ingreso
      #ctl00_phContent_txtNombre            — Nombre (filtro)
      #ctl00_phContent_txtApellido          — Apellido (filtro)
      #ctl00_phContent_btnRefrescar         — Buscar/Refrescar (input[type=image])
      #ctl00_phContent_btnLimpiar           — Limpiar filtro (input[type=image])
    Panel Editar / Crear:
      #ctl00_phContent_txtEditId            — ID del usuario (vacio para nuevo)
      #ctl00_phContent_txtEditNombre        — Nombre del usuario *
      #ctl00_phContent_txtEditApellido      — Apellido *
      #ctl00_phContent_txtEditEmail         — E-mail
      #ctl00_phContent_selNiveles           — Nivel: val=1=Administrador, val=2=Supervisor
      #ctl00_phContent_chkVisibilidad       — Visibilidad total (checkbox)
      #ctl00_phContent_chkTieneCRM          — Tiene CRM (checkbox)
      #ctl00_phContent_btnCrear             — CREAR (input[type=submit])
      #ctl00_phContent_btnModificar         — MODIFICAR
      #ctl00_phContent_btnBorrar            — BORRAR
      #ctl00_phContent_btnEditarLimpiar     — LIMPIAR (reset form)
    Resultado post-creacion:
      #ctl00_phContent_lblPasswordRandom    — Mensaje con la password generada
                                              Formato: "Se inicializo la clave, la misma es: XXXXXXXX"
    Grid de usuarios:
      #ctl00_phContent_grdUsuarios          — Tabla de usuarios (GridView ASP.NET)
"""
import re
import time
from playwright.sync_api import Page, expect
from pages.base_page import BasePage


# ─────────────────────────────────────────────────────────────────────────────
# Constantes del modulo
# ─────────────────────────────────────────────────────────────────────────────

FRAMEWORKS_PORT = 444

import os
from dotenv import load_dotenv
load_dotenv()
_base = os.getenv("ORION_BASE_URL", "https://vm-2k22-fg-01.orioncontactcenter.com.ar")
FRAMEWORKS_BASE = f"{_base.rstrip('/')}:{FRAMEWORKS_PORT}"

NIVEL_ADMINISTRADOR = "1"
NIVEL_SUPERVISOR    = "2"

# Mensaje de exito al crear un usuario — prefijo invariante
MSG_CLAVE_PREFIJO = "se inicializo la clave, la misma es:"


# ─────────────────────────────────────────────────────────────────────────────
# FrameworksNav — abre el tab desde el menu principal de Orion
# ─────────────────────────────────────────────────────────────────────────────

class FrameworksNav:
    """
    Encapsula la apertura del modulo Frameworks (Orion Contact Center).
    Requiere la pagina principal autenticada (shared_page / logged_in_page).
    El modulo se abre en una NUEVA PESTANA en el puerto 8443.
    """

    MENU_SUPERVISION       = "#accionEjecutar_4"
    MENU_ORION_CC          = "#accionEjecutar_44"   # Orion Contact Center

    def __init__(self, main_page: Page):
        self.page = main_page

    def open_frameworks(self, timeout: int = 20000) -> Page:
        """
        Abre el modulo Frameworks (Orion Contact Center) desde el menu Supervision.
        Devuelve la nueva pagina (tab) en el puerto 8443.

        Estrategia:
        1. Esperar que el menu este visible.
        2. Abrir dropdown Supervision.
        3. Click en Orion Contact Center → nueva pestana.
        4. Esperar carga inicial.
        """
        # Esperar que el menu este listo
        self.page.locator(self.MENU_SUPERVISION).wait_for(state="visible", timeout=timeout)

        # Abrir dropdown y esperar que accionEjecutar_44 sea visible
        self.page.evaluate(
            f"document.querySelector('{self.MENU_SUPERVISION}').click()"
        )
        try:
            self.page.wait_for_function(
                f"""() => {{
                    const el = document.querySelector('{self.MENU_ORION_CC}');
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    return r.width > 0 && r.height > 0;
                }}""",
                timeout=5000
            )
        except Exception:
            pass

        # Abrir Orion Contact Center → nueva pestana
        with self.page.context.expect_page(timeout=15000) as new_page_info:
            self.page.evaluate(
                f"document.querySelector('{self.MENU_ORION_CC}').click()"
            )

        tab = new_page_info.value
        tab.wait_for_load_state("domcontentloaded", timeout=25000)
        time.sleep(2)
        return tab

    def open_gestion_usuarios(self, timeout: int = 20000) -> "GestionUsuariosPage":
        """
        Abre Frameworks via menú y navega a Gestión de Usuarios via link interno.
        No usa URL directa — sigue el link a usuarios.aspx que está en la página cargada.
        """
        tab = self.open_frameworks(timeout=timeout)
        # El link a usuarios.aspx está en un menú hover — usar JS click para bypasear visibilidad
        tab.wait_for_load_state("domcontentloaded", timeout=20000)
        time.sleep(1.0)
        tab.evaluate("document.querySelector(\"a[href*='usuarios.aspx']\").click()")
        tab.wait_for_load_state("domcontentloaded", timeout=20000)
        time.sleep(1.5)
        page_obj = GestionUsuariosPage(tab)
        page_obj.wait_for_load()
        return page_obj


# ─────────────────────────────────────────────────────────────────────────────
# GestionUsuariosPage — usuarios.aspx
# ─────────────────────────────────────────────────────────────────────────────

class GestionUsuariosPage(BasePage):
    """
    Page Object para Gestion de Usuarios del modulo Frameworks.
    URL: https://vm-2k22-fg-01.orioncontactcenter.com.ar:8443/usuarios.aspx

    La pagina combina:
      - Panel de filtros (izquierda)
      - Panel de edicion/creacion (derecha, titulo "Editar")
      - Grilla de usuarios (abajo)
    """

    URL_PATH = "/usuarios.aspx"

    # ── Panel de filtros ──────────────────────────────────────────────
    INPUT_FILTRO_NOMBRE    = "#ctl00_phContent_txtNombre"
    INPUT_FILTRO_APELLIDO  = "#ctl00_phContent_txtApellido"
    BTN_REFRESCAR          = "#ctl00_phContent_btnRefrescar"
    BTN_LIMPIAR_FILTRO     = "#ctl00_phContent_btnLimpiar"

    # ── Panel de creacion/edicion ─────────────────────────────────────
    INPUT_ID               = "#ctl00_phContent_txtEditId"
    INPUT_NOMBRE           = "#ctl00_phContent_txtEditNombre"
    INPUT_APELLIDO         = "#ctl00_phContent_txtEditApellido"
    INPUT_EMAIL            = "#ctl00_phContent_txtEditEmail"
    SELECT_NIVEL           = "#ctl00_phContent_selNiveles"
    CHK_VISIBILIDAD        = "#ctl00_phContent_chkVisibilidad"
    CHK_TIENE_CRM          = "#ctl00_phContent_chkTieneCRM"

    BTN_CREAR              = "#ctl00_phContent_btnCrear"
    BTN_MODIFICAR          = "#ctl00_phContent_btnModificar"
    BTN_BORRAR             = "#ctl00_phContent_btnBorrar"
    BTN_LIMPIAR_FORM       = "#ctl00_phContent_btnEditarLimpiar"

    # ── Resultado post-creacion ───────────────────────────────────────
    LBL_PASSWORD           = "#ctl00_phContent_lblPasswordRandom"

    # ── Grid de usuarios ─────────────────────────────────────────────
    GRID_USUARIOS          = "#ctl00_phContent_grdUsuarios"

    # ── Opciones del SELECT nivel ─────────────────────────────────────
    NIVEL_ADMINISTRADOR    = "1"
    NIVEL_SUPERVISOR       = "2"

    def __init__(self, page: Page):
        super().__init__(page)

    def wait_for_load(self):
        """Espera que la pagina cargue verificando que el grid de usuarios esta visible."""
        self.page.locator(self.GRID_USUARIOS).wait_for(state="visible", timeout=15000)
        self.page.locator(self.INPUT_NOMBRE).wait_for(state="visible", timeout=10000)

    def verify_page_loaded(self):
        """Verifica que la pagina cargo correctamente."""
        assert self.URL_PATH in self.page.url, \
            f"URL incorrecta: {self.page.url}"
        assert self.page.locator(self.GRID_USUARIOS).is_visible(), \
            "El grid de usuarios no esta visible"
        assert self.page.locator(self.BTN_CREAR).is_visible(), \
            "El boton CREAR no esta visible"

    # ── Acciones del formulario de creacion ───────────────────────────

    def limpiar_formulario(self):
        """Limpia el panel de edicion/creacion."""
        self.page.locator(self.BTN_LIMPIAR_FORM).click()
        time.sleep(0.5)

    def crear_usuario(
        self,
        nombre: str,
        apellido: str,
        nivel: str = NIVEL_SUPERVISOR,
        email: str = "",
        visibilidad: bool = False,
        tiene_crm: bool = False,
    ) -> str:
        """
        Crea un nuevo usuario con los datos especificados.

        Parametros:
          nombre       : nombre/login del usuario (campo Nombre *)
          apellido     : apellido del usuario (campo Apellido *)
          nivel        : '1'=Administrador, '2'=Supervisor
          email        : e-mail (opcional)
          visibilidad  : checkbox Visibilidad total
          tiene_crm    : checkbox Tiene CRM

        Retorna:
          La password generada (str) o '' si no se pudo capturar.
        """
        # Limpiar formulario antes
        self.limpiar_formulario()

        # Nombre
        self.page.locator(self.INPUT_NOMBRE).fill(nombre)

        # Apellido
        self.page.locator(self.INPUT_APELLIDO).fill(apellido)

        # Email
        if email:
            self.page.locator(self.INPUT_EMAIL).fill(email)

        # Nivel
        self.page.locator(self.SELECT_NIVEL).select_option(value=nivel)

        # Visibilidad total
        chk_vis = self.page.locator(self.CHK_VISIBILIDAD)
        if visibilidad and not chk_vis.is_checked():
            chk_vis.click()
        elif not visibilidad and chk_vis.is_checked():
            chk_vis.click()

        # Tiene CRM
        chk_crm = self.page.locator(self.CHK_TIENE_CRM)
        if tiene_crm and not chk_crm.is_checked():
            chk_crm.click()
        elif not tiene_crm and chk_crm.is_checked():
            chk_crm.click()

        # Crear
        self.page.locator(self.BTN_CREAR).click()
        time.sleep(2)

        # Capturar password generada
        return self._capturar_password_generada()

    def _capturar_password_generada(self) -> str:
        """
        Captura la password generada del LBL_PASSWORD.
        Formato del texto: "Se inicializo la clave, la misma es: XXXXXXXX"
        Retorna la password sola o '' si no se encontro.
        """
        try:
            lbl = self.page.locator(self.LBL_PASSWORD)
            if not lbl.is_visible(timeout=5000):
                return ""
            texto = lbl.inner_text().strip()
            # Extraer la password del mensaje
            match = re.search(r'la misma es:\s*(\S+)', texto, re.IGNORECASE)
            if match:
                return match.group(1)
            # Fallback: devolver el texto completo
            return texto
        except Exception:
            return ""

    def get_password_label_text(self) -> str:
        """Retorna el texto completo del label de password (incluyendo el prefijo)."""
        try:
            lbl = self.page.locator(self.LBL_PASSWORD)
            if lbl.is_visible(timeout=3000):
                return lbl.inner_text().strip()
        except Exception:
            pass
        return ""

    # ── Grid de usuarios ─────────────────────────────────────────────

    def get_total_usuarios(self) -> int:
        """Cuenta las filas de datos en el grid (excluye header)."""
        rows = self.page.locator(f"{self.GRID_USUARIOS} tr").all()
        # La primera fila es header, las demas son datos
        # Filtrar filas que tienen al menos 2 celdas TD
        count = 0
        for row in rows[1:]:  # skip header
            tds = row.locator("td").all()
            if len(tds) >= 2:
                count += 1
        return count

    def get_usuarios_en_grid(self) -> list[dict]:
        """
        Retorna lista de dicts con los datos de cada usuario en el grid.
        Keys: id, nombre, apellido, email, nivel_id, nivel_nombre, visibilidad, crm
        """
        rows = self.page.locator(f"{self.GRID_USUARIOS} tr").all()
        usuarios = []
        for row in rows[1:]:  # skip header
            tds = row.locator("td").all()
            if len(tds) < 10:
                continue
            try:
                usuarios.append({
                    "id":            tds[1].inner_text().strip(),
                    "nombre":        tds[2].inner_text().strip(),
                    "apellido":      tds[3].inner_text().strip(),
                    "email":         tds[4].inner_text().strip(),
                    "nivel_id":      tds[8].inner_text().strip(),
                    "nivel_nombre":  tds[9].inner_text().strip(),
                    "visibilidad":   tds[10].inner_text().strip(),
                    "crm":           tds[11].inner_text().strip() if len(tds) > 11 else "",
                })
            except Exception:
                continue
        return usuarios

    def usuario_existe_en_grid(self, nombre: str) -> bool:
        """Verifica si un usuario con ese nombre existe en el grid."""
        usuarios = self.get_usuarios_en_grid()
        return any(u["nombre"].lower() == nombre.lower() for u in usuarios)

    def seleccionar_usuario_en_grid(self, nombre: str) -> bool:
        """
        Hace click en el boton Seleccionar de la fila del usuario indicado.
        Retorna True si lo encontro y clickeo, False si no.
        """
        resultado = self.page.evaluate(f"""
            () => {{
                const rows = Array.from(document.querySelectorAll('#{self.GRID_USUARIOS.lstrip("#")} tr'));
                for (const row of rows) {{
                    const cells = Array.from(row.querySelectorAll('td'));
                    if (cells.length < 3) continue;
                    if (cells[2].innerText.trim().toLowerCase() === '{nombre.lower()}') {{
                        const btn = row.querySelector('input[type="image"]');
                        if (btn) {{ btn.click(); return true; }}
                    }}
                }}
                return false;
            }}
        """)
        if resultado:
            time.sleep(1.0)
        return bool(resultado)

    def borrar_usuario(self, nombre: str) -> bool:
        """
        Selecciona el usuario en el grid y hace click en BORRAR.
        Retorna True si se borro correctamente, False si no se encontro.
        """
        if not self.seleccionar_usuario_en_grid(nombre):
            return False

        # Verificar que el nombre quedo cargado en el form
        nombre_cargado = self.page.locator(self.INPUT_NOMBRE).input_value()
        if nombre.lower() not in nombre_cargado.lower():
            return False

        # Capturar dialogos de confirmacion si los hay
        dialogs = []
        def _accept_dialog(dialog):
            dialogs.append(dialog.message)
            dialog.accept()
        self.page.on("dialog", _accept_dialog)

        self.page.locator(self.BTN_BORRAR).click()
        time.sleep(2)

        # Verificar que desaparecio
        return not self.usuario_existe_en_grid(nombre)

    # ── Filtros ───────────────────────────────────────────────────────

    def filtrar_por_nombre(self, nombre: str):
        """Aplica filtro por nombre y refresca la lista."""
        self.page.locator(self.INPUT_FILTRO_NOMBRE).fill(nombre)
        self.page.locator(self.BTN_REFRESCAR).click()
        time.sleep(1.5)

    def limpiar_filtros(self):
        """Limpia los filtros de busqueda."""
        self.page.locator(self.BTN_LIMPIAR_FILTRO).click()
        time.sleep(1.0)
