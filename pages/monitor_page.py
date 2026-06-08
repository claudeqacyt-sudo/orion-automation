"""
monitor_page.py - Page Object para el modulo Monitor / Supervision de Orion Contact Center
Selectores verificados contra HTML real de Orion v7.0 (vm-2k22-er-01.orioncontactcenter.com.ar)

Ruta de navegacion en el menu:
  Supervision (accionEjecutar_4)
    Monitores (accionEjecutar_42)
      Monitor de Efectividad (accionEjecutar_421)  -> /MonitorEfectividad

Estado base del sistema (verificado):
  La pagina carga pero muestra "Sin monitores creados asignados a su usuario"
  No hay tablas ni selects activos - el panel monitorWrapper esta en estado vacio.
"""
import time
from pages.base_page import BasePage


class MonitorNav:
    """Navegacion al modulo Monitor desde la pagina principal."""

    MENU_SUPERVISION   = "#accionEjecutar_4"
    MENU_MONITORES     = "#accionEjecutar_42"
    MENU_MONITOR_EFECT = "#accionEjecutar_421"

    def __init__(self, page):
        self.page = page

    def open_monitor_efectividad(self):
        """
        Abre Monitor de Efectividad en nueva pestana.
        Retorna el objeto Page de la nueva pestana.
        """
        self.page.locator(self.MENU_SUPERVISION).wait_for(state='visible', timeout=10000)
        self.page.evaluate(f"document.querySelector('{self.MENU_SUPERVISION}').click()")
        time.sleep(1.0)
        self.page.evaluate(f"document.querySelector('{self.MENU_MONITORES}').click()")
        time.sleep(0.8)

        with self.page.context.expect_page(timeout=15000) as new_page_info:
            self.page.evaluate(
                f"document.querySelector('{self.MENU_MONITOR_EFECT}').click()"
            )

        tab = new_page_info.value
        tab.wait_for_load_state('domcontentloaded')
        time.sleep(2)
        return tab


class MonitorEfectividadPage(BasePage):
    """
    Page Object para Monitor de Efectividad (/MonitorEfectividad).

    DOM verificado:
      #panelMonitorEfectividad  -> panel principal (.panel-gestor)
      #tituloPrincipal          -> h2 "Monitores de Efectividad"
      #monitorWrapper           -> section con el contenido (o mensaje vacio)
      .no-monitors              -> h3 mostrado cuando no hay monitores configurados
    """

    URL_PATH = "/MonitorEfectividad"

    PANEL_PRINCIPAL  = "#panelMonitorEfectividad"
    TITULO           = "#tituloPrincipal"
    MONITOR_WRAPPER  = "#monitorWrapper"
    MSG_SIN_MONITOR  = ".no-monitors"

    TITULO_ESPERADO        = "Monitores de Efectividad"
    MSG_SIN_MONITOR_TEXTO  = "Sin monitores creados"

    def __init__(self, page):
        super().__init__(page)

    def wait_for_load(self):
        """Espera a que el panel principal sea visible."""
        self.page.locator(self.PANEL_PRINCIPAL).wait_for(
            state='visible', timeout=self.timeout
        )

    def verify_page_loaded(self):
        """Verifica que la pagina cargo correctamente."""
        self.wait_for_load()

    def get_titulo(self) -> str:
        """Retorna el texto del titulo principal."""
        return self.page.locator(self.TITULO).inner_text().strip()

    def panel_es_visible(self) -> bool:
        """Verifica que el panel principal es visible."""
        return self.page.locator(self.PANEL_PRINCIPAL).is_visible()

    def wrapper_es_visible(self) -> bool:
        """Verifica que el monitorWrapper es visible."""
        return self.page.locator(self.MONITOR_WRAPPER).is_visible()

    def tiene_mensaje_sin_monitores(self) -> bool:
        """Verifica que se muestra el mensaje de 'sin monitores configurados'."""
        try:
            el = self.page.locator(self.MSG_SIN_MONITOR).first
            if el.is_visible():
                texto = el.inner_text().strip()
                return self.MSG_SIN_MONITOR_TEXTO.lower() in texto.lower()
        except Exception:
            pass
        # Fallback: buscar en body
        return self.page.evaluate(
            f"() => document.body.innerText.toLowerCase()"
            f".includes('{self.MSG_SIN_MONITOR_TEXTO.lower()}')"
        )


# Alias para compatibilidad con el test POC original
class MonitorPage(MonitorEfectividadPage):
    """Alias de compatibilidad."""
    pass
