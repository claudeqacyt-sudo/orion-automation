"""
usuarios_page.py — Page Objects para la seccion Usuarios de Orion Contact Center
Selectores verificados contra HTML real de Orion v7.0 (vm-2k22-er-01.orioncontactcenter.com.ar)

Arquitectura: cada sub-seccion abre en una NUEVA PESTANA.
La clase UsuariosNav encapsula la apertura de cada pestana.
Las clases de seccion encapsulan la interaccion dentro de cada pestana.
"""
import time
from playwright.sync_api import Page, expect
from pages.base_page import BasePage


# ─────────────────────────────────────────────────────────────────────────────
# Navegacion: abrir sub-secciones desde el menu principal
# ─────────────────────────────────────────────────────────────────────────────

class UsuariosNav:
    """
    Encapsula la navegacion al menu Usuarios.
    Requiere la pagina principal autenticada (shared_page / logged_in_page).
    Cada metodo open_*() abre la sub-seccion en nueva pestana y la devuelve.
    """

    MENU_USUARIOS          = "#accionEjecutar_3"
    MENU_GESTION_PERFILES  = "#accionEjecutar_31"
    MENU_PERMISOS_PERFILES = "#accionEjecutar_32"
    MENU_USUARIOS_PERFILES = "#accionEjecutar_33"
    MENU_USUARIOS_CLIENTES = "#accionEjecutar_34"
    MENU_BLOQUEO           = "#accionEjecutar_35"

    def __init__(self, main_page: Page):
        self.page = main_page

    def _open_section(self, child_selector: str, timeout: int = 15000) -> Page:
        """
        Abre una sub-sección del menú Usuarios en una nueva pestaña.

        Estrategia (tres niveles de fallback):
        1. Clic en padre → polling de bbox del hijo → mouse.click(cx, cy)
        2. Si bbox no encontrado: segundo intento abriendo el dropdown de nuevo
        3. Fallback final: JS element.click() que bypasa restricciones de viewport
        """
        child = self.page.locator(child_selector)

        def _obtener_bbox():
            """Abre el dropdown y espera que el hijo gane dimensiones."""
            # Esperar a que el menú esté en el DOM y visible
            # (la SPA puede tardar en cargar, especialmente tras re-login)
            self.page.locator(self.MENU_USUARIOS).wait_for(state="visible", timeout=15000)
            # JS click bypasa las restricciones de viewport de Playwright
            # (el elemento puede estar fuera del viewport sin ser none)
            self.page.evaluate(
                f"document.querySelector('{self.MENU_USUARIOS}').click()"
            )
            time.sleep(1.0)
            deadline = time.time() + 6
            while time.time() < deadline:
                b = child.bounding_box()
                if b and b["width"] > 0 and b["height"] > 0:
                    return b
                time.sleep(0.2)
            return None

        # Intentar obtener bbox (hasta 2 veces)
        bbox = _obtener_bbox()
        if not bbox:
            bbox = _obtener_bbox()

        # Abrir listener de nueva pestaña y hacer el click
        with self.page.context.expect_page(timeout=timeout) as new_page_info:
            if bbox and bbox["width"] > 0:
                # Opción 1: coordenadas absolutas (más fiable)
                self.page.mouse.click(
                    bbox["x"] + bbox["width"] / 2,
                    bbox["y"] + bbox["height"] / 2,
                )
            else:
                # Opción 2: JS click (bypasa restricciones de viewport de Playwright)
                self.page.evaluate(
                    f"document.querySelector('{child_selector}').click()"
                )

        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(1.5)
        return new_page

    def open_gestion_perfiles(self) -> Page:
        """Abre Usuarios → Gestión de Perfiles. URL: /perfiles"""
        return self._open_section(self.MENU_GESTION_PERFILES)

    def open_permisos_perfiles(self) -> Page:
        """Abre Usuarios → Permisos de Perfiles. URL: /configNivelesFunciones"""
        return self._open_section(self.MENU_PERMISOS_PERFILES)

    def open_usuarios_perfiles(self) -> Page:
        """Abre Usuarios → Usuarios de Perfiles. URL: /configPerfilesAgente"""
        return self._open_section(self.MENU_USUARIOS_PERFILES)

    def open_usuarios_clientes(self) -> Page:
        """Abre Usuarios → Usuarios de Clientes. URL: /configUsuariosClientes"""
        return self._open_section(self.MENU_USUARIOS_CLIENTES)

    def open_bloqueo_usuarios(self) -> Page:
        """Abre Usuarios → Bloqueo de Usuarios. URL: /GestorUsuariosBloqueados"""
        return self._open_section(self.MENU_BLOQUEO)


# ─────────────────────────────────────────────────────────────────────────────
# Gestion de Perfiles  (/perfiles)
# ─────────────────────────────────────────────────────────────────────────────

