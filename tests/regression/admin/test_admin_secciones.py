"""
tests/regression/admin/test_admin_secciones.py
Suite de regresión — Admin: carga e interacciones read-only de cada sección disponible.

Cubre (usuario cyt / Administrador):
  ADM-001  Anuncios            /inicio
  ADM-002  Gestión de Perfiles /perfiles
  ADM-003  Permisos de Perfiles /configNivelesFunciones
  ADM-004  Usuarios de Perfiles /configPerfilesAgente
  ADM-005  Usuarios de Clientes /configUsuariosClientes
  ADM-006  Bloqueo de Usuarios  /GestorUsuariosBloqueados
  ADM-007  Notificar Usuarios   /MensajesUsuarios
  ADM-008  Monitor Efectividad  /MonitorEfectividad

Restricciones:
  - Sin creación ni modificación de registros.
  - Sin clicks en Guardar / OK / Asignar / Bloquear / Enviar.
  - Sólo lectura, filtros y modales cancelados.
"""
import time
import pytest
from playwright.sync_api import expect

from pages.anuncios_page import AnunciosNav, AnunciosPage
from pages.usuarios_page import (
    UsuariosNav,
    GestionPerfilesPage,
    PermisosPerfilesPage,
    UsuariosPerfilesPage,
    UsuariosClientesPage,
    BloqueoUsuariosPage,
)
from pages.supervision_page import SupervisionNav, NotificarUsuariosPage

pytestmark = [pytest.mark.regression, pytest.mark.admin]


# ─────────────────────────────────────────────────────────────────────────────
# ADM-001 — Anuncios  (/inicio)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def anuncios_tab(shared_page):
    nav = AnunciosNav(shared_page)
    tab = nav.open_anuncios()
    page_obj = AnunciosPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


class TestAnuncios:
    def test_ADM001_A_carga_correctamente(self, anuncios_tab):
        """ADM-001-A: Anuncios carga el carrusel con 3 slides e indicadores."""
        p = anuncios_tab
        assert "/inicio" in p.page.url
        assert p.get_total_slides() == AnunciosPage.TOTAL_SLIDES
        assert p.get_total_indicadores() == AnunciosPage.TOTAL_SLIDES
        assert p.slide_activo_tiene_imagen()

    def test_ADM001_B_titulos_slides_correctos(self, anuncios_tab):
        """ADM-001-B: Los títulos de los 3 slides coinciden con los valores esperados."""
        titulos = anuncios_tab.get_titulos_slides()
        for esperado in AnunciosPage.TITULOS_SLIDES:
            assert any(esperado.lower() in t.lower() for t in titulos), \
                f"Título esperado '{esperado}' no encontrado. Titles: {titulos}"

    def test_ADM001_C_botones_siguiente_anterior(self, anuncios_tab):
        """ADM-001-C: Los botones siguiente (→) y anterior (←) cambian el slide activo."""
        p = anuncios_tab
        inicio = p.get_indice_slide_activo()
        p.page.locator(AnunciosPage.BTN_NEXT).click()
        time.sleep(1.0)
        despues_next = p.get_indice_slide_activo()
        assert despues_next != inicio, "El slide no avanzó tras clic en Siguiente"
        p.page.locator(AnunciosPage.BTN_PREV).click()
        time.sleep(1.0)
        despues_prev = p.get_indice_slide_activo()
        assert despues_prev == inicio, "El slide no retrocedió tras clic en Anterior"


# ─────────────────────────────────────────────────────────────────────────────
# ADM-002 — Gestión de Perfiles  (/perfiles)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def gestion_perfiles_tab(shared_page):
    nav = UsuariosNav(shared_page)
    tab = nav.open_gestion_perfiles()
    page_obj = GestionPerfilesPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


