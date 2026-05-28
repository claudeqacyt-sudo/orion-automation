"""
test_login.py — Tests de SMOKE para el login de Orion Contact Center
Estos son los primeros tests que deben pasar antes de ejecutar regresión completa.
"""
import pytest
from playwright.sync_api import Page
from pages.login_page import LoginPage


@pytest.mark.smoke
@pytest.mark.login
class TestLogin:

    def test_login_exitoso_admin(self, page: Page, base_url: str, admin_credentials: dict):
        """
        SMOKE-001: Verificar que el usuario admin puede ingresar al sistema.
        Post-condición: hace logout para liberar la sesión.
        """
        page.set_viewport_size({"width": 1600, "height": 900})
        login = LoginPage(page)
        login.navigate(base_url)
        login.login(admin_credentials["username"], admin_credentials["password"])
        login.verify_logged_in()
        login.take_screenshot("SMOKE-001_login_exitoso")

        # Logout explícito para liberar la sesión del servidor
        login.logout()

    def test_login_credenciales_invalidas(self, page: Page, base_url: str):
        """
        SMOKE-002: Verificar que el sistema rechaza credenciales incorrectas.
        Usa usuario distinto al de producción para no interferir con sesiones activas.
        """
        page.set_viewport_size({"width": 1600, "height": 900})
        login = LoginPage(page)
        login.navigate(base_url)
        login.login("usuario_invalido_qa", "password_invalido_qa")
        login.verify_login_error()
        login.take_screenshot("SMOKE-002_login_error")

    def test_logout(self, logged_in_page: Page, base_url: str):
        """
        SMOKE-003: Verificar que el usuario puede cerrar sesión correctamente.
        El fixture logged_in_page ya maneja el login; aquí verificamos el logout.
        """
        login = LoginPage(logged_in_page)
        login.logout()

        # Después del logout debe volver a /login o mostrar el formulario
        import re
        from playwright.sync_api import expect
        expect(logged_in_page).to_have_url(re.compile(r"/login"), timeout=10000)
        login.take_screenshot("SMOKE-003_logout_exitoso")
