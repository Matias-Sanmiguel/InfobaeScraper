# Infobae Scraper — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scraper de artículos de Infobae que produce múltiples CSVs compatibles con Neo4j para investigación de fake news.

**Architecture:** Selenium descubre URLs de secciones con scroll infinito. `requests` + BeautifulSoup4 parsea el HTML de cada artículo individualmente. Un escritor CSV appenda nodos y relaciones a 9 archivos separados, listos para `neo4j-admin import`.

**Tech Stack:** Python 3.11+, Selenium 4, webdriver-manager, requests, beautifulsoup4, lxml, pytest, pytest-mock

## Global Constraints

- Solo Infobae como fuente (URL base hardcodeada: `https://www.infobae.com`)
- Código en español: nombres de variables, funciones, clases, archivos
- Sin comentarios en el código
- `delay` mínimo 2.0s entre requests a artículos
- No crawl recursivo: sección → lista plana de URLs de artículos
- Python 3.11+

---

## Estructura de archivos

```
infobae_scraper/
├── modelos/
│   ├── __init__.py
│   └── esquema.py
├── scraper/
│   ├── __init__.py
│   ├── driver.py
│   ├── crawleador_seccion.py
│   └── parseador_articulo.py
├── salida/
│   ├── __init__.py
│   └── escritor_csv.py
├── tests/
│   ├── __init__.py
│   ├── test_esquema.py
│   ├── test_escritor_csv.py
│   ├── test_parseador_articulo.py
│   └── test_crawleador_seccion.py
├── main.py
└── requirements.txt
```

**Responsabilidades:**
- `modelos/esquema.py` — dataclasses + función `generar_id`
- `scraper/driver.py` — construye Chrome headless
- `scraper/crawleador_seccion.py` — Selenium: lista URLs de una sección
- `scraper/parseador_articulo.py` — requests + BS4 + extracción de verificaciones
- `salida/escritor_csv.py` — appenda filas a los 9 CSVs
- `main.py` — CLI con argparse

---

### Tarea 1: Setup del proyecto

**Archivos:**
- Crear: `infobae_scraper/requirements.txt`
- Crear: `infobae_scraper/modelos/__init__.py`
- Crear: `infobae_scraper/scraper/__init__.py`
- Crear: `infobae_scraper/salida/__init__.py`
- Crear: `infobae_scraper/tests/__init__.py`

**Interfaces:** ninguna

- [ ] **Paso 1: Crear estructura de directorios**

```bash
mkdir -p infobae_scraper/{modelos,scraper,salida,tests}
touch infobae_scraper/modelos/__init__.py
touch infobae_scraper/scraper/__init__.py
touch infobae_scraper/salida/__init__.py
touch infobae_scraper/tests/__init__.py
```

- [ ] **Paso 2: Crear requirements.txt**

Contenido de `infobae_scraper/requirements.txt`:
```
selenium==4.21.0
webdriver-manager==4.0.1
requests==2.32.3
beautifulsoup4==4.12.3
lxml==5.2.2
pytest==8.2.2
pytest-mock==3.14.0
```

- [ ] **Paso 3: Instalar dependencias**

```bash
cd infobae_scraper
pip install -r requirements.txt
```

Resultado esperado: instalación sin errores.

- [ ] **Paso 4: Verificar imports básicos**

```bash
python -c "import selenium; import requests; import bs4; print('OK')"
```

Resultado esperado: `OK`

- [ ] **Paso 5: Commit**

```bash
cd infobae_scraper
git init
git add .
git commit -m "chore: setup inicial del proyecto scraper"
```

---

### Tarea 2: Modelos de datos (`modelos/esquema.py`)

**Archivos:**
- Crear: `infobae_scraper/modelos/esquema.py`
- Test: `infobae_scraper/tests/test_esquema.py`