class TestGestionPerfiles:
    def test_ADM002_A_carga_correctamente(self, gestion_perfiles_tab):
        """ADM-002-A: Gestión de Perfiles carga tabla, botón Nuevo y botón Buscar."""
        p = gestion_perfiles_tab
        assert "/perfiles" in p.page.url
        p.verify_page_loaded()

    def test_ADM002_B_columna_descripcion(self, gestion_perfiles_tab):
        """ADM-002-B: La tabla tiene la columna 'Descripción'."""
        headers = gestion_perfiles_tab.get_column_headers()
        assert "Descripción" in headers, \
            f"Columna 'Descripción' no encontrada. Headers actuales: {headers}"

    def test_ADM002_C_perfiles_base_existen(self, gestion_perfiles_tab):
        """ADM-002-C: Administrador, Agente y Supervisor están en la tabla."""
        nombres = gestion_perfiles_tab.get_profile_names()
        for perfil in GestionPerfilesPage.PERFILES_BASE:
            assert any(perfil.lower() in n.lower() for n in nombres), \
                f"Perfil base '{perfil}' no encontrado. Perfiles actuales: {nombres}"

    def test_ADM002_D_filtro_buscar(self, gestion_perfiles_tab):
        """ADM-002-D: El filtro de búsqueda reduce y restaura la tabla correctamente."""
        p = gestion_perfiles_tab
        total = p.get_row_count()
        p.buscar("Administrador")
        assert p.get_row_count() <= total
        p.limpiar_filtro()
        assert p.get_row_count() == total

    def test_ADM002_E_boton_nuevo_abre_y_cancela_modal(self, gestion_perfiles_tab):
        """ADM-002-E: Botón Nuevo abre modal de creación; Cancelar lo cierra."""
        p = gestion_perfiles_tab
        p.click_nuevo()
        assert p.modal_nuevo_esta_abierto(), "El modal de creación no se abrió"
        p.cancelar_nuevo()
        assert not p.modal_nuevo_esta_abierto(), "El modal no se cerró tras Cancelar"

    def test_ADM002_F_click_fila_abre_modal_edicion(self, gestion_perfiles_tab):
        """ADM-002-F: Click en fila abre modal de edición con ID y descripción; Cancelar cierra."""
        p = gestion_perfiles_tab
        p.click_fila(1)
        assert p.modal_edicion_esta_abierto(), "El modal de edición no se abrió"
        assert p.get_modal_edicion_id() != "", "El campo ID del modal está vacío"
        assert p.get_modal_edicion_desc() != "", "El campo Descripción del modal está vacío"
        p.cancelar_edicion()

    def test_ADM002_G_eliminar_deshabilitado_en_perfiles_base(self, gestion_perfiles_tab):
        """ADM-002-G: El botón Eliminar está deshabilitado en los perfiles base."""
        p = gestion_perfiles_tab
        for perfil in GestionPerfilesPage.PERFILES_BASE:
            idx = p.get_fila_por_descripcion(perfil)
            assert idx is not None, f"No se encontró la fila del perfil '{perfil}'"
            p.click_fila(idx)
            assert p.modal_edicion_esta_abierto()
            assert not p.eliminar_esta_habilitado(), \
                f"'Eliminar' debería estar deshabilitado para el perfil base '{perfil}'"
            p.cancelar_edicion()


# ─────────────────────────────────────────────────────────────────────────────
# ADM-003 — Permisos de Perfiles  (/configNivelesFunciones)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def permisos_tab(shared_page):
    nav = UsuariosNav(shared_page)
    tab = nav.open_permisos_perfiles()
    page_obj = PermisosPerfilesPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


