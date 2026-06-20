import re
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from modelos.esquema import Autor, Noticia, ResultadoArticulo, Tema, Verificacion, generar_id

VERBOS_DECLARACION = {
    "dijo", "afirmó", "señaló", "indicó", "según", "sostuvo",
    "declaró", "aseguró", "manifestó", "informó", "expresó",
}

CABECERAS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
}


def extraer_seccion(url: str) -> str:
    segmentos = urlparse(url).path.strip("/").split("/")
    resultado = []
    for seg in segmentos:
        if re.fullmatch(r'\d{4}', seg):
            break
        resultado.append(seg)
    return "/".join(resultado[:2]) if len(resultado) >= 2 else resultado[0] if resultado else ""


def extraer_meta(soup: BeautifulSoup, propiedad: str) -> str:
    etiqueta = soup.find("meta", property=propiedad) or soup.find(
        "meta", attrs={"name": propiedad}
    )
    return etiqueta.get("content", "") if etiqueta else ""


def extraer_cuerpo(soup: BeautifulSoup) -> str:
    contenedor = (
        soup.find("div", class_="article-body")
        or soup.find("div", class_="body-article")
        or soup.find("article")
        or soup.find("div", attrs={"data-type": "article-body"})
    )
    if not contenedor:
        return ""
    for tag in contenedor.find_all(["script", "style", "figure", "aside"]):
        tag.decompose()
    return contenedor.get_text(separator=" ").strip()


def extraer_autores(soup: BeautifulSoup) -> list[str]:
    etiquetas = soup.find_all("a", class_="author-name") or soup.find_all(
        "span", class_="author-name"
    )
    if etiquetas:
        return [e.get_text(strip=True) for e in etiquetas if e.get_text(strip=True)]
    meta = extraer_meta(soup, "article:author")
    return [meta] if meta else []


def extraer_temas(soup: BeautifulSoup) -> list[str]:
    etiquetas = soup.find_all("a", class_="tag") or soup.find_all(
        "a", attrs={"data-type": "tag"}
    )
    if etiquetas:
        return [e.get_text(strip=True) for e in etiquetas if e.get_text(strip=True)]
    meta = extraer_meta(soup, "keywords")
    return [k.strip() for k in meta.split(",") if k.strip()] if meta else []


def clasificar_oracion(oracion: str) -> tuple[str, str]:
    tiene_comillas = any(c in oracion for c in ('"', "“", "”"))
    palabras = set(oracion.lower().split())
    tiene_verbo = bool(palabras & VERBOS_DECLARACION)
    tiene_estadistica = bool(
        re.search(r"\d+[\.,]?\d*\s*(%|millones?|miles?|mil\b)", oracion, re.IGNORECASE)
    )
    if tiene_comillas or tiene_verbo:
        fuente = ""
        coincidencia = re.search(
            r"según\s+([\w\s]+?)(?:[,.]|$)", oracion, re.IGNORECASE
        )
        if coincidencia:
            fuente = coincidencia.group(1).strip()
        return "cita", fuente
    if tiene_estadistica:
        return "estadistica", ""
    return "sin_clasificar", ""


def extraer_verificaciones(cuerpo: str) -> list[Verificacion]:
    if not cuerpo:
        return []
    oraciones = re.split(r"(?<=[.!?])\s+", cuerpo)
    verificaciones = []
    for oracion in oraciones:
        oracion = oracion.strip()
        if len(oracion) < 30:
            continue
        tipo, fuente = clasificar_oracion(oracion)
        verificaciones.append(
            Verificacion(
                verificacion_id=generar_id(oracion),
                texto=oracion,
                tipo=tipo,
                verificado=False,
                fuente_citada=fuente,
            )
        )
    return verificaciones


def parsear_articulo(url: str, delay: float = 2.0) -> ResultadoArticulo:
    time.sleep(delay)
    respuesta = requests.get(url, headers=CABECERAS, timeout=15)
    respuesta.raise_for_status()
    soup = BeautifulSoup(respuesta.text, "lxml")

    h1 = soup.find("h1")
    titulo = extraer_meta(soup, "og:title") or (h1.get_text(strip=True) if h1 else "")

    noticia_id = generar_id(url)
    noticia = Noticia(
        noticia_id=noticia_id,
        url=url,
        titulo=titulo,
        cuerpo=extraer_cuerpo(soup),
        fecha_publicacion=extraer_meta(soup, "article:published_time"),
        fecha_modificacion=extraer_meta(soup, "article:modified_time"),
        seccion=extraer_seccion(url),
        imagen_portada=extraer_meta(soup, "og:image"),
    )

    autores = [
        Autor(autor_id=generar_id(nombre), nombre=nombre)
        for nombre in extraer_autores(soup)
    ]
    temas = [
        Tema(tema_id=generar_id(nombre), nombre=nombre)
        for nombre in extraer_temas(soup)
    ]
    verificaciones = extraer_verificaciones(noticia.cuerpo)

    return ResultadoArticulo(
        noticia=noticia,
        autores=autores,
        temas=temas,
        verificaciones=verificaciones,
    )
