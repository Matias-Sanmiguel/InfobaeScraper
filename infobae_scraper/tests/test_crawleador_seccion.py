from unittest.mock import MagicMock, call
from scraper.crawleador_seccion import obtener_urls_seccion


def _hacer_enlace(href: str) -> MagicMock:
    enlace = MagicMock()
    enlace.get_attribute.return_value = href
    return enlace


def test_filtra_urls_que_no_son_articulos():
    driver = MagicMock()
    driver.find_elements.return_value = [
        _hacer_enlace("https://www.infobae.com/america/mundo/2026/06/20/nota-uno/"),
        _hacer_enlace("https://www.infobae.com/suscripciones/"),
        _hacer_enlace("https://www.infobae.com/america/mundo/2026/06/19/nota-dos/"),
    ]
    driver.execute_script.side_effect = [500, None, 500]

    urls = obtener_urls_seccion(driver, "/america/mundo/", max_articulos=10, delay_scroll=0)

    assert "https://www.infobae.com/america/mundo/2026/06/20/nota-uno/" in urls
    assert "https://www.infobae.com/america/mundo/2026/06/19/nota-dos/" in urls
    assert "https://www.infobae.com/suscripciones/" not in urls


def test_respeta_maximo_de_articulos():
    urls_validas = [
        f"https://www.infobae.com/america/mundo/2026/06/20/nota-{i}/"
        for i in range(20)
    ]
    driver = MagicMock()
    driver.find_elements.return_value = [_hacer_enlace(u) for u in urls_validas]
    driver.execute_script.side_effect = [500, None, 500]

    urls = obtener_urls_seccion(driver, "/america/mundo/", max_articulos=5, delay_scroll=0)

    assert len(urls) <= 5


def test_para_cuando_altura_no_cambia():
    driver = MagicMock()
    driver.find_elements.return_value = [
        _hacer_enlace("https://www.infobae.com/america/mundo/2026/06/20/nota-a/"),
    ]
    driver.execute_script.side_effect = [300, None, 300]

    urls = obtener_urls_seccion(driver, "/america/mundo/", max_articulos=100, delay_scroll=0)

    assert driver.execute_script.call_count == 3


def test_construye_url_con_barra_inicial():
    driver = MagicMock()
    driver.find_elements.return_value = []
    driver.execute_script.side_effect = [0, None, 0]

    obtener_urls_seccion(driver, "/america/mundo/", max_articulos=1, delay_scroll=0)

    driver.get.assert_called_once_with("https://www.infobae.com/america/mundo/")
