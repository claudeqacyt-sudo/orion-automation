"""
tests/regression/anuncios/test_anuncios.py
Suite de regresion - Anuncios (/inicio)

Estructura DOM verificada:
  #carruselGestor              -> carrusel Bootstrap principal
  ol.carousel-indicators       -> 3 indicadores de posicion
  .carousel-inner .item        -> 3 slides
  .left / .right.carousel-control -> flechas de navegacion

Estado base del sistema (verificado):
  Total slides: 3
  Slide activo al cargar: indice 0 ("Bienvenido a ORION!")
  Cada slide tiene imagen de fondo
"""
import pytest
from pages.anuncios_page import AnunciosNav, AnunciosPage


# ─────────────────────────────────────────────────────────────────────────────
# Fixture de seccion
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="class")
def anuncios_tab(shared_page):
    """Abre Anuncios una sola vez para todos los tests de la clase."""
    nav = AnunciosNav(shared_page)
    tab = nav.open_anuncios()
    page_obj = AnunciosPage(tab)
    page_obj.wait_for_load()
    yield page_obj
    tab.close()


# ─────────────────────────────────────────────────────────────────────────────
# ANN-001 - Anuncios
# ─────────────────────────────────────────────────────────────────────────────

class TestAnuncios:

    # ── ANN-001-A ────────────────────────────────────────────────────

    def test_ANN001_carga_correctamente(self, anuncios_tab):
        """
        ANN-001-A: La seccion carga en la URL correcta y el carrusel es visible.
        """
        page_obj = anuncios_tab
        page_obj.verify_page_loaded()

        assert AnunciosPage.URL_PATH in page_obj.page.url, \
            f"URL incorrecta: {page_obj.page.url}"

        assert page_obj.page.locator(AnunciosPage.CARRUSEL).is_visible(), \
            "#carruselGestor no esta visible"

    # ── ANN-001-B ────────────────────────────────────────────────────

    def test_ANN001_carrusel_tiene_tres_slides(self, anuncios_tab):
        """
        ANN-001-B: El carrusel contiene exactamente 3 slides.
        """
        page_obj = anuncios_tab
        total = page_obj.get_total_slides()

        assert total == AnunciosPage.TOTAL_SLIDES, \
            f"Se esperaban {AnunciosPage.TOTAL_SLIDES} slides, se encontraron {total}"

    # ── ANN-001-C ────────────────────────────────────────────────────

    def test_ANN001_primer_slide_activo_al_cargar(self, anuncios_tab):
        """
        ANN-001-C: Al cargar la pagina, el primer slide (indice 0) esta activo.
        """
        page_obj = anuncios_tab
        indice = page_obj.get_indice_slide_activo()

        assert indice == 0, \
            f"Se esperaba el slide 0 activo al cargar, esta activo el slide {indice}"

    # ── ANN-001-D ────────────────────────────────────────────────────

    def test_ANN001_slides_tienen_titulos_correctos(self, anuncios_tab):
        """
        ANN-001-D: Los 3 slides tienen los titulos esperados del sistema.
        """
        page_obj = anuncios_tab
        titulos = page_obj.get_titulos_slides()

        assert len(titulos) == AnunciosPage.TOTAL_SLIDES, \
            f"Se esperaban {AnunciosPage.TOTAL_SLIDES} titulos, se encontraron {len(titulos)}: {titulos}"

        for texto_esperado in AnunciosPage.TITULOS_SLIDES:
            assert any(texto_esperado.lower() in t.lower() for t in titulos), \
                f"Titulo '{texto_esperado}' no encontrado. Titulos actuales: {titulos}"

    # ── ANN-001-E ────────────────────────────────────────────────────

    def test_ANN001_controles_navegacion_presentes(self, anuncios_tab):
        """
        ANN-001-E: Los botones de navegacion anterior y siguiente estan presentes.
        """
        page_obj = anuncios_tab

        assert page_obj.page.locator(AnunciosPage.BTN_PREV).is_visible(), \
            "El control 'anterior' (.left.carousel-control) no esta visible"
        assert page_obj.page.locator(AnunciosPage.BTN_NEXT).is_visible(), \
            "El control 'siguiente' (.right.carousel-control) no esta visible"

    # ── ANN-001-F ────────────────────────────────────────────────────

    def test_ANN001_indicadores_presentes(self, anuncios_tab):
        """
        ANN-001-F: Los indicadores del carrusel (puntos de posicion) son 3,
        uno por cada slide.
        """
        page_obj = anuncios_tab
        total = page_obj.get_total_indicadores()

        assert total == AnunciosPage.TOTAL_SLIDES, \
            f"Se esperaban {AnunciosPage.TOTAL_SLIDES} indicadores, se encontraron {total}"

    # ── ANN-001-G ────────────────────────────────────────────────────

    def test_ANN001_slide_activo_tiene_imagen(self, anuncios_tab):
        """
        ANN-001-G: El slide activo tiene una imagen de fondo cargada.
        """
        page_obj = anuncios_tab

        assert page_obj.slide_activo_tiene_imagen(), \
            "El slide activo no tiene imagen"