**Interfaces:**
- Produce:
  - `generar_id(texto: str) -> str` — SHA256 hex truncado a 16 chars
  - `Noticia(noticia_id, url, titulo, cuerpo, fecha_publicacion, fecha_modificacion, seccion, imagen_portada)`
  - `Autor(autor_id, nombre)`
  - `Tema(tema_id, nombre)`
  - `Verificacion(verificacion_id, texto, tipo, verificado: bool, fuente_citada)`
  - `ResultadoArticulo(noticia: Noticia, autores: list[Autor], temas: list[Tema], verificaciones: list[Verificacion])`

- [ ] **Paso 1: Escribir tests que fallan**

`infobae_scraper/tests/test_esquema.py`:
```python
from modelos.esquema import generar_id, Noticia, Autor, Tema, Verificacion, ResultadoArticulo


def test_generar_id_es_determinista():
    assert generar_id("https://infobae.com/nota") == generar_id("https://infobae.com/nota")


def test_generar_id_longitud_16():
    assert len(generar_id("cualquier texto")) == 16


def test_generar_id_distintos_inputs_distintos_ids():
    assert generar_id("a") != generar_id("b")


def test_noticia_se_crea_con_campos():
    n = Noticia(
        noticia_id="abc123",
        url="https://infobae.com/nota",
        titulo="Título",
        cuerpo="Texto del artículo",
        fecha_publicacion="2026-06-20T10:00:00",
        fecha_modificacion="2026-06-20T11:00:00",
        seccion="america/mundo",
        imagen_portada="https://img.infobae.com/foto.jpg",
    )
    assert n.titulo == "Título"
    assert n.seccion == "america/mundo"


def test_verificacion_verificado_false_por_defecto_no_aplica():
    v = Verificacion(
        verificacion_id="vid",
        texto="El 80% del petróleo pasa por ahí.",
        tipo="estadistica",
        verificado=False,
        fuente_citada="",
    )
    assert v.verificado is False
    assert v.tipo == "estadistica"


def test_resultado_articulo_agrupa_componentes():
    noticia = Noticia("id", "url", "titulo", "cuerpo", "fp", "fm", "sec", "img")
    autor = Autor(autor_id="aid", nombre="Juan Pérez")
    tema = Tema(tema_id="tid", nombre="Irán")
    ver = Verificacion("vid", "texto", "cita", False, "Reuters")
    r = ResultadoArticulo(noticia=noticia, autores=[autor], temas=[tema], verificaciones=[ver])
    assert r.noticia.titulo == "titulo"
    assert len(r.autores) == 1
    assert r.temas[0].nombre == "Irán"
```

- [ ] **Paso 2: Ejecutar tests y verificar que fallan**

```bash
cd infobae_scraper
pytest tests/test_esquema.py -v
```

Resultado esperado: `ModuleNotFoundError: No module named 'modelos.esquema'`

- [ ] **Paso 3: Implementar `modelos/esquema.py`**

```python
import hashlib
from dataclasses import dataclass


def generar_id(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()[:16]


@dataclass
class Noticia:
    noticia_id: str
    url: str
    titulo: str
    cuerpo: str
    fecha_publicacion: str
    fecha_modificacion: str
    seccion: str
    imagen_portada: str


@dataclass
class Autor:
    autor_id: str
    nombre: str


@dataclass
class Tema:
    tema_id: str
    nombre: str


@dataclass
class Verificacion:
    verificacion_id: str
    texto: str
    tipo: str
    verificado: bool
    fuente_citada: str


@dataclass
class ResultadoArticulo:
    noticia: Noticia
    autores: list[Autor]
    temas: list[Tema]
    verificaciones: list[Verificacion]
```

- [ ] **Paso 4: Ejecutar tests y verificar que pasan**

```bash
pytest tests/test_esquema.py -v
```

Resultado esperado: 6 tests PASSED

- [ ] **Paso 5: Commit**

```bash
git add modelos/esquema.py tests/test_esquema.py
git commit -m "feat: modelos de datos (Noticia, Autor, Tema, Verificacion)"
```

---

### Tarea 3: Escritor CSV (`salida/escritor_csv.py`)

