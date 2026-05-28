"""
base_page.py — Clase base con métodos comunes para todas las páginas (Page Object Model)
"""
from playwright.sync_api import Page, expect
import os


class BasePage:
    """Clase base que heredan todos los Page Objects."""

    def __init__(self, page: Page):
        self.page = page
        self.timeout = int(os.getenv("DEFAULT_TIMEOUT", "30000"))

    def navigate(self, url: str):
        """Navegar a una URL."""
        self.page.goto(url, timeout=int(os.getenv("NAVIGATION_TIMEOUT", "60000")))

    def wait_for_load(self):
        """
        Esperar a que la página cargue.
        Orion hace polling continuo, por lo que networkidle nunca se alcanza.
        Se usa domcontentloaded + pausa breve en su lugar.
        """
        self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)

    def wait_for_selector(self, selector: str):
        """Esperar a que un selector aparezca y sea visible."""
        self.page.wait_for_selector(selector, state="visible", timeout=self.timeout)

    def take_screenshot(self, name: str):
        """Capturar screenshot y guardarlo en reports/screenshots/."""
        os.makedirs("reports/screenshots", exist_ok=True)
        self.page.screenshot(path=f"reports/screenshots/{name}.png", full_page=True)

    def get_text(self, selector: str) -> str:
        """Obtener texto de un elemento."""
        return self.page.locator(selector).text_content()

    def click(self, selector: str):
        """Hacer click en un elemento."""
        self.page.locator(selector).click(timeout=self.timeout)

    def fill(self, selector: str, value: str):
        """Escribir en un campo de texto."""
        self.page.locator(selector).fill(value)

    def is_visible(self, selector: str) -> bool:
        """Verificar si un elemento es visible."""
        return self.page.locator(selector).is_visible()

    def get_table_rows(self, table_selector: str) -> list:
        """Obtener todas las filas de una tabla."""
        return self.page.locator(f"{table_selector} tr").all()

    def select_option(self, selector: str, value: str):
        """Seleccionar una opción de un dropdown."""
        self.page.locator(selector).select_option(value)
