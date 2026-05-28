"""
tests/regression/config/test_usuarios.py
Suite de regresión — Usuarios > Gestión de Perfiles (/perfiles)

Estructura de navegación confirmada:
  Cada sub-sección abre en una NUEVA PESTAÑA del browser.
  El fixture gestion_perfiles_tab captura esa pestaña y la cierra al terminar.
"""
import pytest
import time
from pages.usuarios_page import (
    UsuariosNav,
    GestionPerfilesPage,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures de sección
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def gestion_perfiles_tab(shared_page):
    """
    Abre Gestión de Perfiles UNA SOLA VEZ para toda la clase TestGestionPerfiles.
    Todos los tests del grupo comparten la misma pestaña.
    """
    nav = UsuariosNav(shared_page)
    tab = nav.open_gestion_perfiles()
    page_obj = GestionPerfilesPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


# ─────────────────────────────────────────────────────────────────────────────
# USR-001 — Gestión de Perfiles
# ─────────────────────────────────────────────────────────────────────────────

class TestGestionPerfiles:

    @pytest.fixture(autouse=True)
    def limpiar_estado(self, gestion_perfiles_tab):
        """
        Se ejecuta antes y después de CADA test.
        Garantiza que no queden modales abiertos ni filtros activos entre tests.
        """
        yield
        page = gestion_perfiles_tab.page

        # 1. Cerrar cualquier modal que haya quedado abierto
        for selector in [
            GestionPerfilesPage.BTN_CONFIRM_NO,        # cancelar eliminación si quedó abierta
            GestionPerfilesPage.BTN_MODAL_NUEVO_CAN,
            GestionPerfilesPage.BTN_MODAL_EDIT_CANCEL,
            GestionPerfilesPage.BTN_INFO_OK,
        ]:
            try:
                btn = page.locator(selector)
                if btn.is_visible(timeout=300):
                    btn.click()
                    time.sleep(0.3)
            except Exception:
                pass

        # 2. Limpiar el filtro para que el próximo test vea todos los perfiles
        try:
            gestion_perfiles_tab.limpiar_filtro()
        except Exception:
            pass

    def test_USR001_carga_correctamente(self, gestion_perfiles_tab):
        """
        USR-001-A: La sección carga y muestra los elementos principales.
        Verifica: tabla, botón Nuevo, botón Buscar, campo de filtro.
        """
        page_obj = gestion_perfiles_tab
        page_obj.verify_page_loaded()
        assert "/perfiles" in page_obj.page.url, \
            f"URL incorrecta: {page_obj.page.url}"

    def test_USR001_columnas_tabla(self, gestion_perfiles_tab):
        """
        USR-001-B: La tabla #dt-perfiles tiene la columna 'Descripción'.
        """
        page_obj = gestion_perfiles_tab
        page_obj.wait_for_load()
        headers = page_obj.get_column_headers()
        assert headers, "La tabla no tiene encabezados visibles"
        assert any("Descripci" in h for h in headers), \
            f"Columna 'Descripción' no encontrada. Columnas: {headers}"

    def test_USR001_perfiles_base_existen(self, gestion_perfiles_tab):
        """
        USR-001-C: Los perfiles base del sistema (Administrador, Agente, Supervisor) existen.
        """
        page_obj = gestion_perfiles_tab
        page_obj.wait_for_load()
        nombres = page_obj.get_profile_names()
        assert nombres, "No se encontraron perfiles en la tabla"
        for perfil in GestionPerfilesPage.PERFILES_BASE:
            assert any(perfil.lower() in n.lower() for n in nombres), \
                f"Perfil base '{perfil}' no encontrado. Perfiles encontrados: {nombres}"

    def test_USR001_filtro_busqueda(self, gestion_perfiles_tab):
        """
        USR-001-D: El filtro de búsqueda reduce los resultados correctamente.
        """
        page_obj = gestion_perfiles_tab
        page_obj.wait_for_load()

        total_inicial = page_obj.get_row_count()
        assert total_inicial > 0, "La tabla está vacía antes de filtrar"

        # Buscar "Admin" — debe retornar solo el perfil Administrador
        page_obj.buscar("Admin")
        time.sleep(1)
        filtrados = page_obj.get_profile_names()
        assert len(filtrados) >= 1, "El filtro no devolvió resultados para 'Admin'"
        assert all("admin" in n.lower() for n in filtrados), \
            f"Resultados inesperados para filtro 'Admin': {filtrados}"

    def test_USR001_boton_nuevo_visible(self, gestion_perfiles_tab):
        """
        USR-001-E: El botón Nuevo está habilitado (usuario admin tiene permiso).
        """
        page_obj = gestion_perfiles_tab
        page_obj.verify_page_loaded()
        btn = page_obj.page.locator(GestionPerfilesPage.BTN_NUEVO)
        assert btn.is_enabled(), "El botón Nuevo no está habilitado"

    def test_USR001_boton_nuevo_abre_modal(self, gestion_perfiles_tab):
        """
        USR-001-F: Click en Nuevo abre el modal de creación con los campos correctos.
        Verifica: modal visible, título, campo Descripción editable, campo ID presente.
        """
        page_obj = gestion_perfiles_tab
        page_obj.wait_for_load()

        # Click en Nuevo
        page_obj.click_nuevo()
        time.sleep(1)

        # Modal de CREACIÓN debe abrirse (#modalGlobal2Botones)
        assert page_obj.modal_nuevo_esta_abierto(), \
            "El modal de creación (#modalGlobal2Botones) no se abrió al hacer click en Nuevo"

        # Título del modal
        titulo = page_obj.page.locator(GestionPerfilesPage.MODAL_NUEVO_TITULO).inner_text()
        assert "perfil" in titulo.lower(), \
            f"Título del modal inesperado: '{titulo}'"

        # Campo Descripción editable
        campo_desc = page_obj.page.locator(GestionPerfilesPage.MODAL_NUEVO_DESC)
        assert campo_desc.is_visible(), "Campo Descripción no visible en modal Nuevo"
        assert campo_desc.is_enabled(), "Campo Descripción no editable en modal Nuevo"

        # Campo ID presente
        campo_id = page_obj.page.locator(GestionPerfilesPage.MODAL_NUEVO_ID)
        assert campo_id.is_visible(), "Campo ID no visible en modal Nuevo"

        # Cerrar sin guardar
        page_obj.cancelar_nuevo()
        assert not page_obj.modal_nuevo_esta_abierto(), \
            "El modal no se cerró al hacer click en Cancelar"

    def test_USR001_boton_nuevo_tiene_solo_dos_botones(self, gestion_perfiles_tab):
        """
        USR-001-G: El modal de creación tiene OK y Cancelar (sin botón Eliminar).
        Diferencia clave vs modal de edición que sí tiene Eliminar.
        """
        page_obj = gestion_perfiles_tab
        page_obj.wait_for_load()
        page_obj.click_nuevo()
        time.sleep(1)

        assert page_obj.modal_nuevo_esta_abierto(), "Modal de creación no abierto"

        # OK visible
        btn_ok = page_obj.page.locator(GestionPerfilesPage.BTN_MODAL_NUEVO_OK)
        assert btn_ok.is_visible(), "Botón OK no visible en modal Nuevo"

        # Cancelar visible
        btn_can = page_obj.page.locator(GestionPerfilesPage.BTN_MODAL_NUEVO_CAN)
        assert btn_can.is_visible(), "Botón Cancelar no visible en modal Nuevo"

        # NO debe existir botón Eliminar en este modal
        btn_elim = page_obj.page.locator(GestionPerfilesPage.BTN_MODAL_EDIT_ELIM)
        assert not btn_elim.is_visible(), \
            "El modal de creación NO debería tener botón Eliminar"

        page_obj.cancelar_nuevo()

    def test_USR001_click_fila_abre_modal_edicion(self, gestion_perfiles_tab):
        """
        USR-001-H: Click en una fila de la tabla abre el modal de edición.
        Verifica: modal visible, campo ID deshabilitado, campo Descripción editable,
                  título correcto.
        """
        page_obj = gestion_perfiles_tab
        page_obj.wait_for_load()

        # Click en la primera fila (Administrador)
        page_obj.click_fila(1)
        time.sleep(1)

        # Modal de EDICIÓN debe abrirse (#modalGlobal3Botones)
        assert page_obj.modal_edicion_esta_abierto(), \
            "El modal de edición (#modalGlobal3Botones) no se abrió al hacer click en la fila"

        # El campo ID debe estar DESHABILITADO (no se puede cambiar el ID del perfil)
        campo_id = page_obj.page.locator(GestionPerfilesPage.MODAL_EDICION_ID)
        assert not campo_id.is_enabled(), \
            "El campo ID debería estar deshabilitado en modo edición"

        # El campo Descripción debe ser editable
        campo_desc = page_obj.page.locator(GestionPerfilesPage.MODAL_EDICION_DESC)
        assert campo_desc.is_visible(), "Campo Descripción no visible en modal edición"
        assert campo_desc.is_enabled(), "Campo Descripción no editable en modal edición"

        # Cerrar sin guardar
        page_obj.cancelar_edicion()
        assert not page_obj.modal_edicion_esta_abierto(), \
            "El modal de edición no se cerró con Cancelar"

    def test_USR001_eliminar_deshabilitado_en_perfiles_base(self, gestion_perfiles_tab):
        """
        USR-001-I: El botón Eliminar está deshabilitado para los 3 perfiles base del sistema.
        Los perfiles Administrador, Agente y Supervisor no se pueden borrar.
        """
        page_obj = gestion_perfiles_tab
        page_obj.wait_for_load()

        nombres = page_obj.get_profile_names()
        perfiles_base = [n for n in nombres
                         if any(b.lower() in n.lower()
                                for b in GestionPerfilesPage.PERFILES_BASE)]

        assert perfiles_base, "No se encontraron perfiles base en la tabla"

        for i, nombre in enumerate(perfiles_base):
            page_obj.click_fila(i + 1)
            time.sleep(1)
            assert page_obj.modal_edicion_esta_abierto(), \
                f"Modal no abierto para perfil '{nombre}'"

            assert not page_obj.eliminar_esta_habilitado(), \
                f"Botón Eliminar NO debería estar habilitado para el perfil base '{nombre}'"

            page_obj.cancelar_edicion()
            time.sleep(0.5)

    def test_USR001_buscar_limpia_y_restaura(self, gestion_perfiles_tab):
        """
        USR-001-J: Limpiar el filtro y buscar vacío muestra todos los perfiles nuevamente.
        Primero garantiza estado sin filtro, luego filtra, luego limpia y verifica.
        """
        page_obj = gestion_perfiles_tab
        page_obj.wait_for_load()

        # Asegurar estado sin filtro antes de medir (tests previos pueden haberlo modificado)
        page_obj.limpiar_filtro()
        time.sleep(1)
        total_sin_filtro = page_obj.get_row_count()
        assert total_sin_filtro > 0, "La tabla está vacía incluso sin filtro"

        # Filtrar por algo específico
        page_obj.buscar("Supervisor")
        time.sleep(1)
        filtrados = page_obj.get_profile_names()
        assert len(filtrados) < total_sin_filtro, \
            f"El filtro 'Supervisor' debería reducir los {total_sin_filtro} resultados"

        # Limpiar filtro — debe volver al total sin filtro
        page_obj.limpiar_filtro()
        time.sleep(1)
        total_final = page_obj.get_row_count()
        assert total_final == total_sin_filtro, \
            f"Después de limpiar el filtro se esperaban {total_sin_filtro} perfiles, " \
            f"se encontraron {total_final}"

    def test_USR001_crear_y_eliminar_perfil(self, gestion_perfiles_tab):
        """
        USR-001-K: Se puede crear un perfil nuevo con el botón Nuevo y luego eliminarlo.

        Flujo verificado:
        1. Click en Nuevo → modal de creación con campo ID deshabilitado (auto-generado)
        2. Llenar solo Descripción → click OK
        3. Modal de éxito "El perfil se ha agregado de manera exitosa"
        4. El nuevo perfil aparece en la tabla
        5. Click en la fila del nuevo perfil → modal de edición con Eliminar HABILITADO
        6. Click en Eliminar → modal de confirmación "¿ Desea eliminar el registro ?"
        7. Confirmar con "Sí" → el perfil desaparece de la tabla

        NOTA: Este test crea y elimina su propio perfil de prueba.
              NO afecta los perfiles base del sistema.
        """
        DESC_PRUEBA = "QA Test Automatico K"

        page_obj = gestion_perfiles_tab
        page_obj.wait_for_load()
        page_obj.limpiar_filtro()
        time.sleep(0.5)

        # Registrar perfiles iniciales para comparar al final
        perfiles_iniciales = page_obj.get_profile_names()
        assert DESC_PRUEBA not in perfiles_iniciales, \
            f"El perfil de prueba ya existe en la tabla antes del test: {perfiles_iniciales}"

        # ── PASO 1: Crear el perfil ──────────────────────────────────────
        page_obj.crear_perfil(DESC_PRUEBA)
        time.sleep(1)

        # ── PASO 2: Verificar que aparece en la tabla ────────────────────
        page_obj.wait_for_load()
        assert page_obj.perfil_existe_en_tabla(DESC_PRUEBA), \
            f"El perfil '{DESC_PRUEBA}' no apareció en la tabla tras la creación. " \
            f"Perfiles actuales: {page_obj.get_profile_names()}"

        # ── PASO 3: Click en la fila → modal de edición ──────────────────
        idx = page_obj.get_fila_por_descripcion(DESC_PRUEBA)
        assert idx is not None, \
            f"No se encontró la fila del perfil '{DESC_PRUEBA}' en la tabla"

        page_obj.click_fila(idx)
        time.sleep(1)

        assert page_obj.modal_edicion_esta_abierto(), \
            "El modal de edición no se abrió para el perfil creado"

        # El botón Eliminar debe estar HABILITADO para un perfil recién creado
        assert page_obj.eliminar_esta_habilitado(), \
            "El botón Eliminar debería estar habilitado para un perfil nuevo (no es perfil base)"

        # La descripción en el modal debe coincidir
        desc_en_modal = page_obj.get_modal_edicion_desc()
        assert DESC_PRUEBA.lower() in desc_en_modal.lower(), \
            f"La descripción en el modal ({desc_en_modal!r}) no coincide con {DESC_PRUEBA!r}"

        # ── PASO 4: Eliminar el perfil ────────────────────────────────────
        eliminado = page_obj.eliminar_perfil_seleccionado()
        assert eliminado, "La eliminación no se pudo iniciar (Eliminar deshabilitado)"

        time.sleep(1)

        # ── PASO 5: Verificar que desapareció de la tabla ─────────────────
        page_obj.wait_for_load()
        assert not page_obj.perfil_existe_en_tabla(DESC_PRUEBA), \
            f"El perfil '{DESC_PRUEBA}' todavía aparece en la tabla después de eliminarlo"

        # Los perfiles base deben seguir existiendo intactos
        perfiles_finales = page_obj.get_profile_names()
        for perfil_base in GestionPerfilesPage.PERFILES_BASE:
            assert any(perfil_base.lower() in n.lower() for n in perfiles_finales), \
                f"Perfil base '{perfil_base}' desapareció de la tabla — ERROR CRÍTICO"