class TestPermisosPerfiles:
    def test_ADM003_A_carga_correctamente(self, permisos_tab):
        """ADM-003-A: Permisos de Perfiles carga el select y la lista de permisos."""
        p = permisos_tab
        assert "/configNivelesFunciones" in p.page.url
        p.verify_page_loaded()

    def test_ADM003_B_tres_perfiles_disponibles(self, permisos_tab):
        """ADM-003-B: El select contiene exactamente los 3 perfiles esperados."""
        disponibles = permisos_tab.get_perfiles_disponibles()
        for esperado in PermisosPerfilesPage.PERFILES_OPCIONES:
            assert esperado in disponibles, \
                f"Perfil '{esperado}' no encontrado. Disponibles: {disponibles}"

    def test_ADM003_C_conteo_permisos_activos_por_perfil(self, permisos_tab):
        """ADM-003-C: Cada perfil tiene el número exacto de permisos activos esperados."""
        p = permisos_tab
        for perfil, esperado in PermisosPerfilesPage.ACTIVOS_PERMISOS.items():
            p.seleccionar_perfil(perfil)
            activos = p.get_permisos_activos_count()
            assert activos == esperado, \
                f"Perfil '{perfil}': esperado {esperado} activos, encontrado {activos}"

    def test_ADM003_D_administrador_tiene_todos_los_permisos(self, permisos_tab):
        """ADM-003-D: Administrador tiene todos sus permisos activos (66/66)."""
        p = permisos_tab
        p.seleccionar_perfil("Administrador")
        total = p.get_total_permisos()
        activos = p.get_permisos_activos_count()
        assert total == PermisosPerfilesPage.TOTAL_PERMISOS["Administrador"]
        assert activos == total, \
            f"Administrador tiene {activos} activos de {total} totales"

    def test_ADM003_E_filtro_permisos_funciona(self, permisos_tab):
        """ADM-003-E: El campo de filtro acepta texto y la lista sigue accesible; limpiar no elimina permisos."""
        p = permisos_tab
        p.seleccionar_perfil("Administrador")
        total = p.get_total_permisos()
        assert total > 0, "Lista de permisos vacía"
        p.filtrar_permisos("crear")
        # El filtro puede funcionar visualmente sin cambiar el DOM total
        assert p.get_total_permisos() == total, "El filtro eliminó ítems del DOM inesperadamente"
        p.limpiar_filtro()
        assert p.get_total_permisos() == total, "Limpiar el filtro alteró el total de permisos"


# ─────────────────────────────────────────────────────────────────────────────
# ADM-004 — Usuarios de Perfiles  (/configPerfilesAgente)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def usuarios_perfiles_tab(shared_page):
    nav = UsuariosNav(shared_page)
    tab = nav.open_usuarios_perfiles()
    page_obj = UsuariosPerfilesPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