**Archivos:**
- Crear: `infobae_scraper/salida/escritor_csv.py`
- Test: `infobae_scraper/tests/test_escritor_csv.py`

**Interfaces:**
- Consume: `ResultadoArticulo`, `Noticia`, `Autor`, `Tema`, `Verificacion` de `modelos.esquema`
- Produce: `EscritorCSV(directorio_salida: str)` con método `guardar(resultado: ResultadoArticulo) -> None`

Los 9 archivos CSV generados:
- `noticias.csv`, `medios.csv`, `temas.csv`, `autores.csv`, `verificaciones.csv`
- `rel_publica.csv`, `rel_menciona.csv`, `rel_escrito_por.csv`, `rel_verifica.csv`

- [ ] **Paso 1: Escribir tests que fallan**

`infobae_scraper/tests/test_escritor_csv.py`:
```python
import csv
from pathlib import Path
from modelos.esquema import Noticia, Autor, Tema, Verificacion, ResultadoArticulo
from salida.escritor_csv import EscritorCSV


def _resultado_muestra() -> ResultadoArticulo:
    noticia = Noticia(
        noticia_id="abc123",
        url="https://www.infobae.com/america/mundo/2026/06/20/nota/",
        titulo="Título de prueba",
        cuerpo="El texto del cuerpo.",
        fecha_publicacion="2026-06-20T10:00:00",
        fecha_modificacion="2026-06-20T11:00:00",
        seccion="america/mundo",
        imagen_portada="https://img.infobae.com/foto.jpg",
    )
    return ResultadoArticulo(
        noticia=noticia,
        autores=[Autor(autor_id="au1", nombre="Juan Pérez")],
        temas=[Tema(tema_id="te1", nombre="Irán")],
        verificaciones=[
            Verificacion(verificacion_id="ve1", texto="El 80% pasa por ahí.", tipo="estadistica", verificado=False, fuente_citada="")
        ],
    )


def test_crea_archivos_csv(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    archivos = [f.name for f in tmp_path.iterdir()]
    assert "noticias.csv" in archivos
    assert "medios.csv" in archivos
    assert "temas.csv" in archivos
    assert "autores.csv" in archivos
    assert "verificaciones.csv" in archivos
    assert "rel_publica.csv" in archivos
    assert "rel_menciona.csv" in archivos
    assert "rel_escrito_por.csv" in archivos
    assert "rel_verifica.csv" in archivos


def test_noticias_csv_contiene_datos(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    filas = list(csv.DictReader(open(tmp_path / "noticias.csv", encoding="utf-8")))
    assert len(filas) == 1
    assert filas[0]["noticia_id"] == "abc123"
    assert filas[0]["titulo"] == "Título de prueba"


def test_medios_csv_contiene_infobae(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    filas = list(csv.DictReader(open(tmp_path / "medios.csv", encoding="utf-8")))
    assert any(f["nombre"] == "Infobae" for f in filas)


def test_rel_publica_vincula_medio_a_noticia(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    filas = list(csv.DictReader(open(tmp_path / "rel_publica.csv", encoding="utf-8")))
    assert filas[0]["medio_id"] == "infobae"
    assert filas[0]["noticia_id"] == "abc123"


def test_temas_y_relacion_menciona(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    temas = list(csv.DictReader(open(tmp_path / "temas.csv", encoding="utf-8")))
    menciona = list(csv.DictReader(open(tmp_path / "rel_menciona.csv", encoding="utf-8")))
    assert temas[0]["nombre"] == "Irán"
    assert menciona[0]["noticia_id"] == "abc123"
    assert menciona[0]["tema_id"] == "te1"


def test_verificaciones_y_relacion_verifica(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    vers = list(csv.DictReader(open(tmp_path / "verificaciones.csv", encoding="utf-8")))
    verifica = list(csv.DictReader(open(tmp_path / "rel_verifica.csv", encoding="utf-8")))
    assert vers[0]["tipo"] == "estadistica"
    assert verifica[0]["verificacion_id"] == "ve1"
    assert verifica[0]["noticia_id"] == "abc123"


def test_guardar_dos_veces_appenda_filas(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    resultado2 = _resultado_muestra()
    resultado2.noticia.noticia_id = "def456"
    escritor.guardar(resultado2)
    filas = list(csv.DictReader(open(tmp_path / "noticias.csv", encoding="utf-8")))
    assert len(filas) == 2
```

