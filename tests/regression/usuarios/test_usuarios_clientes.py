"""
tests/regression/usuarios/test_usuarios_clientes.py
Suite de regresión — Usuarios > Usuarios de Clientes (/configUsuariosClientes)

Estructura DOM verificada:
  #cmbCliente          → select de clientes (1 opción: "Cliente generico")
  #chkSelectAll        → checkbox oculto "Todos los usuarios" (checked cuando todos asignados)
  ul#lsConfiguracion   → lista de usuarios asignables
    └── li > label.single-selector > input[type="checkbox"][value="N"] + span[nombre]
  #txtFiltro           → input "Búsqueda rápida"

Mecanismo de asignación:
  - Toggle de checkbox con auto-save (sin botón Guardar explícito).
  - Clicking el label de un li activa/desactiva la asignación del usuario al cliente.
  - El filtro #txtFiltro NO oculta li en el DOM (verificado con diagnóstico CSS).

Estado base del sistema (verificado):
  Clientes: 1 → "Cliente generico"
  Usuarios: 5 (1000 al 1004 – Agente Genérico), todos asignados (checked=True)
  chkSelectAll: True (todos asignados)
"""
import pytest
import time
from pages.usuarios_page import (

    UsuariosNav,
    UsuariosClientesPage,
)
pytestmark = pytest.mark.skip(reason="temporalmente desactivado -- foco en tests FRW supervisor")



# ─────────────────────────────────────────────────────────────────────────────
# Fixture de sección — abre la pestaña UNA VEZ para toda la clase
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def usuarios_clientes_tab(shared_page):
    """
    Abre Usuarios de Clientes una sola vez para todos los tests de la clase.
    Al terminar cierra la pestaña.
    """
    nav = UsuariosNav(shared_page)
    tab = nav.open_usuarios_clientes()
    page_obj = UsuariosClientesPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


# ─────────────────────────────────────────────────────────────────────────────
# USR-004 — Usuarios de Clientes
# ─────────────────────────────────────────────────────────────────────────────

