import argparse
import sys
from urllib.parse import urlparse

from salida.escritor_csv import EscritorCSV
from scraper.crawleador_seccion import obtener_urls_seccion
from scraper.driver import crear_driver
from scraper.parseador_articulo import parsear_articulo


def _validar_url_infobae(url: str):
    dominio = urlparse(url).netloc
    if dominio not in ("www.infobae.com", "infobae.com"):
        raise ValueError(f"URL no pertenece a Infobae: {dominio}")


def procesar_url(url: str, escritor: EscritorCSV, delay: float):
    resultado = parsear_articulo(url, delay=delay)
    escritor.guardar(resultado)
    print(f"OK: {resultado.noticia.titulo[:60]}")


def modo_url(url: str, directorio_salida: str, delay: float):
    _validar_url_infobae(url)
    escritor = EscritorCSV(directorio_salida)
    procesar_url(url, escritor, delay)


def modo_seccion(seccion: str, max_articulos: int, directorio_salida: str, delay: float):
    driver = crear_driver()
    escritor = EscritorCSV(directorio_salida)
    try:
        urls = obtener_urls_seccion(driver, seccion, max_articulos)
        print(f"Encontradas {len(urls)} URLs en {seccion}")
        for url in urls:
            try:
                procesar_url(url, escritor, delay)
            except Exception as error:
                print(f"ERROR {url}: {error}", file=sys.stderr)
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(description="Scraper de Infobae para investigación de fake news")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--url", type=str, help="URL de un artículo individual")
    grupo.add_argument("--seccion", type=str, help="Sección a crawlear (ej: /america/mundo/)")
    parser.add_argument("--max", type=int, default=50, help="Máximo de artículos en modo sección")
    parser.add_argument("--salida", type=str, default="datos", help="Directorio de salida para CSVs")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay entre requests en segundos")
    args = parser.parse_args()

    if args.url:
        modo_url(args.url, args.salida, args.delay)
    else:
        modo_seccion(args.seccion, args.max, args.salida, args.delay)


if __name__ == "__main__":
    main()