class GestionPerfilesPage(BasePage):
    """
    Page Object para Usuarios → Gestión de Perfiles
    URL: /perfiles

    Estructura verificada contra HTML real:
    - La tabla lista perfiles; click en una fila abre modal de edición.
    - Botón Nuevo abre modal de creación (distinto ID al de edición).
    - Los perfiles base (Administrador/Agente/Supervisor) tienen 'Eliminar' DISABLED.
    """

    URL_PATH = "/perfiles"

    # ── Tabla principal ──────────────────────────────────────────────
    TABLE         = "#dt-perfiles"
    TABLE_ROWS    = "#dt-perfiles tbody tr"
    TABLE_HEADERS = "#dt-perfiles thead th"
    TABLE_FIRST_COL = "#dt-perfiles tbody tr td:first-child"
    MSG_SIN_DATOS = "Ningún dato disponible en esta tabla"

    # ── Filtro de búsqueda ───────────────────────────────────────────
    INPUT_FILTRO  = "#filtroNombre"
    BTN_BUSCAR    = "#btnBuscar"

    # ── Acciones principales ─────────────────────────────────────────
    BTN_NUEVO     = "#btnNuevo"

    # ── Modal de EDICIÓN (click en fila)  — #modalGlobal3Botones ─────
    # Tiene 3 botones: OK / Eliminar (disabled en perfiles base) / Cancelar
    # IMPORTANTE: los campos #inputID y #Descripcion existen en AMBOS modales
    # (aunque uno esté oculto). Los selectores se scopean al modal específico.
    MODAL_EDICION         = "#modalGlobal3Botones"
    MODAL_EDICION_TITULO  = "#modalGlobal3Botones .modal-title"
    MODAL_EDICION_ID      = "#modalGlobal3Botones #inputID"    # disabled — solo lectura
    MODAL_EDICION_DESC    = "#modalGlobal3Botones #Descripcion" # editable
    BTN_MODAL_EDIT_OK     = "#modalGlobal3Botones_uno"
    BTN_MODAL_EDIT_ELIM   = "#modalGlobal3Botones_dos"   # DISABLED en perfiles base
    BTN_MODAL_EDIT_CANCEL = "#modalGlobal3Botones_tres"

    # ── Modal de CREACIÓN (Botón Nuevo)  — #modalGlobal2Botones ──────
    # Tiene 2 botones: OK / Cancelar  (sin Eliminar)
    # IMPORTANTE: el campo #inputID está DESHABILITADO en modo creación
    # (el ID es auto-generado por el sistema). Solo #Descripcion es editable.
    MODAL_NUEVO         = "#modalGlobal2Botones"
    MODAL_NUEVO_TITULO  = "#modalGlobal2Botones .modal-title"
    MODAL_NUEVO_ID      = "#modalGlobal2Botones #inputID"    # DISABLED — auto-generado
    MODAL_NUEVO_DESC    = "#modalGlobal2Botones #Descripcion" # único campo editable
    BTN_MODAL_NUEVO_OK  = "#modalGlobal2Botones_uno"
    BTN_MODAL_NUEVO_CAN = "#modalGlobal2Botones_dos"

    # ── Modal de éxito (POST creación/edición) ───────────────────────
    # Aparece tras guardar: "El perfil se ha agregado de manera exitosa"
    MODAL_INFO    = "#modalGlobalGenericoInfo"
    BTN_INFO_OK   = "#modalGlobalGenericoInfo_btnOK"

    # ── Modal de confirmación de ELIMINACIÓN ─────────────────────────
    # Aparece al hacer click en Eliminar: "¿ Desea eliminar el registro ?"
    MODAL_CONFIRM      = "#modalGlobalGenericoConfirmar"
    BTN_CONFIRM_SI     = "#modalGlobalGenericoConfirmar_confirm"
    BTN_CONFIRM_NO     = "#modalGlobalGenericoConfirmar_cancel"

    # ── Datos esperados del sistema ──────────────────────────────────
    EXPECTED_COLUMNS = ["Descripción"]
    PERFILES_BASE    = ["Administrador", "Agente", "Supervisor"]

    def __init__(self, page: Page):
        super().__init__(page)

    # ── Carga ────────────────────────────────────────────────────────

    def wait_for_load(self):
        """Esperar a que la tabla de perfiles esté visible."""
        self.page.locator(self.TABLE).wait_for(state="visible", timeout=self.timeout)

    def verify_page_loaded(self):
        """Verificar que la página cargó correctamente."""
        expect(self.page.locator(self.TABLE)).to_be_visible(timeout=self.timeout)
        expect(self.page.locator(self.BTN_NUEVO)).to_be_visible(timeout=self.timeout)
        expect(self.page.locator(self.BTN_BUSCAR)).to_be_visible(timeout=self.timeout)

    # ── Tabla ────────────────────────────────────────────────────────

    def get_column_headers(self) -> list[str]:
        headers = self.page.locator(self.TABLE_HEADERS).all()
        return [h.inner_text().strip() for h in headers if h.inner_text().strip()]

    def get_profile_names(self) -> list[str]:
        """Retorna la lista de nombres de perfiles visibles en la tabla."""
        rows = self.page.locator(self.TABLE_FIRST_COL).all()
        return [r.inner_text().strip() for r in rows
                if r.inner_text().strip() and r.inner_text().strip() != self.MSG_SIN_DATOS]

    def get_row_count(self) -> int:
        return self.page.locator(self.TABLE_ROWS).count()

    def click_fila(self, index: int):
        """
        Click en la fila N (base-1) para abrir el modal de edición.
        Usa coordenadas absolutas para evitar problemas con el contenedor
        de scroll de DataTables.
        """
        cell = self.page.locator(
            f"#dt-perfiles tbody tr:nth-child({index}) td:first-child"
        )
        cell.wait_for(state="visible", timeout=self.timeout)
        bbox = cell.bounding_box()
        if bbox:
            self.page.mouse.click(
                bbox["x"] + bbox["width"] / 2,
                bbox["y"] + bbox["height"] / 2
            )
        else:
            # Fallback: click directo con force
            cell.click(force=True)
        # Esperar a que aparezca el modal (máx 5 seg)
        try:
            self.page.locator(self.MODAL_EDICION).wait_for(
                state="visible", timeout=5000
            )
        except Exception:
            time.sleep(2)  # Fallback si el wait falla

    # ── Filtro ───────────────────────────────────────────────────────

    def buscar(self, nombre: str):
        self.page.locator(self.INPUT_FILTRO).fill(nombre)
        self.page.locator(self.BTN_BUSCAR).click()
        time.sleep(1)

    def limpiar_filtro(self):
        self.page.locator(self.INPUT_FILTRO).fill("")
        self.page.locator(self.BTN_BUSCAR).click()
        time.sleep(1)

    # ── Modal Edición ────────────────────────────────────────────────

    def modal_edicion_esta_abierto(self) -> bool:
        m = self.page.locator(self.MODAL_EDICION)
        return m.is_visible()

    def get_modal_edicion_id(self) -> str:
        return self.page.locator(self.MODAL_EDICION_ID).input_value()

    def get_modal_edicion_desc(self) -> str:
        return self.page.locator(self.MODAL_EDICION_DESC).input_value()

    def eliminar_esta_habilitado(self) -> bool:
        return self.page.locator(self.BTN_MODAL_EDIT_ELIM).is_enabled()

    def cancelar_edicion(self):
        self.page.locator(self.BTN_MODAL_EDIT_CANCEL).click()
        time.sleep(0.8)

    def guardar_edicion(self):
        self.page.locator(self.BTN_MODAL_EDIT_OK).click()
        time.sleep(1)

    # ── Modal Nuevo ──────────────────────────────────────────────────

    def click_nuevo(self):
        self.page.locator(self.BTN_NUEVO).click()
        try:
            self.page.locator(self.MODAL_NUEVO).wait_for(
                state="visible", timeout=5000
            )
        except Exception:
            time.sleep(1.5)

    def modal_nuevo_esta_abierto(self) -> bool:
        return self.page.locator(self.MODAL_NUEVO).is_visible()

    def cancelar_nuevo(self):
        self.page.locator(self.BTN_MODAL_NUEVO_CAN).click()
        time.sleep(0.8)

    def guardar_nuevo(self):
        self.page.locator(self.BTN_MODAL_NUEVO_OK).click()
        time.sleep(1)

    # ── Modal Confirmación de éxito ──────────────────────────────────

    def cerrar_modal_info(self):
        btn = self.page.locator(self.BTN_INFO_OK)
        if btn.is_visible():
            btn.click()
            time.sleep(0.5)

    def modal_info_esta_abierto(self) -> bool:
        return self.page.locator(self.MODAL_INFO).is_visible()

    def get_modal_info_texto(self) -> str:
        """Retorna el texto del body del modal de información/éxito."""
        try:
            return self.page.locator(f"{self.MODAL_INFO} .modal-body").inner_text().strip()
        except Exception:
            return ""

    # ── CRUD completo ────────────────────────────────────────────────

    def crear_perfil(self, descripcion: str) -> None:
        """
        Crea un perfil nuevo llenando solo el campo Descripción
        (el ID es auto-generado por el sistema y el campo está deshabilitado).
        Cierra el modal de éxito automáticamente.
        Lanza AssertionError si el perfil no se pudo crear.
        """
        self.click_nuevo()
        assert self.modal_nuevo_esta_abierto(), "El modal de creación no se abrió"

        # Verificar que el campo ID está deshabilitado (auto-generado)
        campo_id = self.page.locator(self.MODAL_NUEVO_ID)
        assert not campo_id.is_enabled(), \
            "El campo ID debería estar deshabilitado (auto-generado) en modo creación"

        # Rellenar solo la descripción
        self.page.locator(self.MODAL_NUEVO_DESC).fill(descripcion)
        time.sleep(0.3)

        # Guardar
        self.page.locator(self.BTN_MODAL_NUEVO_OK).click()
        time.sleep(1.5)

        # Cerrar modal de éxito
        if self.modal_info_esta_abierto():
            texto = self.get_modal_info_texto()
            self.cerrar_modal_info()
            assert "exitosa" in texto.lower() or "agregado" in texto.lower(), \
                f"Mensaje de éxito inesperado: {texto!r}"

    def eliminar_perfil_seleccionado(self) -> bool:
        """
        Desde el modal de edición (abierto sobre el perfil), hace clic en Eliminar
        y confirma con 'Sí' en el modal de confirmación.
        Solo procede si Eliminar está habilitado.
        Retorna True si se eliminó, False si Eliminar estaba deshabilitado.
        """
        btn_elim = self.page.locator(self.BTN_MODAL_EDIT_ELIM)
        if not btn_elim.is_enabled():
            return False

        btn_elim.click()
        time.sleep(1)

        # Modal de confirmación "¿ Desea eliminar el registro ?"
        try:
            self.page.locator(self.MODAL_CONFIRM).wait_for(state="visible", timeout=5000)
        except Exception:
            time.sleep(1)

        btn_si = self.page.locator(self.BTN_CONFIRM_SI)
        assert btn_si.is_visible(), "Botón 'Sí' no visible en modal de confirmación"
        btn_si.click()
        time.sleep(1.5)

        return True

    def perfil_existe_en_tabla(self, descripcion: str) -> bool:
        """Verifica si un perfil con esa descripción aparece en la tabla."""
        nombres = self.get_profile_names()
        return any(descripcion.lower() in n.lower() for n in nombres)

    def get_fila_por_descripcion(self, descripcion: str) -> int | None:
        """
        Retorna el índice (base-1) de la fila cuya primera columna contiene la descripción.
        Retorna None si no se encontró.
        """
        rows = self.page.locator(self.TABLE_FIRST_COL).all()
        for i, row in enumerate(rows, start=1):
            texto = row.inner_text().strip()
            if descripcion.lower() in texto.lower():
                return i
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Permisos de Perfiles  (/configNivelesFunciones)
# ─────────────────────────────────────────────────────────────────────────────