class TestUsuariosClientes:

    @pytest.fixture(autouse=True)
    def limpiar_estado(self, usuarios_clientes_tab):
        """Limpia el filtro de texto después de cada test."""
        yield
        try:
            usuarios_clientes_tab.limpiar_filtro()
        except Exception:
            pass

    # ── USR-004-A ────────────────────────────────────────────────────

    def test_USR004_carga_correctamente(self, usuarios_clientes_tab):
        """
        USR-004-A: La sección carga y muestra todos los elementos principales.
        Verifica: URL, título, selector de cliente, lista de usuarios, campo filtro.
        """
        page_obj = usuarios_clientes_tab
        page_obj.verify_page_loaded()

        assert "/configUsuariosClientes" in page_obj.page.url, \
            f"URL incorrecta: {page_obj.page.url}"

        assert page_obj.page.locator(UsuariosClientesPage.SELECT_CLIENTE).is_visible(), \
            "#cmbCliente no está visible"
        assert page_obj.page.locator(UsuariosClientesPage.LISTA_USUARIOS).is_visible(), \
            "#lsConfiguracion no está visible"
        assert page_obj.page.locator(UsuariosClientesPage.INPUT_FILTRO).is_visible(), \
            "#txtFiltro no está visible"

        titulo = page_obj.page.locator("#tituloPrincipal").inner_text().strip()
        assert "usuario" in titulo.lower() and "cliente" in titulo.lower(), \
            f"Título inesperado: '{titulo}'"

    # ── USR-004-B ────────────────────────────────────────────────────

    def test_USR004_selector_tiene_cliente_base(self, usuarios_clientes_tab):
        """
        USR-004-B: El selector #cmbCliente contiene el cliente base del sistema
        ("Cliente generico").
        """
        page_obj = usuarios_clientes_tab
        clientes = page_obj.get_clientes_disponibles()

        assert len(clientes) >= 1, \
            "El selector de clientes está vacío"
        assert any(
            UsuariosClientesPage.CLIENTE_BASE.lower() in c.lower()
            for c in clientes
        ), f"'{UsuariosClientesPage.CLIENTE_BASE}' no encontrado. Clientes: {clientes}"

    # ── USR-004-C ────────────────────────────────────────────────────

    def test_USR004_lista_contiene_cinco_agentes(self, usuarios_clientes_tab):
        """
        USR-004-C: La lista #lsConfiguracion contiene los agentes del sistema.
        Verifica que los agentes base (1000-1004) esten presentes.
        El conteo total es variable segun el ambiente — no se valida un numero exacto.
        """
        page_obj = usuarios_clientes_tab
        total = page_obj.get_total_usuarios()

        assert total > 0, \
            "La lista de usuarios de cliente esta vacia"

        nombres = page_obj.get_nombres_usuarios()
        for num in ["1000", "1001", "1002", "1003", "1004"]:
            assert any(num in n for n in nombres), \
                f"Agente '{num}' no encontrado en la lista. Nombres: {nombres}"

    # ── USR-004-D ────────────────────────────────────────────────────

    def test_USR004_todos_los_agentes_asignados_al_cliente(self, usuarios_clientes_tab):
        """
        USR-004-D: Todos los usuarios de la lista están asignados al cliente
        (todos los checkboxes están en estado checked=True).
        """
        page_obj = usuarios_clientes_tab
        total     = page_obj.get_total_usuarios()
        asignados = page_obj.get_usuarios_asignados_count()

        assert asignados == total, \
            f"Se esperaban {total} usuarios asignados, " \
            f"se encontraron {asignados} de {total}"

    # ── USR-004-E ────────────────────────────────────────────────────

    def test_USR004_chk_select_all_activo(self, usuarios_clientes_tab):
        """
        USR-004-E: El toggle "Todos los usuarios" (#chkSelectAll) está activo,
        lo que indica que todos los usuarios están asignados al cliente actual.
        """
        page_obj = usuarios_clientes_tab
        assert page_obj.chk_select_all_activo(), \
            "El toggle 'Todos los usuarios' (#chkSelectAll) debería estar activo " \
            "cuando todos los usuarios están asignados"

    # ── USR-004-F ────────────────────────────────────────────────────

    def test_USR004_filtro_existe_y_es_funcional(self, usuarios_clientes_tab):
        """
        USR-004-F: El campo de filtro #txtFiltro existe, está habilitado y
        acepta texto sin romper la página ni modificar el total de ítems en el DOM.

        NOTA: Verificado con diagnóstico DOM que el filtro de esta sección NO oculta
        los li mediante CSS (mismo comportamiento que las otras secciones de Usuarios).
        """
        page_obj = usuarios_clientes_tab

        filtro = page_obj.page.locator(UsuariosClientesPage.INPUT_FILTRO)
        assert filtro.is_visible(), "El campo #txtFiltro no está visible"
        assert filtro.is_enabled(), "El campo #txtFiltro no está habilitado"

        total_antes = page_obj.get_total_usuarios()
        assert total_antes > 0, "La lista de usuarios está vacía"

        # Escribir en el filtro no debe lanzar errores ni vaciar la lista
        page_obj.filtrar_usuarios("1002")
        total_con_texto = page_obj.get_total_usuarios()
        assert total_con_texto > 0, \
            "La lista quedó vacía tras escribir en el filtro"

        # Limpiar no debe cambiar el total de ítems en el DOM
        page_obj.limpiar_filtro()
        total_despues = page_obj.get_total_usuarios()
        assert total_despues == total_antes, \
            f"El total de usuarios cambió al limpiar el filtro: " \
            f"antes={total_antes}, después={total_despues}"

    # ── USR-004-G ────────────────────────────────────────────────────

    def test_USR004_toggle_asignacion_usuario(self, usuarios_clientes_tab):
        """
        USR-004-G: El toggle de asignación funciona correctamente.

        Flujo verificado:
        1. Verificar que el último agente (1004) está asignado (checked=True)
        2. Hacer click en su label → queda desasignado (checked=False)
        3. Verificar que el conteo de asignados bajó en 1
        4. Hacer click nuevamente → queda asignado (checked=True)
        5. Verificar que el conteo volvió al total original

        NOTA: La página auto-guarda en cada click (sin botón Guardar).
              El test usa try/finally para garantizar la restauración del estado.
        """
        page_obj = usuarios_clientes_tab

        total_usuarios = page_obj.get_total_usuarios()
        asignados_inicial = page_obj.get_usuarios_asignados_count()
        ultimo_idx = total_usuarios - 1   # índice del último usuario (1004)

        assert asignados_inicial == total_usuarios, \
            f"Estado inicial inesperado: {asignados_inicial}/{total_usuarios} asignados"
        assert page_obj.get_estado_usuario(ultimo_idx) is True, \
            f"El usuario [{ultimo_idx}] debería estar asignado al inicio"

        try:
            # ── DESASIGNAR ───────────────────────────────────────────
            page_obj.toggle_usuario(ultimo_idx)

            asignados_post_des = page_obj.get_usuarios_asignados_count()
            assert asignados_post_des == asignados_inicial - 1, \
                f"Tras desasignar se esperaban {asignados_inicial - 1} asignados, " \
                f"hay {asignados_post_des}"
            assert page_obj.get_estado_usuario(ultimo_idx) is False, \
                f"El usuario [{ultimo_idx}] debería estar DESASIGNADO tras el primer toggle"

            # ── REASIGNAR ────────────────────────────────────────────
            page_obj.toggle_usuario(ultimo_idx)

            asignados_final = page_obj.get_usuarios_asignados_count()
            assert asignados_final == asignados_inicial, \
                f"Tras reasignar se esperaban {asignados_inicial} asignados, " \
                f"hay {asignados_final}"
            assert page_obj.get_estado_usuario(ultimo_idx) is True, \
                f"El usuario [{ultimo_idx}] debería estar ASIGNADO tras el segundo toggle"

        except Exception:
            # Cleanup de emergencia: si el usuario quedó desasignado, restaurarlo
            try:
                if page_obj.get_estado_usuario(ultimo_idx) is False:
                    page_obj.toggle_usuario(ultimo_idx)
            except Exception:
                pass
            raise

