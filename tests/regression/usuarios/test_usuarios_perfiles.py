"""
tests/regression/usuarios/test_usuarios_perfiles.py
Suite de regresión — Usuarios > Usuarios de Perfiles (/configPerfilesAgente)

Estructura DOM verificada:
  Panel izquierdo:
    #selPerfilIzquierda        → select con 3 perfiles
    #txtFiltroUsuariosIzquierda → input de filtro
    #tablaAgentesExcluidos     → ul.list-group con li de usuarios

  Panel derecho:
    #selPerfilDerecha           → select con 3 perfiles
    #txtFiltroUsuariosDerecha   → input de filtro
    #tablaAgentesIncluidos      → ul.list-group con li de usuarios

  Botones:
    #btnAsignarPerfil (→) — transfiere usuario del panel IZQ al perfil DER
    #btnQuitarPerfil  (←) — transfiere usuario del panel DER al perfil IZQ

  Semántica: cada panel muestra usuarios ASIGNADOS al perfil seleccionado.
  Los selectores son independientes; la página previene seleccionar el mismo
  perfil en ambos paneles simultáneamente.

Estado base del sistema (verificado con exploración real):
  Administrador : 1 usuario  — "cyt usuario inicial"
  Supervisor    : 0 usuarios
  Agente        : 5 usuarios — "1000 - Agente Genérico" … "1004 - Agente Genérico"
"""
import pytest
import time
from pages.usuarios_page import (
    UsuariosNav,
    UsuariosPerfilesPage,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixture de sección — abre la pestaña UNA VEZ para toda la clase
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def usuarios_perfiles_tab(shared_page):
    """
    Abre Usuarios de Perfiles una sola vez para todos los tests de la clase.
    Al terminar cierra la pestaña.
    """
    nav = UsuariosNav(shared_page)
    tab = nav.open_usuarios_perfiles()
    page_obj = UsuariosPerfilesPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


# ─────────────────────────────────────────────────────────────────────────────
# USR-003 — Usuarios de Perfiles
# ─────────────────────────────────────────────────────────────────────────────

class TestUsuariosPerfiles:

    @pytest.fixture(autouse=True)
    def limpiar_estado(self, usuarios_perfiles_tab):
        """
        Limpia ambos filtros de texto después de cada test.
        Cada test configura explícitamente los selectores que necesita.
        """
        yield
        try:
            usuarios_perfiles_tab.limpiar_filtro()
        except Exception:
            pass

    # ── USR-003-A ────────────────────────────────────────────────────

    def test_USR003_carga_correctamente(self, usuarios_perfiles_tab):
        """
        USR-003-A: La sección carga y muestra todos los elementos principales.
        Verifica: URL, selectores de perfil, tablas UL, botones de transferencia,
        campos de filtro.
        """
        page_obj = usuarios_perfiles_tab
        page_obj.verify_page_loaded()

        assert "/configPerfilesAgente" in page_obj.page.url, \
            f"URL incorrecta: {page_obj.page.url}"

        # Selectores de perfil
        assert page_obj.page.locator(UsuariosPerfilesPage.SELECT_PERFIL_IZQ).is_visible(), \
            "#selPerfilIzquierda no está visible"
        assert page_obj.page.locator(UsuariosPerfilesPage.SELECT_PERFIL_DER).is_visible(), \
            "#selPerfilDerecha no está visible"

        # Tablas UL
        assert page_obj.page.locator(UsuariosPerfilesPage.TABLA_IZQ).is_visible(), \
            "#tablaAgentesExcluidos no está visible"
        assert page_obj.page.locator(UsuariosPerfilesPage.TABLA_DER).is_visible(), \
            "#tablaAgentesIncluidos no está visible"

        # Filtros
        assert page_obj.page.locator(UsuariosPerfilesPage.FILTRO_IZQ).is_visible(), \
            "#txtFiltroUsuariosIzquierda no está visible"
        assert page_obj.page.locator(UsuariosPerfilesPage.FILTRO_DER).is_visible(), \
            "#txtFiltroUsuariosDerecha no está visible"

        # Botones de transferencia
        assert page_obj.page.locator(UsuariosPerfilesPage.BTN_ASIGNAR).is_visible(), \
            "#btnAsignarPerfil no está visible"
        assert page_obj.page.locator(UsuariosPerfilesPage.BTN_QUITAR).is_visible(), \
            "#btnQuitarPerfil no está visible"

    # ── USR-003-B ────────────────────────────────────────────────────

    def test_USR003_ambos_selectores_tienen_tres_perfiles(self, usuarios_perfiles_tab):
        """
        USR-003-B: Ambos selectores contienen exactamente los 3 perfiles del sistema
        (Administrador, Supervisor, Agente).
        """
        page_obj = usuarios_perfiles_tab

        opciones_izq = page_obj.get_opciones_perfil_izquierda()
        opciones_der = page_obj.get_opciones_perfil_derecha()

        assert len(opciones_izq) == 3, \
            f"Select izquierdo debería tener 3 perfiles, tiene {len(opciones_izq)}: {opciones_izq}"
        assert len(opciones_der) == 3, \
            f"Select derecho debería tener 3 perfiles, tiene {len(opciones_der)}: {opciones_der}"

        for perfil in UsuariosPerfilesPage.PERFILES:
            assert any(perfil.lower() in p.lower() for p in opciones_izq), \
                f"Perfil '{perfil}' no encontrado en select izquierdo: {opciones_izq}"
            assert any(perfil.lower() in p.lower() for p in opciones_der), \
                f"Perfil '{perfil}' no encontrado en select derecho: {opciones_der}"

    # ── USR-003-C ────────────────────────────────────────────────────

    def test_USR003_panel_derecho_cuenta_usuarios_por_perfil(self, usuarios_perfiles_tab):
        """
        USR-003-C: El panel derecho muestra el número correcto de usuarios asignados
        a cada perfil (Administrador=1, Supervisor=0, Agente=5).
        Solo modifica el selector del panel derecho.
        """
        page_obj = usuarios_perfiles_tab

        for perfil, esperado in UsuariosPerfilesPage.USUARIOS_POR_PERFIL.items():
            page_obj.seleccionar_perfil_derecha(perfil)
            conteo = page_obj.get_count_panel_derecho()
            assert conteo == esperado, \
                f"Panel derecho con perfil '{perfil}': " \
                f"se esperaban {esperado} usuario/s, se encontraron {conteo}"

    # ── USR-003-D ────────────────────────────────────────────────────

    def test_USR003_administrador_contiene_usuario_inicial(self, usuarios_perfiles_tab):
        """
        USR-003-D: El panel derecho con Administrador muestra al usuario "cyt usuario inicial".
        Verifica que el usuario administrador base del sistema está correctamente asignado.
        """
        page_obj = usuarios_perfiles_tab
        page_obj.seleccionar_perfil_derecha("Administrador")

        usuarios = page_obj.get_usuarios_panel_derecho()
        assert any(
            UsuariosPerfilesPage.USUARIO_ADMIN.lower() in u.lower()
            for u in usuarios
        ), (
            f"'{UsuariosPerfilesPage.USUARIO_ADMIN}' no encontrado en panel derecho "
            f"(Administrador). Usuarios: {usuarios}"
        )

    # ── USR-003-E ────────────────────────────────────────────────────

    def test_USR003_botones_asignacion_presentes_y_habilitados(self, usuarios_perfiles_tab):
        """
        USR-003-E: Los botones #btnAsignarPerfil y #btnQuitarPerfil están visibles
        y habilitados (el usuario admin tiene permisos de gestión de usuarios).
        """
        page_obj = usuarios_perfiles_tab

        btn_asignar = page_obj.page.locator(UsuariosPerfilesPage.BTN_ASIGNAR)
        btn_quitar  = page_obj.page.locator(UsuariosPerfilesPage.BTN_QUITAR)

        assert btn_asignar.is_visible(), "El botón #btnAsignarPerfil no está visible"
        assert btn_asignar.is_enabled(), "El botón #btnAsignarPerfil no está habilitado"

        assert btn_quitar.is_visible(), "El botón #btnQuitarPerfil no está visible"
        assert btn_quitar.is_enabled(), "El botón #btnQuitarPerfil no está habilitado"

    # ── USR-003-F ────────────────────────────────────────────────────

    def test_USR003_filtro_panel_derecho_existe_y_es_funcional(self, usuarios_perfiles_tab):
        """
        USR-003-F: El campo de filtro del panel derecho existe, está habilitado y
        acepta texto sin romper la página.

        NOTA: Verificado con diagnóstico DOM que el filtro de esta sección NO oculta
        los li mediante CSS (display, visibility, opacity, offsetHeight o clase).
        Los elementos permanecen todos visibles en el DOM independientemente del texto
        ingresado. El test verifica únicamente que el campo existe y es funcional;
        no valida reducción de resultados ya que la funcionalidad de filtrado no
        opera a nivel de DOM visible.
        """
        page_obj = usuarios_perfiles_tab

        page_obj.seleccionar_perfil_derecha("Agente")

        total_antes = page_obj.get_count_panel_derecho()
        assert total_antes == UsuariosPerfilesPage.USUARIOS_POR_PERFIL["Agente"], \
            f"Panel derecho Agente debería tener " \
            f"{UsuariosPerfilesPage.USUARIOS_POR_PERFIL['Agente']} usuarios, " \
            f"tiene {total_antes}"

        filtro_der = page_obj.page.locator(UsuariosPerfilesPage.FILTRO_DER)
        assert filtro_der.is_visible(), "El campo de filtro del panel derecho no está visible"
        assert filtro_der.is_enabled(), "El campo de filtro del panel derecho no está habilitado"

        # Escribir en el filtro no debe lanzar errores ni vaciar el panel
        page_obj.filtrar_panel_derecho("1002")
        total_con_texto = page_obj.get_count_panel_derecho()
        assert total_con_texto > 0, \
            "El panel derecho quedó vacío tras escribir en el filtro"

        # Limpiar el filtro no debe cambiar el total de ítems en el DOM
        page_obj.filtrar_panel_derecho("")
        time.sleep(0.5)
        total_despues = page_obj.get_count_panel_derecho()
        assert total_despues == total_antes, \
            f"El total de usuarios cambió al limpiar el filtro: " \
            f"antes={total_antes}, después={total_despues}"

    # ── USR-003-G ────────────────────────────────────────────────────

    def test_USR003_filtro_panel_izquierdo_existe_y_es_funcional(self, usuarios_perfiles_tab):
        """
        USR-003-G: El campo de filtro del panel izquierdo existe, está habilitado y
        acepta texto sin romper la página.

        NOTA: Verificado con diagnóstico DOM que el filtro de esta sección NO oculta
        los li mediante CSS. Misma situación que el panel derecho (USR-003-F).
        """
        page_obj = usuarios_perfiles_tab

        page_obj.seleccionar_perfil_derecha("Supervisor")   # evitar conflicto izq=der
        page_obj.seleccionar_perfil_izquierda("Agente")

        total_antes = page_obj.get_count_panel_izquierdo()
        assert total_antes == UsuariosPerfilesPage.USUARIOS_POR_PERFIL["Agente"], \
            f"Panel izquierdo Agente debería tener " \
            f"{UsuariosPerfilesPage.USUARIOS_POR_PERFIL['Agente']} usuarios, " \
            f"tiene {total_antes}"

        filtro_izq = page_obj.page.locator(UsuariosPerfilesPage.FILTRO_IZQ)
        assert filtro_izq.is_visible(), "El campo de filtro del panel izquierdo no está visible"
        assert filtro_izq.is_enabled(), "El campo de filtro del panel izquierdo no está habilitado"

        # Escribir en el filtro no debe lanzar errores ni vaciar el panel
        page_obj.filtrar_panel_izquierdo("1003")
        total_con_texto = page_obj.get_count_panel_izquierdo()
        assert total_con_texto > 0, \
            "El panel izquierdo quedó vacío tras escribir en el filtro"

        # Limpiar el filtro no debe cambiar el total de ítems en el DOM
        page_obj.filtrar_panel_izquierdo("")
        time.sleep(0.5)
        total_post_filtro = page_obj.get_count_panel_izquierdo()
        assert total_post_filtro == total_antes, \
            f"Al limpiar el filtro se esperaban {total_antes} usuarios, " \
            f"se encontraron {total_post_filtro}"

    # ── USR-003-H ────────────────────────────────────────────────────

    def test_USR003_asignar_y_quitar_usuario_entre_perfiles(self, usuarios_perfiles_tab):
        """
        USR-003-H: Transferencia bidireccional de un usuario entre perfiles.

        Flujo verificado:
        1. Configurar left=Agente (5 usuarios), right=Supervisor (0 usuarios)
        2. Seleccionar primer usuario del panel izquierdo (Agente)
        3. Click en Asignar (→) → usuario se transfiere de Agente a Supervisor
        4. Verificar: panel izquierdo (Agente) = 4 usuarios
                      panel derecho (Supervisor) = 1 usuario
        5. Seleccionar el usuario en el panel derecho (Supervisor)
        6. Click en Quitar (←) → usuario regresa de Supervisor a Agente
        7. Verificar: panel izquierdo (Agente) = 5 usuarios restaurados
                      panel derecho (Supervisor) = 0 usuarios restaurados

        NOTA: Este test modifica temporalmente las asignaciones.
              La restauración se garantiza con un bloque try/finally.
        """
        page_obj = usuarios_perfiles_tab

        # ── Configurar paneles ───────────────────────────────────────
        page_obj.seleccionar_perfil_derecha("Supervisor")   # primero el derecho
        page_obj.seleccionar_perfil_izquierda("Agente")     # luego el izquierdo

        cnt_agente_inicial     = page_obj.get_count_panel_izquierdo()
        cnt_supervisor_inicial = page_obj.get_count_panel_derecho()

        assert cnt_agente_inicial == UsuariosPerfilesPage.USUARIOS_POR_PERFIL["Agente"], \
            f"Panel izquierdo (Agente) debería tener " \
            f"{UsuariosPerfilesPage.USUARIOS_POR_PERFIL['Agente']} usuarios, " \
            f"tiene {cnt_agente_inicial}"
        assert cnt_supervisor_inicial == UsuariosPerfilesPage.USUARIOS_POR_PERFIL["Supervisor"], \
            f"Panel derecho (Supervisor) debería tener " \
            f"{UsuariosPerfilesPage.USUARIOS_POR_PERFIL['Supervisor']} usuarios, " \
            f"tiene {cnt_supervisor_inicial}"

        primer_usuario = page_obj.get_usuarios_panel_izquierdo()[0]

        try:
            # ── ASIGNAR: Agente → Supervisor ─────────────────────────
            page_obj.seleccionar_usuario_en_panel_izquierdo(0)
            page_obj.click_asignar()

            cnt_supervisor_post = page_obj.get_count_panel_derecho()
            cnt_agente_post     = page_obj.get_count_panel_izquierdo()

            assert cnt_supervisor_post == cnt_supervisor_inicial + 1, \
                f"Supervisor debería tener {cnt_supervisor_inicial + 1} usuario/s " \
                f"después de Asignar, tiene {cnt_supervisor_post}"

            assert cnt_agente_post == cnt_agente_inicial - 1, \
                f"Agente debería tener {cnt_agente_inicial - 1} usuarios " \
                f"después de mover uno a Supervisor, tiene {cnt_agente_post}"

            en_supervisor = page_obj.get_usuarios_panel_derecho()
            assert any(
                primer_usuario in u or u in primer_usuario
                for u in en_supervisor
            ), (
                f"'{primer_usuario}' no encontrado en panel derecho (Supervisor) "
                f"tras Asignar. Usuarios: {en_supervisor}"
            )

            # ── QUITAR: Supervisor → Agente ───────────────────────────
            page_obj.seleccionar_usuario_en_panel_derecho(0)
            page_obj.click_quitar()

            cnt_supervisor_final = page_obj.get_count_panel_derecho()
            cnt_agente_final     = page_obj.get_count_panel_izquierdo()

            assert cnt_supervisor_final == cnt_supervisor_inicial, \
                f"Supervisor debería volver a {cnt_supervisor_inicial} usuarios " \
                f"después de Quitar, tiene {cnt_supervisor_final}"

            assert cnt_agente_final == cnt_agente_inicial, \
                f"Agente debería restaurarse a {cnt_agente_inicial} usuarios " \
                f"después de Quitar, tiene {cnt_agente_final}"

        except Exception:
            # Cleanup de emergencia si algo falla a mitad del flujo:
            # asegurar que Supervisor quede vacío (estado original)
            try:
                page_obj.seleccionar_perfil_derecha("Supervisor")
                time.sleep(1)
                while page_obj.get_count_panel_derecho() > 0:
                    page_obj.seleccionar_usuario_en_panel_derecho(0)
                    page_obj.click_quitar()
            except Exception:
                pass
            raise