- [ ] **Paso 2: Ejecutar tests y verificar que fallan**

```bash
pytest tests/test_escritor_csv.py -v
```

Resultado esperado: `ModuleNotFoundError: No module named 'salida.escritor_csv'`

- [ ] **Paso 3: Implementar `salida/escritor_csv.py`**

```python
import csv
from pathlib import Path
from dataclasses import asdict

from modelos.esquema import ResultadoArticulo, Noticia, Autor, Tema, Verificacion

MEDIO_ID = "infobae"
MEDIO_NOMBRE = "Infobae"


class EscritorCSV:
    def __init__(self, directorio_salida: str = "salida"):
        self.directorio = Path(directorio_salida)
        self.directorio.mkdir(parents=True, exist_ok=True)
        self._inicializar_medios()

    def _ruta(self, nombre: str) -> Path:
        return self.directorio / nombre

    def _es_nuevo(self, nombre: str) -> bool:
        return not self._ruta(nombre).exists()

    def _abrir_csv(self, nombre: str, campos: list[str]):
        nuevo = self._es_nuevo(nombre)
        archivo = open(self._ruta(nombre), "a", newline="", encoding="utf-8")
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        if nuevo:
            escritor.writeheader()
        return archivo, escritor

    def _inicializar_medios(self):
        if self._es_nuevo("medios.csv"):
            archivo, escritor = self._abrir_csv("medios.csv", ["medio_id", "nombre"])
            escritor.writerow({"medio_id": MEDIO_ID, "nombre": MEDIO_NOMBRE})
            archivo.close()

    def guardar(self, resultado: ResultadoArticulo):
        self._guardar_noticia(resultado.noticia)
        self._guardar_rel_publica(resultado.noticia.noticia_id)
        for autor in resultado.autores:
            self._guardar_autor(autor, resultado.noticia.noticia_id)
        for tema in resultado.temas:
            self._guardar_tema(tema, resultado.noticia.noticia_id)
        for verificacion in resultado.verificaciones:
            self._guardar_verificacion(verificacion, resultado.noticia.noticia_id)

    def _guardar_noticia(self, noticia: Noticia):
        campos = ["noticia_id", "url", "titulo", "cuerpo", "fecha_publicacion",
                  "fecha_modificacion", "seccion", "imagen_portada"]
        archivo, escritor = self._abrir_csv("noticias.csv", campos)
        escritor.writerow(asdict(noticia))
        archivo.close()

    def _guardar_rel_publica(self, noticia_id: str):
        archivo, escritor = self._abrir_csv("rel_publica.csv", ["medio_id", "noticia_id"])
        escritor.writerow({"medio_id": MEDIO_ID, "noticia_id": noticia_id})
        archivo.close()

    def _guardar_autor(self, autor: Autor, noticia_id: str):
        archivo, escritor = self._abrir_csv("autores.csv", ["autor_id", "nombre"])
        escritor.writerow(asdict(autor))
        archivo.close()
        archivo, escritor = self._abrir_csv("rel_escrito_por.csv", ["noticia_id", "autor_id"])
        escritor.writerow({"noticia_id": noticia_id, "autor_id": autor.autor_id})
        archivo.close()

    def _guardar_tema(self, tema: Tema, noticia_id: str):
        archivo, escritor = self._abrir_csv("temas.csv", ["tema_id", "nombre"])
        escritor.writerow(asdict(tema))
        archivo.close()
        archivo, escritor = self._abrir_csv("rel_menciona.csv", ["noticia_id", "tema_id"])
        escritor.writerow({"noticia_id": noticia_id, "tema_id": tema.tema_id})
        archivo.close()

    def _guardar_verificacion(self, verificacion: Verificacion, noticia_id: str):
        campos = ["verificacion_id", "texto", "tipo", "verificado", "fuente_citada"]
        archivo, escritor = self._abrir_csv("verificaciones.csv", campos)
        escritor.writerow(asdict(verificacion))
        archivo.close()
        archivo, escritor = self._abrir_csv("rel_verifica.csv", ["verificacion_id", "noticia_id"])
        escritor.writerow({"verificacion_id": verificacion.verificacion_id, "noticia_id": noticia_id})
        archivo.close()
```

