"""
tests/regression/supervision/test_notificar_usuarios.py
Suite de regresion — Supervision > Notificar Usuarios (/MensajesUsuarios)

SKIP PERMANENTE: /MensajesUsuarios cuelga en Playwright headed mode.
  - evaluate().click() en accionEjecutar_41: expect_page() nunca recibe la nueva pestana
  - locator().click() en accionEjecutar_41: wait_for_load_state("domcontentloaded") cuelga
La pagina abre correctamente de forma manual. Incompatibilidad con Playwright headed.
"""
import pytest

pytestmark = [pytest.mark.regression, pytest.mark.admin,
              pytest.mark.skip(reason="NTF: /MensajesUsuarios incompatible con Playwright "
                                      "headed mode — abre ok manualmente")]


class TestNotificarUsuarios:

    def test_NTF001_A_carga_correctamente(self):
        pass

    def test_NTF001_B_formulario_presente(self):
        pass

    def test_NTF001_C_radio_ahora_activo_por_defecto(self):
        pass

    def test_NTF001_D_otro_momento_muestra_fecha(self):
        pass

    def test_NTF001_E_select_cliente_tiene_opciones(self):
        pass

    def test_NTF001_F_lista_usuarios_tiene_destinatarios(self):
        pass

    def test_NTF001_G_tabla_historial_presente(self):
        pass

    def test_NTF001_H_campos_aceptan_texto(self):
        pass

    def test_NTF001_I_boton_refresh_historial_presente(self):
        pass
