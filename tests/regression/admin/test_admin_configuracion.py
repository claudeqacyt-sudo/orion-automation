"""
tests/regression/admin/test_admin_configuracion.py
Suite de regresión — Admin: secciones del menú Configuración

ADM-009: Cada sección hoja abre nueva pestaña, carga sin errores
         y sus botones/controles responden. Accedido como admin (cyt).
"""
import time
import pytest

from tests.regression.frameworks.test_gestion_usuarios import TestSupervisorAcceso as _FRW

pytestmark = [pytest.mark.regression, pytest.mark.admin]

# Secciones del menú Configuración (id_hoja, descripción, abuelo, padre, url_path)
_SECCIONES = _FRW.SECCIONES_HOJA_NAV

# Mapa de verificadores por sección (métodos estáticos del FRW — no duplicar código)
_VERIFICADORES = {
    "accionEjecutar_213": _FRW._verificar_vinculos,
    "accionEjecutar_221": _FRW._verificar_respuestas_rapidas,
    "accionEjecutar_262": _FRW._verificar_ver_importaciones,
    "accionEjecutar_271": _FRW._verificar_tipos_tickets,
    "accionEjecutar_281": _FRW._verificar_busquedas_automaticas,
    "accionEjecutar_5":   _FRW._verificar_ayuda,
}


def _preparar_menu(page, abuelo, padre, hoja_id) -> bool:
    """Expande el menú accordion para que hoja_id sea clickeable."""
    if abuelo is None:
        return True
    page.evaluate(f"() => document.getElementById('{abuelo}')?.click()")
    time.sleep(1.2)
    if padre:
        page.evaluate(f"() => document.getElementById('{padre}')?.click()")
        time.sleep(1.2)
    return page.evaluate(f"""
        () => {{
            const el = document.getElementById('{hoja_id}');
            if (!el) return false;
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
        }}
    """)


class TestAdminConfiguracion:

    def test_ADM009_secciones_configuracion_abren_contenido(self, shared_page):
        """
        ADM-009: Como admin, cada sección hoja de Configuración abre nueva pestaña
        en la URL correcta, sin errores de servidor, y sus controles responden.
        """
        page = shared_page

        for hoja_id, descripcion, abuelo, padre, url_esperada in _SECCIONES:

            hoja_lista = _preparar_menu(page, abuelo, padre, hoja_id)
            assert hoja_lista, (
                f"'{descripcion}' (#{hoja_id}) no es visible en el menú "
                f"después de expandir los padres"
            )

            try:
                with page.context.expect_page(timeout=10000) as nueva_pag_info:
                    page.locator(f"#{hoja_id}").click()
                nueva_pag = nueva_pag_info.value
            except Exception as e:
                pytest.fail(
                    f"'{descripcion}' (#{hoja_id}) no abrió nueva pestaña. "
                    f"Error: {type(e).__name__}"
                )

            try:
                _FRW._esperar_pagina_lista(nueva_pag, url_esperada)
                nueva_pag.bring_to_front()

                assert url_esperada in nueva_pag.url, (
                    f"'{descripcion}': URL inesperada. "
                    f"Esperaba '{url_esperada}', obtuvo '{nueva_pag.url}'"
                )

                assert not _FRW._tiene_error_servidor(nueva_pag), (
                    f"'{descripcion}' mostró error del servidor en '{nueva_pag.url}'"
                )

                verificar = _VERIFICADORES.get(hoja_id)
                if verificar:
                    verificar(nueva_pag)

                time.sleep(2)

            finally:
                nueva_pag.close()