class PermisosPerfilesPage(BasePage):
    """
    Page Object para Usuarios → Permisos de Perfiles
    URL: /configNivelesFunciones

    Estructura DOM verificada:
    - #cmbNivel            → select con 3 perfiles
    - #txtFiltro           → input de búsqueda de permisos
    - #chkSelectAll        → checkbox oculto "Todos los permisos" (solo activo en Administrador)
    - ul#lsConfiguracion   → lista de 66 permisos (64 para Agente)
      └── li > label.single-selector.with-switch
              ├── span > span.fa + span (nombre del permiso)
              └── span.switch > input[type="checkbox"][value="{id}"] + span.slider.round

    Los checkboxes son VISUALMENTE OCULTOS (toggle switch CSS-only).
    Para leer estado usar input.checked; para interactuar click en el label padre.

    Permisos por perfil (estado base del sistema):
      Administrador : 66 permisos, 66 activos   (todos)
      Supervisor    : 66 permisos, 23 activos
      Agente        : 64 permisos, 12 activos
    """

    URL_PATH = "/configNivelesFunciones"

    # ── Selectores principales ───────────────────────────────────────
    SELECT_PERFIL     = "#cmbNivel"
    INPUT_FILTRO      = "#txtFiltro"
    CHK_SELECT_ALL    = "#chkSelectAll"
    LISTA_PERMISOS    = "#lsConfiguracion"
    ITEMS_PERMISOS    = "#lsConfiguracion li"
    # Checkbox oculto de cada permiso (dentro de cada li)
    CHECKBOX_PERMISO  = "#lsConfiguracion li input[type='checkbox']"

    # ── Datos esperados del sistema (estado base) ────────────────────
    PERFILES_OPCIONES = ["Administrador", "Supervisor", "Agente"]

    # Total de permisos por perfil (estado base del sistema)
    TOTAL_PERMISOS = {
        "Administrador": 66,
        "Supervisor":    66,
        "Agente":        64,
    }
    # Cantidad de permisos ACTIVOS por perfil (estado base)
    ACTIVOS_PERMISOS = {
        "Administrador": 66,
        "Supervisor":    23,
        "Agente":        12,
    }

    # Permisos que DEBE tener el Administrador (sample representativo)
    PERMISOS_ADMIN_CRITICOS = [
        "Permite crear perfiles",
        "Permite modificar perfiles",
        "Permite eliminar perfiles",
        "Permite asignar permisos a perfiles",
        "Permite asignar usuarios a perfiles",
        "Permite crear contactos",
    ]

    # Permisos que el Agente NO debe tener
    PERMISOS_BLOQUEADOS_AGENTE = [
        "Permite crear perfiles",
        "Permite eliminar perfiles",
        "Permite asignar permisos a perfiles",
    ]

    def __init__(self, page: Page):
        super().__init__(page)

    # ── Carga ────────────────────────────────────────────────────────

    def wait_for_load(self):
        """Esperar a que el select de perfiles esté visible."""
        self.page.locator(self.SELECT_PERFIL).wait_for(state="visible", timeout=self.timeout)
        # Esperar también que la lista de permisos cargue
        self.page.locator(self.LISTA_PERMISOS).wait_for(state="visible", timeout=self.timeout)

    def verify_page_loaded(self):
        expect(self.page.locator(self.SELECT_PERFIL)).to_be_visible(timeout=self.timeout)
        expect(self.page.locator(self.INPUT_FILTRO)).to_be_visible(timeout=self.timeout)

    # ── Select de perfil ─────────────────────────────────────────────

    def get_perfiles_disponibles(self) -> list[str]:
        """Retorna los nombres de los perfiles en el select."""
        options = self.page.locator(f"{self.SELECT_PERFIL} option").all()
        return [o.inner_text().strip() for o in options if o.inner_text().strip()]

    def seleccionar_perfil(self, nombre: str):
        """Selecciona un perfil y espera que la lista se actualice."""
        self.page.locator(self.SELECT_PERFIL).select_option(label=nombre)
        time.sleep(1.5)

    # ── Lista de permisos ─────────────────────────────────────────────

    def get_total_permisos(self) -> int:
        """Retorna el total de ítems en la lista de permisos."""
        return self.page.locator(self.ITEMS_PERMISOS).count()

    def get_permisos_activos_count(self) -> int:
        """Retorna cuántos permisos están activos (checked=True)."""
        return self.page.evaluate("""
            () => Array.from(
                    document.querySelectorAll('#lsConfiguracion li input[type="checkbox"]')
                  ).filter(cb => cb.checked).length
        """)

    def get_nombres_permisos(self) -> list[str]:
        """Retorna la lista de nombres de permisos visibles."""
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll(
                    '#lsConfiguracion li label > span:first-child > span:last-child'
                  )).map(s => s.innerText.trim()).filter(Boolean)
        """)

    def permiso_esta_activo(self, nombre_parcial: str) -> bool:
        """Verifica si un permiso (por coincidencia parcial de nombre) está activo."""
        return self.page.evaluate(f"""
            () => {{
                const items = document.querySelectorAll('#lsConfiguracion li');
                for (const li of items) {{
                    const span = li.querySelector('label > span:first-child > span:last-child');
                    if (span && span.innerText.toLowerCase().includes({nombre_parcial.lower()!r})) {{
                        const cb = li.querySelector('input[type="checkbox"]');
                        return cb ? cb.checked : null;
                    }}
                }}
                return null;
            }}
        """)

    def chk_select_all_activo(self) -> bool:
        """Retorna si el toggle 'Todos los permisos' está activo."""
        return self.page.evaluate(
            "() => document.getElementById('chkSelectAll').checked"
        )

    # ── Filtro ────────────────────────────────────────────────────────

    def filtrar_permisos(self, texto: str):
        """Escribe en el filtro y espera."""
        self.page.locator(self.INPUT_FILTRO).fill(texto)
        time.sleep(0.8)

    def limpiar_filtro(self):
        """Limpia el filtro."""
        self.page.locator(self.INPUT_FILTRO).fill("")
        time.sleep(0.5)

    def get_permisos_visibles_count(self) -> int:
        """Retorna cuántos li de la lista son visibles según computed style."""
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('#lsConfiguracion li'))
                       .filter(li => window.getComputedStyle(li).display !== 'none'
                                  && window.getComputedStyle(li).visibility !== 'hidden')
                       .length
        """)

    def get_nombres_permisos_visibles(self) -> list[str]:
        """Retorna los nombres de los permisos actualmente visibles."""
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('#lsConfiguracion li'))
                       .filter(li => window.getComputedStyle(li).display !== 'none'
                                  && window.getComputedStyle(li).visibility !== 'hidden')
                       .map(li => {
                           const s = li.querySelector('label > span:first-child > span:last-child');
                           return s ? s.innerText.trim() : '';
                       })
                       .filter(Boolean)
        """)


# ─────────────────────────────────────────────────────────────────────────────
# Usuarios de Perfiles  (/configPerfilesAgente)
# ─────────────────────────────────────────────────────────────────────────────

class UsuariosPerfilesPage(BasePage):
    """
    Page Object para Usuarios → Usuarios de Perfiles
    URL: /configPerfilesAgente

    Estructura DOM verificada (exploración real contra Orion v7.0):

    Panel izquierdo  → #selPerfilIzquierda  · #txtFiltroUsuariosIzquierda
                       #tablaAgentesExcluidos  (ul.list-group)
    Panel derecho    → #selPerfilDerecha    · #txtFiltroUsuariosDerecha
                       #tablaAgentesIncluidos  (ul.list-group)
    Botones          → #btnAsignarPerfil (→) · #btnQuitarPerfil (←)

    Semántica de los paneles:
    - Cada panel muestra los usuarios ASIGNADOS al perfil de su selector.
    - Los dos selectores son INDEPENDIENTES (pueden mostrar perfiles distintos).
    - La página previene seleccionar el mismo perfil en ambos paneles al mismo tiempo.
    - btnAsignarPerfil (→): transfiere el usuario seleccionado del panel IZQ al perfil DER.
    - btnQuitarPerfil  (←): transfiere el usuario seleccionado del panel DER al perfil IZQ.

    Estructura li:
      <li class="">
        <label class="single-selector">
          <input type="checkbox" name="listaChecksDer" value="N">
          <span class="fa fa-circle-o unchecked"></span>
          <span class="fa fa-check-circle-o checked"></span>
          <span class="fa fa-user-circle"></span>
          <span>NOMBRE USUARIO</span>
        </label>
      </li>

    Estado base del sistema (verificado):
      Administrador: 1 usuario  → "cyt usuario inicial"
      Supervisor:    0 usuarios
      Agente:        5 usuarios → "1000 - Agente Genérico" … "1004 - Agente Genérico"
    """

    URL_PATH = "/configPerfilesAgente"

    # ── Selectores ──────────────────────────────────────────────────
    SELECT_PERFIL_IZQ = "#selPerfilIzquierda"
    SELECT_PERFIL_DER = "#selPerfilDerecha"
    FILTRO_IZQ        = "#txtFiltroUsuariosIzquierda"
    FILTRO_DER        = "#txtFiltroUsuariosDerecha"
    TABLA_IZQ         = "#tablaAgentesExcluidos"
    TABLA_DER         = "#tablaAgentesIncluidos"
    ITEMS_IZQ         = "#tablaAgentesExcluidos li"
    ITEMS_DER         = "#tablaAgentesIncluidos li"
    BTN_ASIGNAR       = "#btnAsignarPerfil"
    BTN_QUITAR        = "#btnQuitarPerfil"

    # ── Datos del sistema (estado base verificado) ───────────────────
    PERFILES        = ["Administrador", "Supervisor", "Agente"]
    PERFILES_VALUES = {"Administrador": "1", "Supervisor": "2", "Agente": "3"}

    # Cantidad de usuarios asignados a cada perfil (estado base)
    USUARIOS_POR_PERFIL = {
        "Administrador": 1,
        "Supervisor":    0,
        "Agente":        5,
    }
    USUARIO_ADMIN  = "cyt usuario inicial"
    TEXTO_AGENTES  = "Agente Genérico"    # texto parcial compartido por todos los agentes

    def __init__(self, page: Page):
        super().__init__(page)

    # ── Carga ────────────────────────────────────────────────────────

    def wait_for_load(self):
        self.page.locator(self.SELECT_PERFIL_IZQ).wait_for(state="visible", timeout=self.timeout)
        self.page.locator(self.SELECT_PERFIL_DER).wait_for(state="visible", timeout=self.timeout)
        time.sleep(1)

    def verify_page_loaded(self):
        assert "/configPerfilesAgente" in self.page.url, \
            f"URL incorrecta: {self.page.url}"
        expect(self.page.locator(self.SELECT_PERFIL_IZQ)).to_be_visible(timeout=self.timeout)
        expect(self.page.locator(self.BTN_ASIGNAR)).to_be_visible(timeout=self.timeout)

    # ── Selects ───────────────────────────────────────────────────────

    def get_opciones_perfil_izquierda(self) -> list[str]:
        """Retorna los nombres de perfil del select izquierdo."""
        return self.page.evaluate("""
            () => Array.from(document.querySelector('#selPerfilIzquierda').options)
                       .map(o => o.text.trim())
        """)

    def get_opciones_perfil_derecha(self) -> list[str]:
        """Retorna los nombres de perfil del select derecho."""
        return self.page.evaluate("""
            () => Array.from(document.querySelector('#selPerfilDerecha').options)
                       .map(o => o.text.trim())
        """)

    def seleccionar_perfil_izquierda(self, nombre: str):
        """Selecciona el perfil en el panel izquierdo y espera la actualización."""
        self.page.locator(self.SELECT_PERFIL_IZQ).select_option(
            value=self.PERFILES_VALUES[nombre]
        )
        time.sleep(1.5)

    def seleccionar_perfil_derecha(self, nombre: str):
        """Selecciona el perfil en el panel derecho y espera la actualización."""
        self.page.locator(self.SELECT_PERFIL_DER).select_option(
            value=self.PERFILES_VALUES[nombre]
        )
        time.sleep(1.5)

    # ── Conteo y listado de usuarios ──────────────────────────────────

    def get_count_panel_izquierdo(self) -> int:
        """Total de li en el panel izquierdo."""
        return self.page.evaluate(
            "() => document.querySelectorAll('#tablaAgentesExcluidos li').length"
        )

    def get_count_panel_derecho(self) -> int:
        """Total de li en el panel derecho."""
        return self.page.evaluate(
            "() => document.querySelectorAll('#tablaAgentesIncluidos li').length"
        )

    def get_usuarios_panel_izquierdo(self) -> list[str]:
        """Retorna los nombres de usuario del panel izquierdo."""
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('#tablaAgentesExcluidos li'))
                       .map(li => li.innerText.trim()).filter(Boolean)
        """)

    def get_usuarios_panel_derecho(self) -> list[str]:
        """Retorna los nombres de usuario del panel derecho."""
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('#tablaAgentesIncluidos li'))
                       .map(li => li.innerText.trim()).filter(Boolean)
        """)

    # ── Filtros ───────────────────────────────────────────────────────

    def filtrar_panel_izquierdo(self, texto: str):
        self.page.locator(self.FILTRO_IZQ).fill(texto)
        time.sleep(0.8)

    def filtrar_panel_derecho(self, texto: str):
        self.page.locator(self.FILTRO_DER).fill(texto)
        time.sleep(0.8)

    def limpiar_filtro(self):
        """Limpia ambos filtros de texto."""
        self.page.locator(self.FILTRO_IZQ).fill("")
        self.page.locator(self.FILTRO_DER).fill("")
        time.sleep(0.5)

    def get_count_visibles_panel_izquierdo(self) -> int:
        """Cuenta los li visibles (con altura > 0) en el panel izquierdo."""
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('#tablaAgentesExcluidos li'))
                       .filter(li => li.offsetHeight > 0).length
        """)

    def get_count_visibles_panel_derecho(self) -> int:
        """Cuenta los li visibles (con altura > 0) en el panel derecho."""
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('#tablaAgentesIncluidos li'))
                       .filter(li => li.offsetHeight > 0).length
        """)

    def get_usuarios_visibles_panel_derecho(self) -> list[str]:
        """Retorna los textos de li visibles en el panel derecho (para tests de filtro)."""
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('#tablaAgentesIncluidos li'))
                       .filter(li => li.offsetHeight > 0)
                       .map(li => li.innerText.trim()).filter(Boolean)
        """)

    # ── Selección de usuario y botones de transferencia ───────────────

    def seleccionar_usuario_en_panel_izquierdo(self, index: int = 0):
        """
        Selecciona el usuario N (base-0) del panel izquierdo.
        Usa single-selector: sólo un usuario activo a la vez.
        """
        self.page.locator(self.ITEMS_IZQ).nth(index).locator("label").click()
        time.sleep(0.5)

    def seleccionar_usuario_en_panel_derecho(self, index: int = 0):
        """
        Selecciona el usuario N (base-0) del panel derecho.
        Usa single-selector: sólo un usuario activo a la vez.
        """
        self.page.locator(self.ITEMS_DER).nth(index).locator("label").click()
        time.sleep(0.5)

    def click_asignar(self):
        """
        Hace clic en 'Asignar' (→): transfiere el usuario seleccionado del panel
        izquierdo al perfil del panel derecho.
        """
        self.page.locator(self.BTN_ASIGNAR).click()
        time.sleep(1.5)

    def click_quitar(self):
        """
        Hace clic en 'Quitar' (←): transfiere el usuario seleccionado del panel
        derecho al perfil del panel izquierdo.
        """
        self.page.locator(self.BTN_QUITAR).click()
        time.sleep(1.5)