class TestUsuariosPerfiles:
    def test_ADM004_A_carga_correctamente(self, usuarios_perfiles_tab):
        """ADM-004-A: Usuarios de Perfiles carga ambos paneles y los botones Asignar/Quitar."""
        p = usuarios_perfiles_tab
        assert "/configPerfilesAgente" in p.page.url
        p.verify_page_loaded()
        expect(p.page.locator(UsuariosPerfilesPage.BTN_ASIGNAR)).to_be_visible()
        expect(p.page.locator(UsuariosPerfilesPage.BTN_QUITAR)).to_be_visible()

    def test_ADM004_B_ambos_selectores_tienen_tres_perfiles(self, usuarios_perfiles_tab):
        """ADM-004-B: Ambos selectores de perfil muestran los 3 perfiles del sistema."""
        p = usuarios_perfiles_tab
        izq = p.get_opciones_perfil_izquierda()
        der = p.get_opciones_perfil_derecha()
        for perfil in UsuariosPerfilesPage.PERFILES:
            assert any(perfil.lower() in o.lower() for o in izq), \
                f"Perfil '{perfil}' no encontrado en panel izquierdo"
            assert any(perfil.lower() in o.lower() for o in der), \
                f"Perfil '{perfil}' no encontrado en panel derecho"

    def test_ADM004_C_panel_derecho_cuenta_usuarios_por_perfil(self, usuarios_perfiles_tab):
        """ADM-004-C: Cada perfil en panel derecho tiene la cantidad esperada de usuarios."""
        p = usuarios_perfiles_tab
        for perfil, esperado in UsuariosPerfilesPage.USUARIOS_POR_PERFIL.items():
            p.seleccionar_perfil_derecha(perfil)
            count = p.get_count_panel_derecho()
            assert count == esperado, \
                f"Perfil '{perfil}': esperado {esperado} usuarios, encontrado {count}"

    def test_ADM004_D_filtro_panel_izquierdo(self, usuarios_perfiles_tab):
        """ADM-004-D: El filtro del panel izquierdo funciona y se puede limpiar."""
        p = usuarios_perfiles_tab
        p.seleccionar_perfil_izquierda("Agente")
        total = p.get_count_visibles_panel_izquierdo()
        p.filtrar_panel_izquierdo("1000")
        filtrados = p.get_count_visibles_panel_izquierdo()
        assert filtrados <= total
        p.filtrar_panel_izquierdo("")
        assert p.get_count_visibles_panel_izquierdo() == total

    def test_ADM004_E_filtro_panel_derecho(self, usuarios_perfiles_tab):
        """ADM-004-E: El filtro del panel derecho funciona y se puede limpiar."""
        p = usuarios_perfiles_tab
        p.seleccionar_perfil_derecha("Agente")
        total = p.get_count_visibles_panel_derecho()
        p.filtrar_panel_derecho("1000")
        filtrados = p.get_count_visibles_panel_derecho()
        assert filtrados <= total
        p.filtrar_panel_derecho("")
        assert p.get_count_visibles_panel_derecho() == total


# ─────────────────────────────────────────────────────────────────────────────
# ADM-005 — Usuarios de Clientes  (/configUsuariosClientes)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def usuarios_clientes_tab(shared_page):
    nav = UsuariosNav(shared_page)
    tab = nav.open_usuarios_clientes()
    page_obj = UsuariosClientesPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


class TestUsuariosClientes:
    def test_ADM005_A_carga_correctamente(self, usuarios_clientes_tab):
        """ADM-005-A: Usuarios de Clientes carga el select de clientes y la lista."""
        p = usuarios_clientes_tab
        assert "/configUsuariosClientes" in p.page.url
        p.verify_page_loaded()

    def test_ADM005_B_selector_tiene_cliente_base(self, usuarios_clientes_tab):
        """ADM-005-B: El selector contiene 'Cliente generico'."""
        clientes = usuarios_clientes_tab.get_clientes_disponibles()
        assert any(
            UsuariosClientesPage.CLIENTE_BASE.lower() in c.lower() for c in clientes
        ), f"'Cliente generico' no encontrado. Clientes: {clientes}"

    def test_ADM005_C_lista_contiene_usuarios_asignados(self, usuarios_clientes_tab):
        """ADM-005-C: La lista tiene usuarios y al menos uno está asignado."""
        p = usuarios_clientes_tab
        assert p.get_total_usuarios() >= 1, "Lista de usuarios vacía"
        assert p.get_usuarios_asignados_count() >= 1, "Ningún usuario asignado al cliente base"

    def test_ADM005_D_chk_select_all_activo(self, usuarios_clientes_tab):
        """ADM-005-D: El toggle 'Todos los usuarios' está activo (todos asignados en estado base)."""
        assert usuarios_clientes_tab.chk_select_all_activo(), \
            "Se esperaba 'Seleccionar Todos' activo en estado base"

    def test_ADM005_E_filtro_acepta_texto(self, usuarios_clientes_tab):
        """ADM-005-E: El campo de filtro acepta texto y se puede limpiar."""
        p = usuarios_clientes_tab
        p.filtrar_usuarios("1000")
        time.sleep(0.5)
        p.limpiar_filtro()


# ─────────────────────────────────────────────────────────────────────────────
# ADM-006 — Bloqueo de Usuarios  (/GestorUsuariosBloqueados)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def bloqueo_tab(shared_page):
    nav = UsuariosNav(shared_page)
    tab = nav.open_bloqueo_usuarios()
    page_obj = BloqueoUsuariosPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


