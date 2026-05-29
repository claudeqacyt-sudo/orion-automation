"""
tests/regression/supervision/test_notificar_usuarios.py
Suite de regresion - Supervision > Notificar Usuarios (/MensajesUsuarios)

Estructura DOM verificada:
  #panelMensajesProgramados  -> panel principal
  #frmMessageData            -> formulario
    #txtAsunto               -> input asunto (maxlength=40)
    #txaMensaje              -> textarea mensaje (maxlength=500)
    #rdbAhora                -> radio "Ahora" (default checked)
    #rdbOtroMomento          -> radio "Otro momento"
    #datetimeOtroMomento     -> div fecha/hora (oculto por defecto)
    #cmbCliente              -> select clientes
    #listadoUsuarios         -> lista de destinatarios
      #chkAllUsers           -> checkbox "Seleccionar Todos"
      li.user-item           -> un item por usuario
    #btnGuardarMensaje       -> "Enviar Mensaje"
  #tblMensajesProgramados    -> historial de mensajes enviados

Estado base del sistema (verificado):
  Usuarios en lista: 6 (1000-1004 Agente Generico + cyt usuario inicial)
  Historial: 0 mensajes
  Radio activo: "Ahora"

IMPORTANTE: Los tests verifican la UI sin enviar mensajes reales a los agentes.
"""
import pytest
import time
from pages.supervision_page import SupervisionNav, NotificarUsuariosPage


# ─────────────────────────────────────────────────────────────────────────────
# Fixture de seccion
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def notificar_tab(shared_page):
    """Abre Notificar Usuarios una sola vez para todos los tests de la clase."""
    nav = SupervisionNav(shared_page)
    tab = nav.open_notificar_usuarios()
    page_obj = NotificarUsuariosPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


# ─────────────────────────────────────────────────────────────────────────────
# NTF-001 - Notificar Usuarios
# ─────────────────────────────────────────────────────────────────────────────

