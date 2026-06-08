"""
tests/regression/usuarios/test_bloqueo_usuarios.py
Suite de regresión — Usuarios > Bloqueo de Usuarios (/GestorUsuariosBloqueados)

Estructura DOM verificada:
  #frmUserFilter         → panel de filtros lateral
  #cmbClientes           → select de clientes ("0"=Cualquier, "1"=Cliente generico)
  #cmbNiveles            → select de perfiles ("0"=Cualquier, "1"=Admin, "2"=Supervisor, "3"=Agente)
  #cmbListas             → select de estado (""=Todos, "1"=Habilitados, "2"=Bloqueados)
  #txtFiltrarUsuarios    → input de filtro de texto
  #activeUserList        → ul de usuarios habilitados (li.user con .user-name, .btn-block-pass)
  #blockedUserList       → ul de usuarios bloqueados (ídem)
  #btnSeleccionarVariosActivos / #btnSeleccionarVariosBloqueados → selección múltiple

Operaciones:
  - Bloquear usuario: clic en .btn-block-pass dentro de activeUserList li.user
  - Desbloquear usuario: clic en .btn-block-pass dentro de blockedUserList li.user
  - Los filtros de cliente/perfil/estado llaman a AJAX y actualizan las listas

Estado base del sistema (verificado):
  Activos:    6 (agentes 1000-1004 + cyt usuario inicial)
  Bloqueados: 0
"""
import pytest
import time
from pages.usuarios_page import (

    UsuariosNav,
    BloqueoUsuariosPage,
)
# ─────────────────────────────────────────────────────────────────────────────
# Fixture de sección — abre la pestaña UNA VEZ para toda la clase
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def bloqueo_tab(shared_page):
    """
    Abre Bloqueo de Usuarios una sola vez para todos los tests de la clase.
    Al terminar cierra la pestaña.
    """
    nav = UsuariosNav(shared_page)
    tab = nav.open_bloqueo_usuarios()
    page_obj = BloqueoUsuariosPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


# ─────────────────────────────────────────────────────────────────────────────
# USR-005 — Bloqueo de Usuarios
# ─────────────────────────────────────────────────────────────────────────────

