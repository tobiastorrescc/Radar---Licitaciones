#!/usr/bin/env bash
# Runner efímero: reutilizar binarios, instalar con índices existentes y actualizar
# sólo repositorios oficiales Ubuntu si la instalación lo requiere.
set -euo pipefail
# Lectura de planillas sin ejecutar Office. Versiones reproducibles.
if ! python -c 'import openpyxl,xlrd' 2>/dev/null; then
  python -m pip install --disable-pip-version-check --timeout 15 --retries 1 openpyxl==3.1.5 xlrd==2.0.2
fi
if python - <<'PY'
import shutil,subprocess,sys
ok=all(shutil.which(n) for n in ('pdftotext','pdfinfo','pdftoppm','tesseract'))
if ok:ok='spa' in subprocess.check_output(['tesseract','--list-langs'],text=True,stderr=subprocess.DEVNULL).splitlines()
sys.exit(0 if ok else 1)
PY
then
  echo 'Lectura documental disponible; no se repite instalación.'
  exit 0
fi
opciones=(-o Acquire::Retries=0 -o Acquire::http::Timeout=8 -o Acquire::https::Timeout=8 -o DPkg::Lock::Timeout=20)
if ! sudo apt-get "${opciones[@]}" install -y --no-install-recommends poppler-utils tesseract-ocr tesseract-ocr-spa; then
  if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then
    apt_temporal=$(mktemp -d)
    trap 'rm -rf "$apt_temporal"' EXIT
    # Alternativa pública oficial ante fallo del mirror Azure del runner.
    sed 's|azure.archive.ubuntu.com|archive.ubuntu.com|g' /etc/apt/sources.list.d/ubuntu.sources > "$apt_temporal/ubuntu.sources"
    opciones+=(-o "Dir::Etc::sourcelist=$apt_temporal/ubuntu.sources" -o Dir::Etc::sourceparts=- -o APT::Get::List-Cleanup=0)
    sudo apt-get "${opciones[@]}" update
  else
    sudo apt-get "${opciones[@]}" update
  fi
  sudo apt-get "${opciones[@]}" install -y --no-install-recommends poppler-utils tesseract-ocr tesseract-ocr-spa
fi
pdftotext -v
tesseract --list-langs
