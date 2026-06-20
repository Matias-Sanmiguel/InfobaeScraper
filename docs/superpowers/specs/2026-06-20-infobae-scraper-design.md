# Diseño: Infobae Scraper — Proyecto Investigación Fake News

**Fecha:** 2026-06-20  
**Stack:** Python, Selenium, requests, BeautifulSoup4  
**Salida:** JSONL  
**Destino:** Neo4j

---

## Objetivo

Scraper de artículos de Infobae para investigación sobre fake news. Dos modos: artículo individual (URL) y crawl de sección (ej: `/america/mundo/`). Salida en `.jsonl` compatible con importación a Neo4j.

---

## Arquitectura

```
infobae_scraper/
├── scraper/
│   ├── section_crawler.py   # Selenium: descubre URLs de una sección
│   ├── article_parser.py    # requests + BS4: parsea artículo individual
│   └── driver.py            # configuración Selenium headless
├── models/
│   └── esquema.py           # dataclasses: Articulo, Claim, PlantillaNeo4j
├── output/
│   └── escritor.py          # escribe .jsonl
├── main.py                  # CLI: --url / --seccion / --max-articulos
└── requirements.txt
```

### Flujo — modo sección

1. `main.py --seccion "/america/mundo/" --max 100`
2. `section_crawler.py` abre Selenium headless, scrollea hasta cargar N artículos, extrae lista de URLs
3. Por cada URL → `article_parser.py` hace GET con `requests`, parsea HTML con BS4
4. Resultado → `escritor.py` appenda línea al `.jsonl`

### Flujo — modo artículo individual

1. `main.py --url "https://www.infobae.com/..."`
2. Directo a `article_parser.py`
3. Resultado → `.jsonl`

---

## Campos scrapeados

### Nodo `Articulo`

| Campo | Tipo | Fuente HTML |
|---|---|---|
| `id` | str | SHA256(url) |
| `url` | str | input |
| `titulo` | str | `h1.article-headline` |
| `cuerpo` | str | `div.article-body` |
| `fecha_publicacion` | datetime | `<time>` / meta `article:published_time` |
| `fecha_modificacion` | datetime | meta `article:modified_time` |
| `seccion` | str | path de URL |
| `fuente` | str | "Infobae" (fijo) |
| `autores` | list[str] | `a.author-name` |
| `tags` | list[str] | `a.tag` / meta keywords |
| `imagen_portada` | str | `og:image` |

### Nodo `Claim`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | str | SHA256(texto) |
| `texto` | str | Oración extraída del cuerpo |
| `tipo` | str | `afirmacion` / `cita` / `estadistica` / `sin_clasificar` |
| `verificado` | bool | False por defecto (anotación manual posterior) |
| `fuente_citada` | str | Fuente explícita si aparece en texto |

**Heurística extracción de claims:**
- `cita`: oraciones con comillas o verbos de declaración ("dijo", "afirmó", "según")
- `estadistica`: oraciones con cifras numéricas significativas (%, millones, miles)
- `afirmacion`: resto de oraciones principales del primer y último párrafo
- `sin_clasificar`: default

---

## Modelo Neo4j

### Nodos
- `Article`
- `Author`
- `Tag`
- `Claim`

### Relaciones
```
(Article)-[:ESCRITO_POR]->(Author)
(Article)-[:TIENE_TAG]->(Tag)
(Article)-[:CONTIENE]->(Claim)
(Claim)-[:EVIDENCIA_DE]->(Article)
```

---

## Formato de salida — múltiples CSVs

Compatible con `neo4j-admin database import` y `LOAD CSV`.

### Nodos

**`noticias.csv`**
```
noticia_id,url,titulo,cuerpo,fecha_publicacion,fecha_modificacion,seccion,imagen_portada
```

**`medios.csv`**
```
medio_id,nombre
```
(siempre una fila: `infobae,Infobae`)

**`temas.csv`**
```
tema_id,nombre
```

**`autores.csv`**
```
autor_id,nombre
```

**`verificaciones.csv`**
```
verificacion_id,texto,tipo,verificado,fuente_citada
```

### Relaciones

**`rel_publica.csv`** — `(Medio)-[:PUBLICA]->(Noticia)`
```
medio_id,noticia_id
```

**`rel_menciona.csv`** — `(Noticia)-[:MENCIONA]->(Tema)`
```
noticia_id,tema_id
```

**`rel_escrito_por.csv`** — `(Noticia)-[:ESCRITO_POR]->(Autor)`
```
noticia_id,autor_id
```

**`rel_verifica.csv`** — `(Verificacion)-[:VERIFICA]->(Noticia)`
```
verificacion_id,noticia_id
```

---

## CLI

```bash
# Artículo individual
python main.py --url "https://www.infobae.com/..."

# Sección completa
python main.py --seccion "/america/mundo/" --max 100 --salida datos.jsonl

# Opciones
--salida       # archivo de salida (default: output/datos.jsonl)
--max          # máximo de artículos en modo sección (default: 50)
--delay        # delay entre requests en segundos (default: 2)
```

---

## Dependencias

```
selenium
webdriver-manager
requests
beautifulsoup4
lxml
python-dateutil
```

---

## Restricciones

- Solo Infobae como fuente (hardcodeado, no genérico)
- Código en español (nombres de variables, funciones, clases)
- Sin comentarios en el código
- `delay` mínimo 2s entre requests (ética de scraping)
- No recursivo: sección → lista de URLs, no seguir links internos de artículos