- [ ] **Paso 4: Ejecutar tests y verificar que pasan**

```bash
pytest tests/test_escritor_csv.py -v
```

Resultado esperado: 7 tests PASSED

- [ ] **Paso 5: Commit**

```bash
git add salida/escritor_csv.py tests/test_escritor_csv.py
git commit -m "feat: escritor de CSVs compatible con Neo4j import"
```

---

### Tarea 4: Parseador de artículos (`scraper/parseador_articulo.py`)

**Archivos:**
- Crear: `infobae_scraper/scraper/parseador_articulo.py`
- Test: `infobae_scraper/tests/test_parseador_articulo.py`

**Interfaces:**
- Consume: `modelos.esquema` (todos los dataclasses + `generar_id`)
- Produce:
  - `extraer_seccion(url: str) -> str`
  - `extraer_meta(soup: BeautifulSoup, propiedad: str) -> str`
  - `extraer_cuerpo(soup: BeautifulSoup) -> str`
  - `extraer_autores(soup: BeautifulSoup) -> list[str]`
  - `extraer_temas(soup: BeautifulSoup) -> list[str]`
  - `clasificar_oracion(oracion: str) -> tuple[str, str]` — retorna `(tipo, fuente_citada)`
  - `extraer_verificaciones(cuerpo: str) -> list[Verificacion]`
  - `parsear_articulo(url: str, delay: float = 2.0) -> ResultadoArticulo`

- [ ] **Paso 1: Escribir tests que fallan**

