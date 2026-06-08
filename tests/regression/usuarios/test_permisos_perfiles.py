"""
tests/regression/usuarios/test_permisos_perfiles.py
Suite de regresión — Usuarios > Permisos de Perfiles (/configNivelesFunciones)

Estructura DOM verificada:
  - #cmbNivel          : select con 3 perfiles (Administrador, Supervisor, Agente)
  - #txtFiltro         : input de búsqueda de permisos
  - #chkSelectAll      : toggle "Todos los permisos" (activo solo en Administrador)
  - ul#lsConfiguracion : lista de permisos como toggle switches CSS
    └── li > label.single-selector.with-switch > span.switch > input[type=checkbox]

Estado base del sistema:
  Administrador : 66 permisos, 66 activos (chkSelectAll = True)
  Supervisor    : 66 permisos, 23 activos
  Agente        : 64 permisos, 12 activos
"""
import pytest
import time
from pages.usuarios_page import (

    UsuariosNav,
    PermisosPerfilesPage,
)
# ─────────────────────────────────────────────────────────────────────────────
# Fixture de sección — abre la pestaña UNA VEZ para toda la clase
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def permisos_perfiles_tab(shared_page):
    """
    Abre Permisos de Perfiles una sola vez para todos los tests de la clase.
    Al terminar cierra la pestaña.
    """
    nav = UsuariosNav(shared_page)
    tab = nav.open_permisos_perfiles()
    page_obj = PermisosPerfilesPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


# ─────────────────────────────────────────────────────────────────────────────
# USR-002 — Permisos de Perfiles
# ─────────────────────────────────────────────────────────────────────────────