# ─────────────────────────────────────────────────────────────────────────────
# Usuarios de Clientes  (/configUsuariosClientes)
# ─────────────────────────────────────────────────────────────────────────────

class UsuariosClientesPage(BasePage):
    """
    Page Object para Usuarios → Usuarios de Clientes
    URL: /configUsuariosClientes

    Estructura DOM verificada (exploración real contra Orion v7.0):

    #cmbCliente           → select con clientes disponibles
    ul.module-check-list  → contenedor del panel de asignación
      └── li > label[for="chkSelectAll"] + input#chkSelectAll → "Todos los usuarios"
      └── ul#lsConfiguracion.list-group
            └── li > label.single-selector
                  └── input[type="checkbox"][value="N"] (checked=asignado)
                      + span con nombre del usuario
    #txtFiltro            → input "Búsqueda rápida"

    Asignación: toggles de checkbox con auto-save (NO tiene botón Guardar).
    Clicking el label del li cambia el estado de asignación inmediatamente.

    NOTA: el filtro #txtFiltro NO modifica el DOM (no oculta li via CSS).
    Comportamiento verificado con diagnóstico DOM.

    Estado base del sistema (verificado):
      Clientes: 1 → "Cliente generico" (value="1")
      Usuarios: 5 (1000 al 1004 – Agente Genérico), todos asignados (checked=True)
      chkSelectAll: checked=True (todos asignados)
    """

    URL_PATH = "/configUsuariosClientes"

    # ── Selectores ──────────────────────────────────────────────────
    SELECT_CLIENTE = "#cmbCliente"
    CHK_SELECT_ALL = "#chkSelectAll"
    LISTA_USUARIOS = "#lsConfiguracion"
    ITEMS_USUARIOS = "#lsConfiguracion li"
    INPUT_FILTRO   = "#txtFiltro"

    # ── Datos del sistema (estado base verificado) ───────────────────
    CLIENTE_BASE   = "Cliente generico"
    TOTAL_USUARIOS = 5   # 1000-1004, todos asignados a Cliente generico

    def __init__(self, page: Page):
        super().__init__(page)

    # ── Carga ────────────────────────────────────────────────────────

    def wait_for_load(self):
        self.page.locator(self.SELECT_CLIENTE).wait_for(state="visible", timeout=self.timeout)
        self.page.locator(self.LISTA_USUARIOS).wait_for(state="visible", timeout=self.timeout)
        time.sleep(1)

    def verify_page_loaded(self):
        assert "/configUsuariosClientes" in self.page.url, \
            f"URL incorrecta: {self.page.url}"
        expect(self.page.locator(self.SELECT_CLIENTE)).to_be_visible(timeout=self.timeout)

    # ── Select de cliente ─────────────────────────────────────────────

    def get_clientes_disponibles(self) -> list[str]:
        """Retorna los nombres de clientes en el select."""
        return self.page.evaluate("""
            () => Array.from(document.querySelector('#cmbCliente').options)
                       .map(o => o.text.trim())
        """)

    def seleccionar_cliente(self, nombre: str):
        self.page.locator(self.SELECT_CLIENTE).select_option(label=nombre)
        time.sleep(1.5)

    # ── Lista de usuarios ─────────────────────────────────────────────

    def get_total_usuarios(self) -> int:
        """Total de usuarios en la lista (independiente del estado del checkbox)."""
        return self.page.evaluate(
            "() => document.querySelectorAll('#lsConfiguracion li').length"
        )

    def get_usuarios_asignados_count(self) -> int:
        """Cantidad de usuarios con checkbox marcado (asignados al cliente)."""
        return self.page.evaluate("""
            () => Array.from(
                    document.querySelectorAll('#lsConfiguracion li input[type="checkbox"]')
                  ).filter(cb => cb.checked).length
        """)

    def get_nombres_usuarios(self) -> list[str]:
        """Retorna los nombres de todos los usuarios en la lista."""
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('#lsConfiguracion li'))
                       .map(li => li.innerText.trim()).filter(Boolean)
        """)

    def chk_select_all_activo(self) -> bool:
        """Retorna True si el toggle 'Todos los usuarios' está marcado."""
        return self.page.evaluate(
            "() => document.getElementById('chkSelectAll').checked"
        )

    def get_estado_usuario(self, index: int) -> bool | None:
        """
        Retorna el estado del checkbox del usuario N (base-0).
        True=asignado, False=no asignado, None=no existe.
        """
        return self.page.evaluate(f"""
            () => {{
                const cb = document.querySelectorAll(
                    '#lsConfiguracion li input[type="checkbox"]'
                )[{index}];
                return cb !== undefined ? cb.checked : null;
            }}
        """)

    # ── Toggle de asignación ──────────────────────────────────────────

    def toggle_usuario(self, index: int):
        """
        Cambia el estado de asignación del usuario N (base-0) haciendo click en su label.
        La página auto-guarda el cambio inmediatamente.
        """
        self.page.locator(self.ITEMS_USUARIOS).nth(index).locator("label").click()
        time.sleep(1.5)   # esperar auto-save AJAX

    # ── Filtro ────────────────────────────────────────────────────────

    def filtrar_usuarios(self, texto: str):
        self.page.locator(self.INPUT_FILTRO).fill(texto)
        time.sleep(0.8)

    def limpiar_filtro(self):
        self.page.locator(self.INPUT_FILTRO).fill("")
        time.sleep(0.5)


# ─────────────────────────────────────────────────────────────────────────────
# Bloqueo de Usuarios  (/GestorUsuariosBloqueados)
# ─────────────────────────────────────────────────────────────────────────────

class BloqueoUsuariosPage(BasePage):
    """
    Page Object para Usuarios → Bloqueo de Usuarios
    URL: /GestorUsuariosBloqueados

    Estructura DOM verificada (exploración real contra Orion v7.0):

    Título: "Bloqueo y reinicio de contraseñas"
    Panel: #panelPassBlockReset

    Filtros en #frmUserFilter:
      #cmbClientes          → select: "0"=[Cualquier cliente], "1"=Cliente generico
      #cmbNiveles           → select: "0"=[Cualquier perfil], "1"=Administrador,
                                       "2"=Supervisor, "3"=Agente
      #cmbListas            → select: ""=[Listar todos], "1"=Listar Habilitados,
                                       "2"=Listar Bloqueados
      #txtFiltrarUsuarios   → input, placeholder "Nombre de usuario o número de agente..."

    Listas de usuarios:
      #activeUserList   (ul.user-list.active-user-list)  → usuarios habilitados
      #blockedUserList  (ul.user-list.blocked-user-list) → usuarios bloqueados

    Estructura de cada li en las listas:
      <li class="user" data-fclient="1 " data-fnivel="3" data-fstate="2">
        <article class="user-item">
          <div class="user-data-group">
            <strong class="user-name">1000 - Agente Genérico</strong>
          </div>
          <div class="user-operations">
            <button class="btn-reset-pass circle-button-sm" data-user="..."></button>
            <button class="btn-block-pass circle-button-sm" data-user="..."></button>
          </div>
        </article>
        <label class="check-item">
          <input type="checkbox" class="cyt-check" value="2__3__1000__">
        </label>
      </li>

    Botones de selección múltiple:
      #btnSeleccionarVariosActivos    → activa modo selección en lista activos
      #btnSeleccionarVariosBloqueados → activa modo selección en lista bloqueados
      #chkSelectAllActiveUsers        → checkbox "seleccionar todos" en activos
      #chkSelectAllBlockedUsers       → checkbox "seleccionar todos" en bloqueados

    Estado base del sistema (verificado):
      Activos:    6 (1000-1004 Agente Genérico + cyt usuario inicial)
      Bloqueados: 0
    """

    URL_PATH = "/GestorUsuariosBloqueados"

    # ── Filtros ──────────────────────────────────────────────────────────
    FORM_FILTRO       = "#frmUserFilter"
    SELECT_CLIENTE    = "#cmbClientes"
    SELECT_PERFIL     = "#cmbNiveles"
    SELECT_ESTADO     = "#cmbListas"
    INPUT_FILTRO      = "#txtFiltrarUsuarios"

    # ── Listas de usuarios ───────────────────────────────────────────────
    LISTA_ACTIVOS     = "#activeUserList"
    LISTA_BLOQUEADOS  = "#blockedUserList"
    ITEMS_ACTIVOS     = "#activeUserList li.user"
    ITEMS_BLOQUEADOS  = "#blockedUserList li.user"

    # ── Botones de selección múltiple ────────────────────────────────────
    BTN_SELECT_ACTIVOS    = "#btnSeleccionarVariosActivos"
    BTN_SELECT_BLOQUEADOS = "#btnSeleccionarVariosBloqueados"
    CHK_ALL_ACTIVOS       = "#chkSelectAllActiveUsers"
    CHK_ALL_BLOQUEADOS    = "#chkSelectAllBlockedUsers"

    # ── Valores de los selects ───────────────────────────────────────────
    CLIENTE_CUALQUIERA    = "0"    # [Cualquier cliente]
    CLIENTE_GENERICO      = "1"    # Cliente generico
    PERFIL_CUALQUIERA     = "0"    # [Cualquier perfil]
    PERFIL_ADMIN          = "1"    # Administrador
    PERFIL_SUPERVISOR     = "2"    # Supervisor
    PERFIL_AGENTE         = "3"    # Agente
    ESTADO_TODOS          = ""     # [Listar todos]
    ESTADO_HABILITADOS    = "1"    # Listar Habilitados
    ESTADO_BLOQUEADOS_VAL = "2"    # Listar Bloqueados

    # ── Modales ──────────────────────────────────────────────────────────
    MODAL_CONFIRM  = "#modalGlobalGenericoConfirmar"
    BTN_CONFIRM_SI = "#modalGlobalGenericoConfirmar_confirm"
    BTN_CONFIRM_NO = "#modalGlobalGenericoConfirmar_cancel"
    MODAL_INFO     = "#modalGlobalGenericoInfo"
    BTN_INFO_OK    = "#modalGlobalGenericoInfo_btnOK"

    # ── Estado base del sistema ──────────────────────────────────────────
    TOTAL_ACTIVOS    = 6    # 5 agentes (1000-1004) + 1 admin (cyt)
    TOTAL_BLOQUEADOS = 0    # ninguno bloqueado en estado base

    def __init__(self, page: Page):
        super().__init__(page)

    # ── Carga ────────────────────────────────────────────────────────────

    def wait_for_load(self):
        """Espera a que el panel de filtros y la lista de activos estén visibles."""
        self.page.locator(self.SELECT_CLIENTE).wait_for(state="visible", timeout=self.timeout)
        self.page.locator(self.LISTA_ACTIVOS).wait_for(state="visible", timeout=self.timeout)
        time.sleep(1)

    def verify_page_loaded(self):
        assert "/GestorUsuariosBloqueados" in self.page.url, \
            f"URL incorrecta: {self.page.url}"
        expect(self.page.locator(self.SELECT_CLIENTE)).to_be_visible(timeout=self.timeout)
        expect(self.page.locator(self.INPUT_FILTRO)).to_be_visible(timeout=self.timeout)
        expect(self.page.locator(self.LISTA_ACTIVOS)).to_be_visible(timeout=self.timeout)

    # ── Conteo y listado de usuarios ─────────────────────────────────────

    def get_count_activos(self) -> int:
        """Cantidad de li.user en la lista de activos (#activeUserList)."""
        return self.page.evaluate(
            "() => document.querySelectorAll('#activeUserList li.user').length"
        )

    def get_count_bloqueados(self) -> int:
        """Cantidad de li.user en la lista de bloqueados (#blockedUserList)."""
        return self.page.evaluate(
            "() => document.querySelectorAll('#blockedUserList li.user').length"
        )

    def get_nombres_activos(self) -> list[str]:
        """Retorna los nombres de usuarios en la lista de activos."""
        return self.page.evaluate("""
            () => Array.from(
                    document.querySelectorAll('#activeUserList li.user .user-name')
                  ).map(el => el.textContent.trim()).filter(Boolean)
        """)

    def get_nombres_bloqueados(self) -> list[str]:
        """Retorna los nombres de usuarios en la lista de bloqueados."""
        return self.page.evaluate("""
            () => Array.from(
                    document.querySelectorAll('#blockedUserList li.user .user-name')
                  ).map(el => el.textContent.trim()).filter(Boolean)
        """)

    def get_opciones_select(self, selector: str) -> list[dict]:
        """Retorna las opciones de un select como lista de {value, text}."""
        return self.page.evaluate(f"""
            () => Array.from(document.querySelector('{selector}').options)
                       .map(o => ({{value: o.value, text: o.text.trim()}}))
        """)

    # ── Filtros ──────────────────────────────────────────────────────────

    def seleccionar_cliente(self, valor: str):
        """Selecciona en #cmbClientes por valor."""
        self.page.locator(self.SELECT_CLIENTE).select_option(value=valor)
        time.sleep(1)

    def seleccionar_perfil(self, valor: str):
        """Selecciona en #cmbNiveles por valor."""
        self.page.locator(self.SELECT_PERFIL).select_option(value=valor)
        time.sleep(1)

    def seleccionar_estado(self, valor: str):
        """Selecciona en #cmbListas por valor."""
        self.page.locator(self.SELECT_ESTADO).select_option(value=valor)
        time.sleep(1)

    def filtrar_por_texto(self, texto: str):
        """Escribe en el campo de filtro de texto."""
        self.page.locator(self.INPUT_FILTRO).fill(texto)
        time.sleep(0.8)

    def limpiar_filtros(self):
        """Restablece todos los filtros a su estado inicial (primera opción de cada select)."""
        self.page.locator(self.INPUT_FILTRO).fill("")
        self.page.locator(self.SELECT_CLIENTE).select_option(index=0)
        self.page.locator(self.SELECT_PERFIL).select_option(index=0)
        self.page.locator(self.SELECT_ESTADO).select_option(index=0)
        time.sleep(1)

    # ── Operaciones sobre usuarios ───────────────────────────────────────

    # ── Constantes del modal de desbloqueo ─────────────────────────────
    # El modal de desbloqueo (#modalGlobal3Botones) pregunta:
    # "¿Desea también restablecer la contraseña?"
    # Sí = desbloquear + resetear password; No = solo desbloquear; Cancelar = abortar
    MODAL_UNLOCK       = "#modalGlobal3Botones"
    BTN_UNLOCK_SI      = "#modalGlobal3Botones_uno"    # Sí (desbloquear + reset pass)
    BTN_UNLOCK_NO      = "#modalGlobal3Botones_dos"    # No (solo desbloquear, sin reset)
    BTN_UNLOCK_CANCEL  = "#modalGlobal3Botones_tres"   # Cancelar (no hacer nada)

    def _forzar_ops_visible(self, lista_selector: str, nombre_parcial: str) -> bool:
        """
        Fuerza la visibilidad del div .user-operations del usuario cuyo nombre
        contiene nombre_parcial en la lista indicada (activeUserList o blockedUserList).
        Los botones de operación son CSS-ocultos hasta hover; este método los muestra.
        Retorna True si se encontró el usuario.
        """
        return bool(self.page.evaluate(f"""
            () => {{
                const lis = document.querySelectorAll('{lista_selector} li.user');
                for (const li of lis) {{
                    const nm = li.querySelector('.user-name');
                    if (nm && nm.textContent.includes({nombre_parcial!r})) {{
                        const ops = li.querySelector('.user-operations');
                        if (ops) ops.style.setProperty('display', 'flex', 'important');
                        return true;
                    }}
                }}
                return false;
            }}
        """))

    def bloquear_usuario(self, nombre_parcial: str) -> bool:
        """
        Bloquea el usuario cuyo nombre contiene nombre_parcial en la lista de activos.
        El bloqueo no tiene modal de confirmación — el usuario se mueve inmediatamente.
        Usa JS evaluate para el click (bypasa interceptores CSS del layout).
        Retorna True si se encontró y se hizo clic en btn-block-pass.
        """
        encontrado = self.page.evaluate(f"""
            () => {{
                const lis = document.querySelectorAll('#activeUserList li.user');
                for (const li of lis) {{
                    const nm = li.querySelector('.user-name');
                    if (nm && nm.textContent.includes({nombre_parcial!r})) {{
                        const btn = li.querySelector('.btn-block-pass');
                        if (btn) {{ btn.click(); return true; }}
                    }}
                }}
                return false;
            }}
        """)
        if encontrado:
            time.sleep(1.5)
        return bool(encontrado)

    def desbloquear_usuario_sin_reset(self, nombre_parcial: str) -> bool:
        """
        Desbloquea el usuario cuyo nombre contiene nombre_parcial en la lista de bloqueados.
        Al hacer clic en btn-unlock-pass aparece el modal #modalGlobal3Botones:
          "¿Desea también restablecer la contraseña?"
        Este método hace clic en "No" para desbloquear SIN resetear la contraseña.
        Luego cierra el modal de información que aparece a continuación.
        Retorna True si se encontró el usuario y se completó el flujo.
        """
        if not self._forzar_ops_visible(self.LISTA_BLOQUEADOS, nombre_parcial):
            return False
        time.sleep(0.3)
        blocked_li = (
            self.page.locator(f"{self.LISTA_BLOQUEADOS} li.user")
                .filter(has_text=nombre_parcial)
        )
        unlock_btn = blocked_li.locator('.btn-unlock-pass')
        unlock_btn.click()
        time.sleep(1.2)

        # Modal: "¿Desea también restablecer la contraseña?"
        modal = self.page.locator(self.MODAL_UNLOCK)
        try:
            modal.wait_for(state='visible', timeout=4000)
            self.page.locator(self.BTN_UNLOCK_NO).click()   # "No" — sin reset de contraseña
            time.sleep(1.2)
        except Exception:
            pass

        # Modal de info ("Usuario desbloqueado exitosamente")
        try:
            info = self.page.locator(self.MODAL_INFO)
            if info.is_visible():
                self.page.locator(self.BTN_INFO_OK).click()
                time.sleep(0.8)
        except Exception:
            pass

        time.sleep(1)
        return True

    def modal_unlock_visible(self) -> bool:
        """
        Retorna True si el modal de desbloqueo (#modalGlobal3Botones) está abierto.
        Aparece al hacer clic en btn-unlock-pass en la lista de bloqueados.
        """
        try:
            return self.page.locator(self.MODAL_UNLOCK).is_visible()
        except Exception:
            return False

    def cancelar_modal_unlock(self):
        """Cancela el modal de desbloqueo haciendo clic en 'Cancelar'."""
        try:
            btn = self.page.locator(self.BTN_UNLOCK_CANCEL)
            if btn.is_visible():
                btn.click()
                time.sleep(0.8)
        except Exception:
            pass

    def click_boton_bloquear(self, nombre_parcial: str) -> bool:
        """
        Hace clic en el botón de bloqueo (.btn-block-pass) del usuario cuyo nombre
        contiene nombre_parcial en la lista de activos.
        Usa JS evaluate para bypassar interceptores CSS del layout.
        NO espera ni maneja modal — el bloqueo es inmediato (sin confirmación).
        Retorna True si se encontró el usuario y se hizo clic.
        """
        encontrado = self.page.evaluate(f"""
            () => {{
                const lis = document.querySelectorAll('#activeUserList li.user');
                for (const li of lis) {{
                    const nm = li.querySelector('.user-name');
                    if (nm && nm.textContent.includes({nombre_parcial!r})) {{
                        const btn = li.querySelector('.btn-block-pass');
                        if (btn) {{ btn.click(); return true; }}
                    }}
                }}
                return false;
            }}
        """)
        if encontrado:
            time.sleep(1)
        return bool(encontrado)

    def click_boton_desbloquear(self, nombre_parcial: str) -> bool:
        """
        Hace clic en el botón de desbloqueo (.btn-unlock-pass) del usuario cuyo nombre
        contiene nombre_parcial en la lista de bloqueados.
        NO maneja el modal — el test es responsable.
        Retorna True si se encontró el usuario y se hizo clic.
        """
        if not self._forzar_ops_visible(self.LISTA_BLOQUEADOS, nombre_parcial):
            return False
        time.sleep(0.3)
        blocked_li = (
            self.page.locator(f"{self.LISTA_BLOQUEADOS} li.user")
                .filter(has_text=nombre_parcial)
        )
        blocked_li.locator('.btn-unlock-pass').click()
        time.sleep(1)
        return True