`infobae_scraper/tests/test_parseador_articulo.py`:
```python
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from scraper.parseador_articulo import (
    extraer_seccion,
    extraer_meta,
    extraer_cuerpo,
    extraer_autores,
    extraer_temas,
    clasificar_oracion,
    extraer_verificaciones,
    parsear_articulo,
)

HTML_MUESTRA = """
<html>
<head>
  <meta property="og:title" content="Título de prueba" />
  <meta property="og:image" content="https://img.infobae.com/foto.jpg" />
  <meta property="article:published_time" content="2026-06-20T10:00:00-03:00" />
  <meta property="article:modified_time" content="2026-06-20T11:00:00-03:00" />
  <meta property="article:author" content="Juan Pérez" />
</head>
<body>
  <div class="article-body">
    El régimen de Irán anunció el cierre del estrecho de Ormuz.
    "Cerraremos el estrecho", dijo el portavoz según Reuters.
    El 80% del petróleo del Golfo pasa por ese punto.
  </div>
  <a class="tag">Irán</a>
  <a class="tag">Estrecho de Ormuz</a>
  <a class="author-name">Juan Pérez</a>
</body>
</html>
"""


def _soup() -> BeautifulSoup:
    return BeautifulSoup(HTML_MUESTRA, "lxml")


def test_extraer_seccion_dos_segmentos():
    url = "https://www.infobae.com/america/mundo/2026/06/20/nota/"
    assert extraer_seccion(url) == "america/mundo"


def test_extraer_seccion_un_segmento():
    url = "https://www.infobae.com/economia/2026/06/20/nota/"
    assert extraer_seccion(url) == "economia/2026"


def test_extraer_meta_og_title():
    soup = _soup()
    assert extraer_meta(soup, "og:title") == "Título de prueba"


def test_extraer_meta_faltante_retorna_string_vacio():
    soup = _soup()
    assert extraer_meta(soup, "og:nonexistent") == ""


def test_extraer_cuerpo_devuelve_texto():
    soup = _soup()
    cuerpo = extraer_cuerpo(soup)
    assert "Irán" in cuerpo
    assert len(cuerpo) > 10


def test_extraer_autores_desde_clase():
    soup = _soup()
    autores = extraer_autores(soup)
    assert "Juan Pérez" in autores


def test_extraer_temas_desde_clase_tag():
    soup = _soup()
    temas = extraer_temas(soup)
    assert "Irán" in temas
    assert "Estrecho de Ormuz" in temas


def test_clasificar_oracion_cita_con_dijo():
    tipo, fuente = clasificar_oracion('"Cerraremos el estrecho", dijo el portavoz.')
    assert tipo == "cita"


def test_clasificar_oracion_estadistica():
    tipo, fuente = clasificar_oracion("El 80% del petróleo del Golfo pasa por ese punto.")
    assert tipo == "estadistica"


def test_clasificar_oracion_segun_extrae_fuente():
    tipo, fuente = clasificar_oracion("El cierre fue confirmado según Reuters.")
    assert tipo == "cita"
    assert "Reuters" in fuente


def test_clasificar_oracion_sin_clasificar():
    tipo, fuente = clasificar_oracion("El estrecho tiene una longitud de doscientos kilómetros.")
    assert tipo == "sin_clasificar"


def test_extraer_verificaciones_genera_lista():
    cuerpo = (
        "El régimen de Irán anunció el cierre del estrecho de Ormuz. "
        '"Cerraremos el estrecho", dijo el portavoz según Reuters. '
        "El 80% del petróleo del Golfo pasa por ese punto."
    )
    verificaciones = extraer_verificaciones(cuerpo)
    assert len(verificaciones) >= 2
    tipos = {v.tipo for v in verificaciones}
    assert "cita" in tipos or "estadistica" in tipos


def test_parsear_articulo_llama_requests(mocker):
    respuesta_mock = MagicMock()
    respuesta_mock.text = HTML_MUESTRA
    respuesta_mock.raise_for_status = MagicMock()
    mocker.patch("scraper.parseador_articulo.requests.get", return_value=respuesta_mock)
    mocker.patch("scraper.parseador_articulo.time.sleep")

    url = "https://www.infobae.com/america/mundo/2026/06/20/nota-ejemplo/"
    resultado = parsear_articulo(url, delay=0)

    assert resultado.noticia.titulo == "Título de prueba"
    assert resultado.noticia.seccion == "america/mundo"
    assert resultado.noticia.imagen_portada == "https://img.infobae.com/foto.jpg"
    assert len(resultado.temas) == 2
```

- [ ] **Paso 2: Ejecutar tests y verificar que fallan**

```bash
pytest tests/test_parseador_articulo.py -v
```

Resultado esperado: `ModuleNotFoundError: No module named 'scraper.parseador_articulo'`

- [ ] **Paso 3: Implementar `scraper/parseador_articulo.py`**

```python
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
    return "/".join(segmentos[:2]) if len(segmentos) >= 2 else segmentos[0]


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
```

- [ ] **Paso 4: Ejecutar tests y verificar que pasan**

```bash
pytest tests/test_parseador_articulo.py -v
```

Resultado esperado: 13 tests PASSED

- [ ] **Paso 5: Commit**

```bash
git add scraper/parseador_articulo.py tests/test_parseador_articulo.py
git commit -m "feat: parseador de articulos con extraccion de verificaciones"
```

---

### Tarea 5: Driver Selenium + Crawleador de sección

**Archivos:**
- Crear: `infobae_scraper/scraper/driver.py`
- Crear: `infobae_scraper/scraper/crawleador_seccion.py`
- Test: `infobae_scraper/tests/test_crawleador_seccion.py`