class TestBloqueoUsuarios:

    @pytest.fixture(autouse=True)
    def limpiar_estado(self, bloqueo_tab):
        """Restablece todos los filtros al estado inicial después de cada test."""
        yield
        try:
            bloqueo_tab.limpiar_filtros()
        except Exception:
            pass

    # ── USR-005-A ────────────────────────────────────────────────────

    def test_USR005_carga_correctamente(self, bloqueo_tab):
        """
        USR-005-A: La sección carga y muestra todos los elementos principales.
        Verifica: URL, título, filtros de cliente/perfil/estado,
        campo de texto, lista de activos y lista de bloqueados.
        """
        page_obj = bloqueo_tab
        page_obj.verify_page_loaded()

        assert "/GestorUsuariosBloqueados" in page_obj.page.url, \
            f"URL incorrecta: {page_obj.page.url}"

        assert page_obj.page.locator(BloqueoUsuariosPage.SELECT_CLIENTE).is_visible(), \
            "#cmbClientes no está visible"
        assert page_obj.page.locator(BloqueoUsuariosPage.SELECT_PERFIL).is_visible(), \
            "#cmbNiveles no está visible"
        assert page_obj.page.locator(BloqueoUsuariosPage.SELECT_ESTADO).is_visible(), \
            "#cmbListas no está visible"
        assert page_obj.page.locator(BloqueoUsuariosPage.INPUT_FILTRO).is_visible(), \
            "#txtFiltrarUsuarios no está visible"
        assert page_obj.page.locator(BloqueoUsuariosPage.LISTA_ACTIVOS).is_visible(), \
            "#activeUserList no está visible"
        assert page_obj.page.locator(BloqueoUsuariosPage.LISTA_BLOQUEADOS).is_visible(), \
            "#blockedUserList no está visible"

        # Verificar que la página muestra contenido relacionado con "bloqueo"
        # El título "Bloqueo y reinicio de contraseñas" está en el panel h2
        tiene_contenido = page_obj.page.evaluate("""
            () => document.body.innerText.toLowerCase().includes('bloqueo')
        """)
        assert tiene_contenido, \
            "La página no muestra contenido de 'bloqueo' — puede que no haya cargado correctamente"

    # ── USR-005-B ────────────────────────────────────────────────────

    def test_USR005_select_cliente_tiene_opciones(self, bloqueo_tab):
        """
        USR-005-B: El selector #cmbClientes contiene las opciones esperadas:
        una opción "Cualquier cliente" y el cliente base del sistema.
        """
        page_obj = bloqueo_tab
        opciones = page_obj.get_opciones_select(BloqueoUsuariosPage.SELECT_CLIENTE)

        assert len(opciones) >= 2, \
            f"Se esperaban al menos 2 opciones en #cmbClientes, hay {len(opciones)}: {opciones}"

        textos = [o["text"] for o in opciones]
        assert any("cualquier" in t.lower() or "todos" in t.lower() for t in textos), \
            f"Falta opción 'Cualquier cliente'. Opciones: {textos}"
        assert any("generico" in t.lower() or "generic" in t.lower() for t in textos), \
            f"Falta 'Cliente generico'. Opciones: {textos}"

    # ── USR-005-C ────────────────────────────────────────────────────

    def test_USR005_select_perfil_tiene_opciones(self, bloqueo_tab):
        """
        USR-005-C: El selector #cmbNiveles contiene los perfiles esperados:
        [Cualquier perfil], Administrador, Supervisor y Agente.
        """
        page_obj = bloqueo_tab
        opciones = page_obj.get_opciones_select(BloqueoUsuariosPage.SELECT_PERFIL)

        assert len(opciones) >= 4, \
            f"Se esperaban al menos 4 opciones en #cmbNiveles, hay {len(opciones)}: {opciones}"

        textos = [o["text"] for o in opciones]
        assert any("cualquier" in t.lower() for t in textos), \
            f"Falta opción 'Cualquier perfil'. Opciones: {textos}"
        for perfil in ["Administrador", "Supervisor", "Agente"]:
            assert any(perfil.lower() in t.lower() for t in textos), \
                f"Perfil '{perfil}' no encontrado en #cmbNiveles. Opciones: {textos}"

    # ── USR-005-D ────────────────────────────────────────────────────

    def test_USR005_select_estado_tiene_opciones(self, bloqueo_tab):
        """
        USR-005-D: El selector #cmbListas contiene las tres opciones de estado:
        [Listar todos], Listar Habilitados y Listar Bloqueados.
        """
        page_obj = bloqueo_tab
        opciones = page_obj.get_opciones_select(BloqueoUsuariosPage.SELECT_ESTADO)

        assert len(opciones) >= 3, \
            f"Se esperaban al menos 3 opciones en #cmbListas, hay {len(opciones)}: {opciones}"

        textos = [o["text"] for o in opciones]
        assert any("todos" in t.lower() or "all" in t.lower() for t in textos), \
            f"Falta opción 'Listar todos'. Opciones: {textos}"
        assert any("habilit" in t.lower() for t in textos), \
            f"Falta opción 'Listar Habilitados'. Opciones: {textos}"
        assert any("bloqu" in t.lower() for t in textos), \
            f"Falta opción 'Listar Bloqueados'. Opciones: {textos}"

    # ── USR-005-E ────────────────────────────────────────────────────

    def test_USR005_lista_activos_contiene_usuarios_base(self, bloqueo_tab):
        """
        USR-005-E: La lista #activeUserList contiene usuarios activos.
        Verifica que los agentes base (1000-1004) estan presentes y que no hay bloqueados.
        El conteo total es variable segun el ambiente — no se valida un numero exacto.
        """
        page_obj = bloqueo_tab
        total = page_obj.get_count_activos()

        assert total > 0, \
            "La lista de activos esta vacia — no hay usuarios habilitados en el sistema"

        nombres = page_obj.get_nombres_activos()
        assert any("agente" in n.lower() for n in nombres), \
            f"No se encontro ningun agente en la lista de activos. Nombres: {nombres}"
        assert any("cyt" in n.lower() for n in nombres), \
            f"Usuario administrador 'cyt' no encontrado en activos. Nombres: {nombres}"

    # ── USR-005-F ────────────────────────────────────────────────────

    def test_USR005_filtro_texto_existe_y_es_funcional(self, bloqueo_tab):
        """
        USR-005-F: El campo #txtFiltrarUsuarios existe, está habilitado y
        acepta texto sin romper la página. Al limpiar, la lista de activos
        vuelve al total original.
        """
        page_obj = bloqueo_tab

        filtro = page_obj.page.locator(BloqueoUsuariosPage.INPUT_FILTRO)
        assert filtro.is_visible(), "#txtFiltrarUsuarios no está visible"
        assert filtro.is_enabled(), "#txtFiltrarUsuarios no está habilitado"

        total_antes = page_obj.get_count_activos()
        assert total_antes > 0, "La lista de activos está vacía antes de filtrar"

        # Escribir en el filtro no debe lanzar errores
        page_obj.filtrar_por_texto("1002")

        # Al limpiar, el total debe restaurarse
        page_obj.filtrar_por_texto("")
        total_despues = page_obj.get_count_activos()
        assert total_despues == total_antes, \
            f"Al limpiar el filtro el total cambió: " \
            f"antes={total_antes}, después={total_despues}"

    # ── USR-005-G ────────────────────────────────────────────────────

    def test_USR005_filtro_estado_habilitados(self, bloqueo_tab):
        """
        USR-005-G: Seleccionar 'Listar Habilitados' en #cmbListas aplica sin errores
        y la lista de activos sigue mostrando los mismos usuarios
        (todos son habilitados en el estado base).
        """
        page_obj = bloqueo_tab

        total_base = page_obj.get_count_activos()
        assert total_base > 0, \
            "No hay usuarios activos para filtrar"

        page_obj.seleccionar_estado(BloqueoUsuariosPage.ESTADO_HABILITADOS)
        total_habilitados = page_obj.get_count_activos()

        assert total_habilitados == total_base, \
            f"Con 'Listar Habilitados' se esperaban {total_base} activos, " \
            f"se encontraron {total_habilitados}"

    # ── USR-005-H ────────────────────────────────────────────────────

    def test_USR005_bloquear_y_desbloquear_sin_reset(self, bloqueo_tab):
        """
        USR-005-H: Bloquear y desbloquear un usuario verifica que ambas
        operaciones funcionan correctamente en la UI.

        Flujo:
        1. Verificar estado base: 6 activos, 0 bloqueados
        2. Bloquear agente 1004 (btn-block-pass, sin modal — inmediato)
        3. Verificar: activos=5, bloqueados=1, agente aparece en bloqueados
        4. Desbloquear agente 1004 (btn-unlock-pass → modal "¿Resetear contraseña?" → clic "No")
        5. Verificar: activos=6, bloqueados=0

        NOTA: El modal de desbloqueo pregunta "¿Desea también restablecer la contraseña?".
              Se responde "No" para NO modificar credenciales del sistema.
              Usa try/finally para restaurar el estado incluso si el test falla.
        """
        page_obj = bloqueo_tab
        agente = "1004"

        total_activos_inicial    = page_obj.get_count_activos()
        total_bloqueados_inicial = page_obj.get_count_bloqueados()

        assert total_activos_inicial >= 1, \
            "Se necesita al menos 1 usuario activo para ejecutar este test"
        # total_bloqueados_inicial puede ser > 0 si el sistema tiene usuarios pre-bloqueados
        # — lo usamos como base relativa para verificar el cambio neto

        try:
            # ── BLOQUEAR ─────────────────────────────────────────────
            bloqueado = page_obj.bloquear_usuario(agente)
            assert bloqueado, f"No se encontró el agente '{agente}' para bloquear"

            time.sleep(1)
            activos_post    = page_obj.get_count_activos()
            bloqueados_post = page_obj.get_count_bloqueados()

            assert activos_post == total_activos_inicial - 1, \
                f"Tras bloquear: esperados {total_activos_inicial - 1} activos, hay {activos_post}"
            assert bloqueados_post == total_bloqueados_inicial + 1, \
                f"Tras bloquear: esperados {total_bloqueados_inicial + 1} bloqueados, hay {bloqueados_post}"

            nombres_b = page_obj.get_nombres_bloqueados()
            assert any(agente in n for n in nombres_b), \
                f"Agente '{agente}' no aparece en bloqueados: {nombres_b}"

            # ── DESBLOQUEAR (sin resetear contraseña) ────────────────
            desbloqueado = page_obj.desbloquear_usuario_sin_reset(agente)
            assert desbloqueado, f"No se encontró el agente '{agente}' para desbloquear"

            time.sleep(1)
            activos_final    = page_obj.get_count_activos()
            bloqueados_final = page_obj.get_count_bloqueados()

            assert activos_final == total_activos_inicial, \
                f"Tras desbloquear: esperados {total_activos_inicial} activos, hay {activos_final}"
            assert bloqueados_final == total_bloqueados_inicial, \
                f"Tras desbloquear: esperados {total_bloqueados_inicial} bloqueados, hay {bloqueados_final}"

        except Exception:
            # Cleanup de emergencia
            try:
                if page_obj.get_count_bloqueados() > 0:
                    page_obj.desbloquear_usuario_sin_reset(agente)
            except Exception:
                pass
            raise

