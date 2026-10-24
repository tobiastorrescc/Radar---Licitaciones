from __future__ import annotations

import json
import time
import unicodedata

from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import (
    urljoin,
    urlparse,
    urldefrag,
    parse_qsl,
    urlencode,
    urlunparse,
)
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


ZONA = ZoneInfo("America/Argentina/Buenos_Aires")

ARCHIVO_ESTADO = Path("radar_estado.json")

ROSARIO = (
    "https://www.rosario.gob.ar/"
    "inicio/compras-y-licitaciones"
)

MAX_PAGINAS = 40
MAX_PROFUNDIDAD = 3
TIMEOUT = 15

EXTENSIONES = (
    ".pdf", ".doc", ".docx",
    ".xls", ".xlsx", ".zip"
)

PALABRAS_OPORTUNIDAD = (