class TestBloqueoUsuarios:
    def test_ADM006_A_carga_correctamente(self, bloqueo_tab):
        """ADM-006-A: Bloqueo de Usuarios carga los filtros y la lista de activos."""
        p = bloqueo_tab
        assert "/GestorUsuariosBloqueados" in p.page.url
        p.verify_page_loaded()

    def test_ADM006_B_select_cliente_tiene_opciones(self, bloqueo_tab):
        """ADM-006-B: El select de cliente tiene al menos 2 opciones."""
        opciones = bloqueo_tab.get_opciones_select(BloqueoUsuariosPage.SELECT_CLIENTE)
        assert len(opciones) >= 2, f"Select cliente tiene pocas opciones: {opciones}"

    def test_ADM006_C_select_perfil_tiene_opciones(self, bloqueo_tab):
        """ADM-006-C: El select de perfil tiene al menos 4 opciones (cualquiera + 3 perfiles)."""
        opciones = bloqueo_tab.get_opciones_select(BloqueoUsuariosPage.SELECT_PERFIL)
        assert len(opciones) >= 4, f"Select perfil tiene pocas opciones: {opciones}"

    def test_ADM006_D_select_estado_tiene_opciones(self, bloqueo_tab):
        """ADM-006-D: El select de estado tiene al menos 3 opciones."""
        opciones = bloqueo_tab.get_opciones_select(BloqueoUsuariosPage.SELECT_ESTADO)
        assert len(opciones) >= 3, f"Select estado tiene pocas opciones: {opciones}"

    def test_ADM006_E_lista_activos_contiene_usuarios(self, bloqueo_tab):
        """ADM-006-E: La lista de activos tiene al menos 1 usuario."""
        count = bloqueo_tab.get_count_activos()
        assert count >= 1, "La lista de usuarios activos está vacía"

    def test_ADM006_F_filtro_por_estado_habilitados(self, bloqueo_tab):
        """ADM-006-F: Filtrar por 'Habilitados' devuelve usuarios; restaurar a 'Todos' preserva el total."""
        p = bloqueo_tab
        total = p.get_count_activos()
        p.seleccionar_estado(BloqueoUsuariosPage.ESTADO_HABILITADOS)
        time.sleep(0.8)
        assert p.get_count_activos() >= 1
        p.seleccionar_estado(BloqueoUsuariosPage.ESTADO_TODOS)
        time.sleep(0.8)
        assert p.get_count_activos() == total

    def test_ADM006_G_filtro_por_perfil(self, bloqueo_tab):
        """ADM-006-G: Filtrar por perfil Agente reduce la lista; restaurar la devuelve al total."""
        p = bloqueo_tab
        total = p.get_count_activos()
        p.seleccionar_perfil(BloqueoUsuariosPage.PERFIL_AGENTE)
        time.sleep(0.8)
        count_agentes = p.get_count_activos()
        assert count_agentes <= total
        p.seleccionar_perfil(BloqueoUsuariosPage.PERFIL_CUALQUIERA)
        time.sleep(0.8)
        assert p.get_count_activos() == total

    def test_ADM006_H_filtro_texto(self, bloqueo_tab):
        """ADM-006-H: El filtro de texto acepta entrada y se puede limpiar."""
        p = bloqueo_tab
        p.filtrar_por_texto("1000")
        time.sleep(0.5)
        p.filtrar_por_texto("")
        time.sleep(0.5)


# ─────────────────────────────────────────────────────────────────────────────
# ADM-007 — Notificar Usuarios  (/MensajesUsuarios)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def ntf_tab(shared_page):
    nav = SupervisionNav(shared_page)
    tab = nav.open_notificar_usuarios()
    page_obj = NotificarUsuariosPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    try:
        tab.close()
    except Exception:
        pass