**Interfaces:**
- Produce:
  - `crear_driver() -> webdriver.Chrome`
  - `obtener_urls_seccion(driver: webdriver.Chrome, seccion: str, max_articulos: int = 50, delay_scroll: float = 2.0) -> list[str]`

- [ ] **Paso 1: Escribir tests que fallan**

`infobae_scraper/tests/test_crawleador_seccion.py`:
```python
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
    driver.execute_script.side_effect = [500, 500]

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
    driver.execute_script.side_effect = [500, 500]

    urls = obtener_urls_seccion(driver, "/america/mundo/", max_articulos=5, delay_scroll=0)

    assert len(urls) <= 5


def test_para_cuando_altura_no_cambia():
    driver = MagicMock()
    driver.find_elements.return_value = [
        _hacer_enlace("https://www.infobae.com/america/mundo/2026/06/20/nota-a/"),
    ]
    driver.execute_script.side_effect = [300, 300]

    urls = obtener_urls_seccion(driver, "/america/mundo/", max_articulos=100, delay_scroll=0)

    assert driver.execute_script.call_count == 2


def test_construye_url_con_barra_inicial():
    driver = MagicMock()
    driver.find_elements.return_value = []
    driver.execute_script.side_effect = [0, 0]

    obtener_urls_seccion(driver, "/america/mundo/", max_articulos=1, delay_scroll=0)

    driver.get.assert_called_once_with("https://www.infobae.com/america/mundo/")
```

- [ ] **Paso 2: Ejecutar tests y verificar que fallan**

```bash
pytest tests/test_crawleador_seccion.py -v
```

Resultado esperado: `ModuleNotFoundError: No module named 'scraper.crawleador_seccion'`

- [ ] **Paso 3: Implementar `scraper/driver.py`**

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def crear_driver() -> webdriver.Chrome:
    opciones = Options()
    opciones.add_argument("--headless")
    opciones.add_argument("--no-sandbox")
    opciones.add_argument("--disable-dev-shm-usage")
    opciones.add_argument("--disable-gpu")
    opciones.add_argument("--window-size=1920,1080")
    opciones.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    servicio = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=servicio, options=opciones)
```

- [ ] **Paso 4: Implementar `scraper/crawleador_seccion.py`**

```python
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
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(delay_scroll)
        altura_nueva = driver.execute_script("return document.body.scrollHeight")

        if altura_nueva == altura_anterior:
            break

    return list(urls_encontradas)[:max_articulos]
```

- [ ] **Paso 5: Ejecutar tests y verificar que pasan**

```bash
pytest tests/test_crawleador_seccion.py -v
```

Resultado esperado: 4 tests PASSED

- [ ] **Paso 6: Commit**

```bash
git add scraper/driver.py scraper/crawleador_seccion.py tests/test_crawleador_seccion.py
git commit -m "feat: crawleador de seccion con Selenium y scroll infinito"
```

---

### Tarea 6: CLI (`main.py`)

**Archivos:**
- Crear: `infobae_scraper/main.py`

**Interfaces:**
- Consume: `crear_driver` de `scraper.driver`, `obtener_urls_seccion` de `scraper.crawleador_seccion`, `parsear_articulo` de `scraper.parseador_articulo`, `EscritorCSV` de `salida.escritor_csv`

- [ ] **Paso 1: Implementar `main.py`**

(No hay tests unitarios para CLI; se verifica con ejecución manual en Paso 2.)

```python
import argparse
import sys

from salida.escritor_csv import EscritorCSV
from scraper.crawleador_seccion import obtener_urls_seccion
from scraper.driver import crear_driver
from scraper.parseador_articulo import parsear_articulo


def procesar_url(url: str, escritor: EscritorCSV, delay: float):
    resultado = parsear_articulo(url, delay=delay)
    escritor.guardar(resultado)
    print(f"OK: {resultado.noticia.titulo[:60]}")