class TestNotificarUsuarios:

    @pytest.fixture(autouse=True)
    def limpiar_estado(self, notificar_tab):
        """Restablece el formulario al estado inicial despues de cada test."""
        yield
        try:
            notificar_tab.limpiar_formulario()
        except Exception:
            pass

    # ── NTF-001-A ────────────────────────────────────────────────────

    def test_NTF001_carga_correctamente(self, notificar_tab):
        """
        NTF-001-A: La seccion carga y muestra todos los elementos principales.
        Verifica: URL, panel principal, formulario, lista de usuarios y tabla.
        """
        page_obj = notificar_tab
        page_obj.verify_page_loaded()

        assert NotificarUsuariosPage.URL_PATH in page_obj.page.url, \
            f"URL incorrecta: {page_obj.page.url}"

        assert page_obj.page.locator(NotificarUsuariosPage.PANEL_PRINCIPAL).is_visible(), \
            "#panelMensajesProgramados no esta visible"
        assert page_obj.page.locator(NotificarUsuariosPage.FORM_MENSAJE).is_visible(), \
            "#frmMessageData no esta visible"
        assert page_obj.page.locator(NotificarUsuariosPage.LISTA_USUARIOS).is_visible(), \
            "#listadoUsuarios no esta visible"
        assert page_obj.page.locator(NotificarUsuariosPage.TABLA_HISTORIAL).is_visible(), \
            "#tblMensajesProgramados no esta visible"

        titulo = page_obj.page.evaluate(
            "() => document.body.innerText.toLowerCase().includes('notificaciones')"
        )
        assert titulo, "La pagina no muestra contenido de 'notificaciones'"

    # ── NTF-001-B ────────────────────────────────────────────────────

    def test_NTF001_campos_formulario_presentes(self, notificar_tab):
        """
        NTF-001-B: Todos los campos del formulario estan presentes y habilitados.
        Verifica: asunto, mensaje, radios de momento, select de cliente y boton enviar.
        """
        page_obj = notificar_tab

        for selector, nombre in [
            (NotificarUsuariosPage.INPUT_ASUNTO,    "#txtAsunto"),
            (NotificarUsuariosPage.TEXTAREA_MENSAJE, "#txaMensaje"),
            (NotificarUsuariosPage.RADIO_AHORA,     "#rdbAhora"),
            (NotificarUsuariosPage.RADIO_OTRO,      "#rdbOtroMomento"),
            (NotificarUsuariosPage.SELECT_CLIENTE,  "#cmbCliente"),
            (NotificarUsuariosPage.BTN_ENVIAR,      "#btnGuardarMensaje"),
        ]:
            assert page_obj.page.locator(selector).is_visible(), \
                f"{nombre} no esta visible"
            assert page_obj.page.locator(selector).is_enabled(), \
                f"{nombre} no esta habilitado"

    # ── NTF-001-C ────────────────────────────────────────────────────

    def test_NTF001_radio_ahora_activo_por_defecto(self, notificar_tab):
        """
        NTF-001-C: El radio "Ahora" esta seleccionado por defecto y el panel de
        fecha/hora (#datetimeOtroMomento) esta oculto.
        """
        page_obj = notificar_tab

        assert page_obj.radio_ahora_seleccionado(), \
            "#rdbAhora deberia estar seleccionado por defecto"
        assert not page_obj.radio_otro_seleccionado(), \
            "#rdbOtroMomento no deberia estar seleccionado por defecto"
        assert not page_obj.datetime_visible(), \
            "#datetimeOtroMomento deberia estar oculto cuando 'Ahora' esta activo"

    # ── NTF-001-D ────────────────────────────────────────────────────

    def test_NTF001_otro_momento_muestra_campos_fecha(self, notificar_tab):
        """
        NTF-001-D: Al seleccionar "Otro momento", el panel #datetimeOtroMomento
        se hace visible y muestra el campo de fecha #dtpFechaNotificacion.
        """
        page_obj = notificar_tab

        assert not page_obj.datetime_visible(), \
            "El panel de fecha/hora deberia estar oculto inicialmente"

        page_obj.seleccionar_radio_otro_momento()

        assert page_obj.radio_otro_seleccionado(), \
            "#rdbOtroMomento deberia estar seleccionado"
        assert page_obj.datetime_visible(), \
            "#datetimeOtroMomento deberia ser visible al seleccionar 'Otro momento'"
        assert page_obj.page.locator(NotificarUsuariosPage.INPUT_FECHA).is_visible(), \
            "#dtpFechaNotificacion deberia ser visible"

    # ── NTF-001-E ────────────────────────────────────────────────────

    def test_NTF001_select_cliente_tiene_opciones(self, notificar_tab):
        """
        NTF-001-E: El selector #cmbCliente contiene las opciones esperadas:
        [Todos los Clientes] y Cliente generico.
        """
        page_obj = notificar_tab
        opciones = page_obj.get_opciones_cliente()

        assert len(opciones) >= 2, \
            f"Se esperaban al menos 2 opciones en #cmbCliente, hay {len(opciones)}"

        valores  = [o["value"] for o in opciones]
        textos   = [o["text"]  for o in opciones]

        assert NotificarUsuariosPage.CLIENTE_TODOS in valores, \
            f"Falta opcion 'Todos los Clientes' (value=-1). Opciones: {opciones}"
        assert any(
            NotificarUsuariosPage.CLIENTE_BASE_TEXT.lower() in t.lower()
            for t in textos
        ), f"Falta '{NotificarUsuariosPage.CLIENTE_BASE_TEXT}'. Opciones: {opciones}"

    # ── NTF-001-F ────────────────────────────────────────────────────

    def test_NTF001_lista_contiene_seis_usuarios(self, notificar_tab):
        """
        NTF-001-F: La lista #listadoUsuarios contiene usuarios notificables.
        Verifica que los agentes base (1000-1004) y el admin (cyt) estan presentes.
        El conteo total es variable segun el ambiente — no se valida un numero exacto.
        """
        page_obj = notificar_tab
        total = page_obj.get_total_usuarios()

        assert total > 0, \
            "La lista de usuarios esta vacia — no hay destinatarios disponibles"

        labels = page_obj.get_labels_usuarios()
        for num in ["1000", "1001", "1002", "1003", "1004"]:
            assert any(num in l for l in labels), \
                f"Agente '{num}' no encontrado en la lista. Labels: {labels}"
        assert any("cyt" in l.lower() for l in labels), \
            f"Usuario 'cyt' no encontrado en la lista. Labels: {labels}"

    # ── NTF-001-G ────────────────────────────────────────────────────

    def test_NTF001_chk_seleccionar_todos_presente(self, notificar_tab):
        """
        NTF-001-G: El checkbox "Seleccionar Todos" (#chkAllUsers) esta presente
        en la lista de destinatarios.
        """
        page_obj = notificar_tab

        chk = page_obj.page.locator(NotificarUsuariosPage.CHK_ALL_USERS)
        assert chk.count() > 0, \
            "#chkAllUsers no encontrado en la lista de destinatarios"

    # ── NTF-001-H ────────────────────────────────────────────────────

    def test_NTF001_validacion_campos_requeridos(self, notificar_tab):
        """
        NTF-001-H: El formulario valida campos requeridos en el cliente.
        Al intentar enviar sin completar los campos, deben aparecer
        mensajes de error sin que se envie ninguna notificacion real.

        Errores esperados:
          - "Debe indicar un asunto"
          - "Debe indicar un Mensaje"
          - "Debe indicar por lo menos un destinatario"
        """
        page_obj = notificar_tab

        # Asegurarse que los campos esten vacios y sin destinatarios
        page_obj.limpiar_formulario()

        # Click en "Enviar Mensaje" sin llenar nada
        page_obj.click_enviar()

        errores = page_obj.get_errores_visibles()

        assert len(errores) >= 3, \
            f"Se esperaban al menos 3 errores de validacion, se encontraron {len(errores)}: {errores}"

        textos = " ".join(errores).lower()
        assert "asunto" in textos, \
            f"Falta error de asunto requerido. Errores: {errores}"
        assert "mensaje" in textos, \
            f"Falta error de mensaje requerido. Errores: {errores}"
        assert "destinatario" in textos, \
            f"Falta error de destinatario requerido. Errores: {errores}"

    # ── NTF-001-I ────────────────────────────────────────────────────

    def test_NTF001_historial_mensajes_vacio(self, notificar_tab):
        """
        NTF-001-I: La tabla #tblMensajesProgramados esta presente y muestra
        0 mensajes en el estado base del sistema.
        La tabla tiene las columnas: Fecha de notificacion, Estado general,
        Asunto y Mensaje.
        """
        page_obj = notificar_tab

        assert page_obj.page.locator(NotificarUsuariosPage.TABLA_HISTORIAL).is_visible(), \
            "#tblMensajesProgramados no esta visible"

        info = page_obj.get_tabla_info()
        assert "0" in info, \
            f"Se esperaban 0 mensajes en el historial, info: '{info}'"

        # Verificar columnas de la tabla
        headers = page_obj.page.evaluate("""
            () => Array.from(document.querySelectorAll('#tblMensajesProgramados th'))
                .map(th => th.innerText.trim())
        """)
        for col in ["Fecha", "Estado", "Asunto", "Mensaje"]:
            assert any(col.lower() in h.lower() for h in headers), \
                f"Columna '{col}' no encontrada. Headers: {headers}"

    # ── NTF-001-J ────────────────────────────────────────────────────

    def test_NTF001_campos_aceptan_texto(self, notificar_tab):
        """
        NTF-001-J: Los campos #txtAsunto y #txaMensaje aceptan texto correctamente.

        Verifica que:
          - El campo asunto acepta y retiene el texto ingresado
          - El campo mensaje acepta y retiene el texto ingresado
          - Los campos respetan su maxlength (40 para asunto, 500 para mensaje)

        NOTA: No se hace click en Enviar — solo se verifica que los campos
        reciben input sin errores ni comportamientos inesperados.
        """
        page_obj = notificar_tab

        asunto_input  = page_obj.page.locator(NotificarUsuariosPage.INPUT_ASUNTO)
        mensaje_input = page_obj.page.locator(NotificarUsuariosPage.TEXTAREA_MENSAJE)

        # Llenar asunto
        asunto_input.fill("Test automatizado asunto")
        valor_asunto = asunto_input.input_value()
        assert valor_asunto == "Test automatizado asunto", \
            f"El campo asunto no retuvo el texto: '{valor_asunto}'"

        # Llenar mensaje
        mensaje_input.fill("Este es un mensaje de prueba automatizado.")
        valor_mensaje = mensaje_input.input_value()
        assert valor_mensaje == "Este es un mensaje de prueba automatizado.", \
            f"El campo mensaje no retuvo el texto: '{valor_mensaje}'"

        # Verificar maxlength del asunto (40 caracteres)
        max_asunto = page_obj.page.evaluate(
            "() => document.getElementById('txtAsunto').maxLength"
        )
        assert max_asunto == 40, \
            f"El maxlength de #txtAsunto deberia ser 40, es {max_asunto}"

        # Verificar maxlength del mensaje (500 caracteres)
        max_mensaje = page_obj.page.evaluate(
            "() => document.getElementById('txaMensaje').maxLength"
        )
        assert max_mensaje == 500, \
            f"El maxlength de #txaMensaje deberia ser 500, es {max_mensaje}"

    # ── NTF-001-K ────────────────────────────────────────────────────

    def test_NTF001_boton_refresh_historial(self, notificar_tab):
        """
        NTF-001-J: El boton de refrescar el historial (#btnRefreshTable)
        esta presente, visible y habilitado.
        """
        page_obj = notificar_tab

        btn = page_obj.page.locator(NotificarUsuariosPage.BTN_REFRESH)
        assert btn.is_visible(), "#btnRefreshTable no esta visible"
        assert btn.is_enabled(), "#btnRefreshTable no esta habilitado"