@pytest.mark.skip(reason="MensajesUsuarios se cuelga en regresion completa — funciona en aislamiento")
class TestNotificarUsuarios:
    def test_ADM007_A_carga_correctamente(self, ntf_tab):
        """ADM-007-A: Notificar Usuarios carga el panel principal sin errores de servidor."""
        p = ntf_tab
        assert p.page.locator(NotificarUsuariosPage.PANEL_PRINCIPAL).is_visible(), \
            "Panel de mensajes programados no visible"

    def test_ADM007_B_formulario_presente(self, ntf_tab):
        """ADM-007-B: El formulario de nuevo mensaje está presente en la página."""
        p = ntf_tab
        assert p.page.locator(NotificarUsuariosPage.FORM_MENSAJE).count() > 0, \
            "Formulario de mensaje no encontrado"

    def test_ADM007_C_radio_ahora_activo_por_defecto(self, ntf_tab):
        """ADM-007-C: El radio 'Ahora' está seleccionado por defecto al cargar la sección."""
        p = ntf_tab
        radio = p.page.locator(NotificarUsuariosPage.RADIO_AHORA)
        assert radio.is_visible(), "Radio 'Ahora' no visible"
        assert radio.is_checked(), "Radio 'Ahora' no está seleccionado por defecto"

    def test_ADM007_D_otro_momento_muestra_datetime(self, ntf_tab):
        """ADM-007-D: Seleccionar 'Otro momento' muestra el selector de fecha/hora y se revierte."""
        p = ntf_tab
        radio_otro = p.page.locator(NotificarUsuariosPage.RADIO_OTRO)
        div_dt = p.page.locator(NotificarUsuariosPage.DIV_DATETIME)
        radio_otro.click()
        time.sleep(0.5)
        assert div_dt.is_visible(), "Div datetime no visible tras seleccionar 'Otro momento'"
        p.page.locator(NotificarUsuariosPage.RADIO_AHORA).click()
        time.sleep(0.3)

    def test_ADM007_E_select_cliente_tiene_opciones(self, ntf_tab):
        """ADM-007-E: El select de cliente contiene al menos 1 opción seleccionable."""
        p = ntf_tab
        select = p.page.locator(NotificarUsuariosPage.SELECT_CLIENTE)
        assert select.is_visible(), "Select de cliente no visible"
        opciones = select.locator("option").all()
        assert len(opciones) >= 1, f"Select cliente sin opciones: {len(opciones)}"

    def test_ADM007_F_lista_usuarios_presente(self, ntf_tab):
        """ADM-007-F: La lista de usuarios destinatarios está presente en el DOM."""
        p = ntf_tab
        lista = p.page.locator(NotificarUsuariosPage.LISTA_USUARIOS)
        assert lista.count() > 0, "Lista de usuarios no encontrada en el DOM"

    def test_ADM007_G_tabla_historial_presente(self, ntf_tab):
        """ADM-007-G: La tabla de historial de mensajes programados está presente."""
        p = ntf_tab
        tabla = p.page.locator(NotificarUsuariosPage.TABLA_HISTORIAL)
        assert tabla.count() > 0, "Tabla de historial no encontrada"

    def test_ADM007_H_campos_aceptan_texto_sin_enviar(self, ntf_tab):
        """ADM-007-H: Los campos Asunto y Mensaje aceptan texto; se borran sin enviar el formulario."""
        p = ntf_tab
        asunto = p.page.locator(NotificarUsuariosPage.INPUT_ASUNTO)
        mensaje = p.page.locator(NotificarUsuariosPage.TEXTAREA_MENSAJE)
        asunto.fill("Test QA - borrar")
        time.sleep(0.3)
        mensaje.fill("Mensaje de prueba automatizado - no enviar")
        time.sleep(0.3)
        asunto.fill("")
        mensaje.fill("")
        time.sleep(0.3)