def modo_url(url: str, directorio_salida: str, delay: float):
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
    parser.add_argument("--salida", type=str, default="salida", help="Directorio de salida para CSVs")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay entre requests en segundos")
    args = parser.parse_args()

    if args.url:
        modo_url(args.url, args.salida, args.delay)
    else:
        modo_seccion(args.seccion, args.max, args.salida, args.delay)


if __name__ == "__main__":
    main()
```

- [ ] **Paso 2: Verificar modo --url con artículo real**

```bash
cd infobae_scraper
python main.py --url "https://www.infobae.com/america/mundo/2026/06/20/el-regimen-de-iran-anuncio-el-cierre-del-estrecho-de-ormuz-por-los-ataques-israelies-contra-hezbollah-en-el-libano/" --salida test_salida
```

Resultado esperado:
```
OK: <título del artículo>
```

Verificar archivos generados:
```bash
ls test_salida/
# noticias.csv  medios.csv  temas.csv  autores.csv  verificaciones.csv
# rel_publica.csv  rel_menciona.csv  rel_escrito_por.csv  rel_verifica.csv

head -5 test_salida/noticias.csv
head -5 test_salida/verificaciones.csv
```

- [ ] **Paso 3: Ejecutar suite completa de tests**

```bash
pytest tests/ -v
```

Resultado esperado: todos los tests PASSED (≥30 tests).

- [ ] **Paso 4: Commit final**

```bash
git add main.py
git commit -m "feat: CLI con modos --url y --seccion"
```

---

## Ejemplo de uso final

```bash
# Un artículo
python main.py --url "https://www.infobae.com/america/mundo/2026/06/20/nota/" --salida datos/

# Sección completa (100 artículos, delay 3s)
python main.py --seccion "/america/mundo/" --max 100 --delay 3 --salida datos/

# Inspeccionar resultados
wc -l datos/noticias.csv
wc -l datos/verificaciones.csv
```

## Importar a Neo4j

```cypher
LOAD CSV WITH HEADERS FROM 'file:///noticias.csv' AS row
CREATE (:Noticia {noticia_id: row.noticia_id, url: row.url, titulo: row.titulo, seccion: row.seccion});

LOAD CSV WITH HEADERS FROM 'file:///medios.csv' AS row
CREATE (:Medio {medio_id: row.medio_id, nombre: row.nombre});

LOAD CSV WITH HEADERS FROM 'file:///autores.csv' AS row
MERGE (:Autor {autor_id: row.autor_id, nombre: row.nombre});

LOAD CSV WITH HEADERS FROM 'file:///temas.csv' AS row
MERGE (:Tema {tema_id: row.tema_id, nombre: row.nombre});

LOAD CSV WITH HEADERS FROM 'file:///verificaciones.csv' AS row
CREATE (:Verificacion {verificacion_id: row.verificacion_id, texto: row.texto, tipo: row.tipo, verificado: toBoolean(row.verificado)});

LOAD CSV WITH HEADERS FROM 'file:///rel_publica.csv' AS row
MATCH (m:Medio {medio_id: row.medio_id}), (n:Noticia {noticia_id: row.noticia_id})
CREATE (m)-[:PUBLICA]->(n);

LOAD CSV WITH HEADERS FROM 'file:///rel_escrito_por.csv' AS row
MATCH (n:Noticia {noticia_id: row.noticia_id}), (a:Autor {autor_id: row.autor_id})
CREATE (n)-[:ESCRITO_POR]->(a);

LOAD CSV WITH HEADERS FROM 'file:///rel_menciona.csv' AS row
MATCH (n:Noticia {noticia_id: row.noticia_id}), (t:Tema {tema_id: row.tema_id})
CREATE (n)-[:MENCIONA]->(t);

LOAD CSV WITH HEADERS FROM 'file:///rel_verifica.csv' AS row
MATCH (v:Verificacion {verificacion_id: row.verificacion_id}), (n:Noticia {noticia_id: row.noticia_id})
CREATE (v)-[:VERIFICA]->(n);
```
