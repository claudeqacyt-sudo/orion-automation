"""
supervision_page.py - Page Objects para el modulo Supervision de Orion Contact Center
Selectores verificados contra HTML real de Orion v7.0 (vm-2k22-er-01.orioncontactcenter.com.ar)

Secciones cubiertas:
  - NotificarUsuariosPage (/MensajesUsuarios)
"""
import time
from pages.base_page import BasePage


# ─────────────────────────────────────────────────────────────────────────────
# Navegacion
# ─────────────────────────────────────────────────────────────────────────────

class SupervisionNav:
    """Navegacion al modulo Supervision desde la pagina principal."""

    MENU_SUPERVISION     = "#accionEjecutar_4"
    MENU_NOTIFICAR       = "#accionEjecutar_41"
    MENU_MONITORES       = "#accionEjecutar_42"
    MENU_MONITOR_EFECT   = "#accionEjecutar_421"
    MENU_DASHBOARDS      = "#accionEjecutar_43"

    def __init__(self, page):
        self.page = page

    def _abrir_tab(self, item_id: str):
        """Abre un item del menu Supervision en nueva pestana."""
        self.page.locator(self.MENU_SUPERVISION).wait_for(state='visible', timeout=10000)
        self.page.evaluate(f"document.querySelector('{self.MENU_SUPERVISION}').click()")
        time.sleep(1.2)
        with self.page.context.expect_page(timeout=15000) as new_page_info:
            self.page.evaluate(f"document.querySelector('{item_id}').click()")
        tab = new_page_info.value
        try:
            tab.wait_for_load_state('domcontentloaded', timeout=15000)
        except Exception:
            time.sleep(3)
        time.sleep(2)
        return tab

    def open_notificar_usuarios(self):
        return self._abrir_tab(self.MENU_NOTIFICAR)


# ─────────────────────────────────────────────────────────────────────────────
# Notificar Usuarios (/MensajesUsuarios)
# ─────────────────────────────────────────────────────────────────────────────

class NotificarUsuariosPage(BasePage):
    """
    Page Object para Notificar Usuarios (/MensajesUsuarios).

    DOM verificado:
      #panelMensajesProgramados     -> panel principal
      #frmMessageData               -> formulario de mensaje
        #txtAsunto                  -> input asunto (maxlength=40)
        #txaMensaje                 -> textarea mensaje (maxlength=500)
        #rdbAhora                   -> radio "Ahora" (checked por defecto)
        #rdbOtroMomento             -> radio "Otro momento"
        #datetimeOtroMomento        -> div fecha/hora (display:none por defecto)
          #dtpFechaNotificacion     -> datepicker DD/MM/AAAA
        #cmbCliente                 -> select clientes (valor -1 y 1)
        #listadoUsuarios            -> ul.user-check-list
          #chkAllUsers              -> checkbox "Seleccionar Todos"
          li.user-item              -> 6 usuarios (1000-1004 + cyt)
        #btnGuardarMensaje          -> boton "Enviar Mensaje"
      #messageQueue                 -> seccion cola de mensajes
        #tblMensajesProgramados     -> DataTable historial
        #btnRefreshTable            -> boton refrescar

    Estado base del sistema (verificado):
      Usuarios en lista: 6 (1000-1004 = Agente Generico + cyt usuario inicial)
      Tabla de historial: 0 mensajes (vacia)
      Radio por defecto: "Ahora" (#rdbAhora)
    """

    URL_PATH = "/MensajesUsuarios"

    # Selectores del formulario
    PANEL_PRINCIPAL      = "#panelMensajesProgramados"
    FORM_MENSAJE         = "#frmMessageData"
    INPUT_ASUNTO         = "#txtAsunto"
    TEXTAREA_MENSAJE     = "#txaMensaje"
    RADIO_AHORA          = "#rdbAhora"
    RADIO_OTRO           = "#rdbOtroMomento"
    DIV_DATETIME         = "#datetimeOtroMomento"
    INPUT_FECHA          = "#dtpFechaNotificacion"
    SELECT_CLIENTE       = "#cmbCliente"
    LISTA_USUARIOS       = "#listadoUsuarios"
    CHK_ALL_USERS        = "#chkAllUsers"
    ITEMS_USUARIOS       = "#listadoUsuarios li.user-item"
    BTN_ENVIAR           = "#btnGuardarMensaje"

    # Selectores de la cola de mensajes
    TABLA_HISTORIAL      = "#tblMensajesProgramados"
    BTN_REFRESH          = "#btnRefreshTable"
    INFO_TABLA           = "#tblMensajesProgramados_info"

    # Opciones del select de clientes
    CLIENTE_TODOS        = "-1"
    CLIENTE_GENERICO     = "1"

    # Constantes del estado base
    TOTAL_USUARIOS       = 6
    CLIENTE_BASE_TEXT    = "Cliente generico"

    def __init__(self, page):
        super().__init__(page)

    def wait_for_load(self):
        """Espera a que el panel principal sea visible."""
        self.page.locator(self.PANEL_PRINCIPAL).wait_for(
            state='visible', timeout=self.timeout
        )

    def verify_page_loaded(self):
        self.wait_for_load()

    # ── Getters de estado ────────────────────────────────────────────

    def radio_ahora_seleccionado(self) -> bool:
        return self.page.locator(self.RADIO_AHORA).is_checked()

    def radio_otro_seleccionado(self) -> bool:
        return self.page.locator(self.RADIO_OTRO).is_checked()

    def datetime_visible(self) -> bool:
        return self.page.evaluate(
            "() => window.getComputedStyle("
            "document.getElementById('datetimeOtroMomento')).display !== 'none'"
        )

    def get_opciones_cliente(self) -> list:
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('#cmbCliente option'))
                .map(o => ({value: o.value, text: o.text.trim()}))
        """)

    def get_total_usuarios(self) -> int:
        return self.page.locator(self.ITEMS_USUARIOS).count()

    def get_labels_usuarios(self) -> list:
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('#listadoUsuarios li.user-item label'))
                .map(l => l.innerText.trim())
        """)

    def get_tabla_info(self) -> str:
        try:
            return self.page.locator(self.INFO_TABLA).inner_text().strip()
        except Exception:
            return ""

    # ── Interacciones ────────────────────────────────────────────────

    def seleccionar_radio_otro_momento(self):
        self.page.locator(self.RADIO_OTRO).click()
        time.sleep(0.4)

    def seleccionar_radio_ahora(self):
        self.page.locator(self.RADIO_AHORA).click()
        time.sleep(0.4)

    def click_enviar(self):
        self.page.locator(self.BTN_ENVIAR).click()
        time.sleep(1.0)

    def get_errores_visibles(self) -> list:
        """Retorna los textos de los elementos .error actualmente visibles."""
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('.error'))
                .filter(el => el.getBoundingClientRect().width > 0
                           && el.innerText.trim())
                .map(el => el.innerText.trim())
        """)

    def limpiar_formulario(self):
        """Restablece el formulario al estado inicial."""
        try:
            # Limpiar campos de texto
            self.page.evaluate("""
                () => {
                    const a = document.getElementById('txtAsunto');
                    const m = document.getElementById('txaMensaje');
                    if (a) a.value = '';
                    if (m) m.value = '';
                }
            """)
            # Restaurar radio a "Ahora"
            if not self.radio_ahora_seleccionado():
                self.seleccionar_radio_ahora()
            # Desmarcar todos los checkboxes de usuarios
            self.page.evaluate("""
                () => {
                    document.querySelectorAll('#listadoUsuarios input[type="checkbox"]')
                        .forEach(cb => cb.checked = false);
                }
            """)
        except Exception:
            pass