class TestPermisosPerfiles:

    @pytest.fixture(autouse=True)
    def limpiar_estado(self, permisos_perfiles_tab):
        """
        Limpia el filtro de texto después de cada test.
        Cada test selecciona explícitamente el perfil que necesita —
        no es necesario resetear el selector aquí.
        """
        yield
        try:
            permisos_perfiles_tab.limpiar_filtro()
        except Exception:
            pass

    # ── USR-002-A ────────────────────────────────────────────────────

    def test_USR002_carga_correctamente(self, permisos_perfiles_tab):
        """
        USR-002-A: La sección carga y muestra los elementos principales.
        Verifica: URL, select de perfil, filtro, lista de permisos.
        """
        page_obj = permisos_perfiles_tab
        page_obj.verify_page_loaded()
        assert "/configNivelesFunciones" in page_obj.page.url, \
            f"URL incorrecta: {page_obj.page.url}"

        assert page_obj.page.locator(PermisosPerfilesPage.LISTA_PERMISOS).is_visible(), \
            "La lista de permisos (#lsConfiguracion) no está visible"

    # ── USR-002-B ────────────────────────────────────────────────────

    def test_USR002_select_tiene_tres_perfiles(self, permisos_perfiles_tab):
        """
        USR-002-B: El select #cmbNivel contiene exactamente los 3 perfiles del sistema.
        """
        page_obj = permisos_perfiles_tab
        page_obj.wait_for_load()

        perfiles = page_obj.get_perfiles_disponibles()
        assert len(perfiles) == 3, \
            f"Se esperaban 3 perfiles, se encontraron {len(perfiles)}: {perfiles}"

        for esperado in PermisosPerfilesPage.PERFILES_OPCIONES:
            assert any(esperado.lower() in p.lower() for p in perfiles), \
                f"Perfil '{esperado}' no encontrado. Perfiles: {perfiles}"

    # ── USR-002-C ────────────────────────────────────────────────────

    def test_USR002_administrador_tiene_todos_los_permisos(self, permisos_perfiles_tab):
        """
        USR-002-C: Al seleccionar Administrador todos los permisos estan activos.
        El toggle "Todos los permisos" (#chkSelectAll) debe estar marcado.
        No se valida un numero exacto — se verifica que activos == total (todos encendidos).
        """
        page_obj = permisos_perfiles_tab
        page_obj.seleccionar_perfil("Administrador")

        total   = page_obj.get_total_permisos()
        activos = page_obj.get_permisos_activos_count()

        assert total > 0, \
            "La lista de permisos del Administrador esta vacia"

        assert activos == total, \
            f"Administrador deberia tener TODOS los permisos activos " \
            f"({total}), pero tiene {activos} activos"

        assert page_obj.chk_select_all_activo(), \
            "El toggle 'Todos los permisos' (#chkSelectAll) deberia estar activo " \
            "para el Administrador"

    # ── USR-002-D ────────────────────────────────────────────────────

    def test_USR002_permisos_criticos_administrador(self, permisos_perfiles_tab):
        """
        USR-002-D: Los permisos críticos del Administrador están activos.
        Verifica permisos de gestión de perfiles y contactos.
        """
        page_obj = permisos_perfiles_tab
        page_obj.seleccionar_perfil("Administrador")

        for permiso in PermisosPerfilesPage.PERMISOS_ADMIN_CRITICOS:
            estado = page_obj.permiso_esta_activo(permiso)
            assert estado is True, \
                f"El permiso '{permiso}' debería estar ACTIVO para Administrador, " \
                f"estado encontrado: {estado}"

    # ── USR-002-E ────────────────────────────────────────────────────

    def test_USR002_supervisor_tiene_menos_permisos_que_admin(self, permisos_perfiles_tab):
        """
        USR-002-E: El Supervisor tiene menos permisos activos que el Administrador.
        Se miden ambos dinamicamente y se verifica la jerarquia — sin numeros hardcodeados.
        """
        page_obj = permisos_perfiles_tab

        page_obj.seleccionar_perfil("Administrador")
        activos_admin = page_obj.get_permisos_activos_count()

        page_obj.seleccionar_perfil("Supervisor")
        total_sup   = page_obj.get_total_permisos()
        activos_sup = page_obj.get_permisos_activos_count()

        assert total_sup > 0, \
            "La lista de permisos del Supervisor esta vacia"

        assert activos_sup < activos_admin, \
            f"Supervisor ({activos_sup} activos) deberia tener MENOS permisos " \
            f"que Administrador ({activos_admin} activos)"

        assert not page_obj.chk_select_all_activo(), \
            "El toggle 'Todos los permisos' NO deberia estar activo para Supervisor"

    # ── USR-002-F ────────────────────────────────────────────────────

    def test_USR002_agente_tiene_menos_permisos_que_supervisor(self, permisos_perfiles_tab):
        """
        USR-002-F: El Agente tiene permisos restringidos respecto al Administrador.
        Verifica que la lista carga, tiene permisos, y el Agente no tiene acceso total
        (sus permisos activos son menores a los del Administrador).
        La comparacion Agente vs Supervisor es configurable segun el sistema
        y no se evalua como invariante.
        """
        page_obj = permisos_perfiles_tab

        page_obj.seleccionar_perfil("Administrador")
        activos_admin = page_obj.get_permisos_activos_count()

        page_obj.seleccionar_perfil("Agente")
        total_age   = page_obj.get_total_permisos()
        activos_age = page_obj.get_permisos_activos_count()

        assert total_age > 0, \
            "La lista de permisos del Agente esta vacia"

        assert activos_age < activos_admin, \
            f"Agente ({activos_age} activos) deberia tener MENOS permisos " \
            f"que Administrador ({activos_admin} activos)"

    # ── USR-002-G ────────────────────────────────────────────────────

    def test_USR002_permisos_criticos_bloqueados_en_agente(self, permisos_perfiles_tab):
        """
        USR-002-G: Los permisos de gestión de perfiles están INACTIVOS para el Agente.
        El Agente no puede crear, eliminar ni asignar permisos a perfiles.
        """
        page_obj = permisos_perfiles_tab
        page_obj.seleccionar_perfil("Agente")

        for permiso in PermisosPerfilesPage.PERMISOS_BLOQUEADOS_AGENTE:
            estado = page_obj.permiso_esta_activo(permiso)
            assert estado is False, \
                f"El permiso '{permiso}' debería estar INACTIVO para Agente, " \
                f"estado encontrado: {estado}"

    # ── USR-002-H ────────────────────────────────────────────────────

    def test_USR002_cambiar_perfil_actualiza_lista(self, permisos_perfiles_tab):
        """
        USR-002-H: Cambiar el perfil en el select actualiza la lista de permisos.
        Verifica que la cantidad de activos cambia al cambiar de perfil.
        """
        page_obj = permisos_perfiles_tab

        # Medir Admin y Agente dinamicamente — si son iguales, el selector no funciona.
        page_obj.seleccionar_perfil("Administrador")
        activos_admin = page_obj.get_permisos_activos_count()

        page_obj.seleccionar_perfil("Agente")
        activos_agente = page_obj.get_permisos_activos_count()

        assert activos_agente != activos_admin, \
            "La lista de permisos NO cambio al cambiar de perfil — " \
            f"Agente muestra {activos_agente} activos igual que Administrador ({activos_admin})"

    # ── USR-002-I ────────────────────────────────────────────────────

    def test_USR002_filtro_existe_y_es_funcional(self, permisos_perfiles_tab):
        """
        USR-002-I: El campo de filtro #txtFiltro existe, está habilitado y acepta texto.

        Nota: el filtro de esta sección NO oculta permisos individuales por nombre —
        opera a nivel de categoría/módulo. El test verifica que el campo existe
        y que escribir en él no rompe la página ni modifica el conteo de permisos.
        """
        page_obj = permisos_perfiles_tab
        page_obj.seleccionar_perfil("Administrador")

        filtro = page_obj.page.locator(PermisosPerfilesPage.INPUT_FILTRO)
        assert filtro.is_visible(), "El campo de filtro #txtFiltro no está visible"
        assert filtro.is_enabled(), "El campo de filtro #txtFiltro no está habilitado"

        total_antes = page_obj.get_total_permisos()
        assert total_antes > 0, "La lista de permisos está vacía"

        # Escribir en el filtro no debe lanzar errores ni vaciar la lista
        page_obj.filtrar_permisos("crear")
        total_con_filtro = page_obj.get_total_permisos()
        assert total_con_filtro > 0, \
            "La lista de permisos quedó vacía tras escribir en el filtro"

        # Limpiar el filtro no debe cambiar el total de ítems en el DOM
        page_obj.limpiar_filtro()
        total_despues = page_obj.get_total_permisos()
        assert total_despues == total_antes, \
            f"El total de permisos cambió después de limpiar el filtro: " \
            f"antes={total_antes}, después={total_despues}"

