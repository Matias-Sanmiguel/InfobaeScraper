import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By

URL_BASE = "https://www.infobae.com"
PATRON_ARTICULO = re.compile(
    r"https://www\.infobae\.com/[^/]+/[^/]+/\d{4}/\d{2}/\d{2}/[^/]+/"
)


def obtener_urls_seccion(
    driver: webdriver.Chrome,
    seccion: str,
    max_articulos: int = 50,
    delay_scroll: float = 2.0,
) -> list[str]:
    url_seccion = f"{URL_BASE}{seccion}" if seccion.startswith("/") else f"{URL_BASE}/{seccion}"
    driver.get(url_seccion)
    time.sleep(3)

    urls_encontradas: set[str] = set()

    while len(urls_encontradas) < max_articulos:
        enlaces = driver.find_elements(By.TAG_NAME, "a")
        for enlace in enlaces:
            href = enlace.get_attribute("href") or ""
            if PATRON_ARTICULO.match(href):
                urls_encontradas.add(href)

        if len(urls_encontradas) >= max_articulos:
            break

        altura_anterior = driver.execute_script("return document.body.scrollHeight")
        time.sleep(delay_scroll)
        altura_nueva = driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight); return document.body.scrollHeight"
        )

        if altura_nueva == altura_anterior:
            break

    return list(urls_encontradas)[:max_articulos]
