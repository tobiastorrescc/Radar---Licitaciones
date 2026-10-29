"""Lectura de documentos públicos sin ejecutar adjuntos ni extraer rutas de ZIP."""
from io import BytesIO
from pathlib import Path
import os
import re
import subprocess
import tempfile
import zipfile
from xml.etree import ElementTree


def docx(datos):
    with zipfile.ZipFile(BytesIO(datos)) as z:
        i=z.getinfo('word/document.xml')
        if i.file_size>32_000_000:raise ValueError('DOCX excede tamaño seguro')
        root=ElementTree.fromstring(z.read(i))
        return '\n'.join(' '.join(t.text or '' for t in p.iter() if t.tag.endswith('}t'))
                         for p in root.iter() if p.tag.endswith('}p'))


def pdf(datos,ocr=False,progreso=None):
    if not datos.startswith(b'%PDF-'):raise ValueError('Respuesta no es PDF')
    r=subprocess.run(['pdftotext','-layout','-','-'],input=datos,capture_output=True,check=True,timeout=35)
    texto=r.stdout.decode('utf-8')
    if texto.strip():return texto
    if not ocr:raise ValueError('PDF sin texto: requiere OCR; no se declara vacío')
    with tempfile.TemporaryDirectory() as d:
        source=Path(d)/'documento.pdf';source.write_bytes(datos)
        info=subprocess.run(['pdfinfo',str(source)],capture_output=True,text=True,check=True,timeout=5)
        m=re.search(r'^Pages:\s*(\d+)',info.stdout,re.M)
        if not m:raise ValueError('No se pudo obtener cantidad de páginas para OCR')
        paginas=[]
        for pagina in range(1,int(m[1])+1):
            prefix=Path(d)/'pagina'
            subprocess.run(['pdftoppm','-f',str(pagina),'-l',str(pagina),'-scale-to','1600','-singlefile','-png',str(source),str(prefix)],capture_output=True,check=True,timeout=15)
            result=subprocess.run(['tesseract',str(prefix)+'.png','stdout','-l','spa+eng'],capture_output=True,text=True,check=True,timeout=20,env={**os.environ,'OMP_THREAD_LIMIT':'1'})
            paginas.append(result.stdout)
            if progreso:progreso('\n'.join(paginas))
        texto='\n'.join(paginas)
        if not texto.strip():raise ValueError('OCR sin texto reconocido')
        return texto


def excel(datos,url):
    """Tablas públicas: valores, rótulos y fechas; nunca ejecuta fórmulas ni macros."""
    if datos.startswith(b'PK'):
        with zipfile.ZipFile(BytesIO(datos)) as z:
            if sum(i.file_size for i in z.infolist())>32_000_000:raise ValueError('XLSX excede tamaño seguro')
        import openpyxl
        book=openpyxl.load_workbook(BytesIO(datos),read_only=True,data_only=True,keep_links=False)
        try:
            hojas=[];celdas=0
            for ws in book.worksheets:
                if (ws.max_row or 0)>100000 or (ws.max_column or 0)>1000:raise ValueError('Dimensiones XLSX exceden lectura segura')
                filas=[]
                for fila in ws.iter_rows(values_only=True):
                    celdas+=len(fila)
                    if celdas>500000:raise ValueError('Planilla supera presupuesto de celdas; lectura pendiente')
                    filas.append(fila)
                hojas.append((ws.title,filas))
        finally:book.close()
    else:
        import xlrd
        book=xlrd.open_workbook(file_contents=datos,on_demand=True)
        hojas=[]
        try:
            celdas=0
            for ws in book.sheets():
                celdas+=ws.nrows*ws.ncols
                if ws.nrows>100000 or celdas>500000:raise ValueError('XLS excede lectura segura')
                filas=[]
                for i in range(ws.nrows):
                    fila=[]
                    for c in ws.row(i):
                        if c.ctype==xlrd.XL_CELL_DATE:valor=xlrd.xldate.xldate_as_datetime(c.value,book.datemode)
                        else:valor=c.value
                        fila.append(valor)
                    filas.append(fila)
                hojas.append((ws.name,filas))
        finally:book.release_resources()
    from datetime import datetime,date
    def valor(v):
        if v is None:return ''
        if isinstance(v,(date,datetime)):return v.isoformat(sep=' ') if isinstance(v,datetime) else v.isoformat()
        if isinstance(v,float) and v.is_integer():return str(int(v))
        return str(v).replace('\n',' ').strip()
    texto=[]
    for nombre,filas in hojas:
        if len(filas)>100000:raise ValueError('Planilla supera límite de lectura segura; no se declara completa')
        texto.append(nombre)
        for fila in filas:
            celdas=[valor(c) for c in fila]
            if any(celdas):texto.append(' | '.join(celdas))
    if not texto:raise ValueError('Planilla sin celdas reconocibles')
    return '\n'.join(texto)


def leer(datos,tipo,url,ocr=False,progreso=None):
    if datos.startswith(b'%PDF-') or 'pdf' in tipo.lower():return pdf(datos,ocr,progreso)
    if tipo.lower().startswith(('image/jpeg','image/png')):
        if not ocr:raise ValueError('Imagen de publicación requiere OCR')
        with tempfile.TemporaryDirectory() as d:
            image=Path(d)/'publicacion';image.write_bytes(datos)
            r=subprocess.run(['tesseract',str(image),'stdout','-l','spa+eng'],capture_output=True,text=True,check=True,timeout=20,env={**os.environ,'OMP_THREAD_LIMIT':'1'})
            if not r.stdout.strip():raise ValueError('Imagen sin texto reconocido')
            return r.stdout
    if datos.startswith(b'\xd0\xcf\x11\xe0') or (datos.startswith(b'PK') and ('spreadsheet' in tipo.lower() or url.lower().split('?')[0].endswith('.xlsx'))):return excel(datos,url)
    if datos.startswith(b'PK'):
        with zipfile.ZipFile(BytesIO(datos)) as z:
            if 'xl/workbook.xml' in z.namelist():return excel(datos,url)
            if 'word/document.xml' in z.namelist():return docx(datos)
            if sum(i.file_size for i in z.infolist())>32_000_000:raise ValueError('ZIP excede tamaño seguro')
            textos=[]
            for i in z.infolist():
                nombre=i.filename.lower()
                if nombre.endswith(('.pdf','.docx','.txt','.xls','.xlsx')):
                    contenido=z.read(i)
                    textos.append(contenido.decode('utf-8') if nombre.endswith('.txt') else leer(contenido,'',nombre,ocr,progreso))
            if not textos:raise ValueError('ZIP sin documentos de contratación legibles')
            return '\n'.join(textos)
    raise ValueError('Formato de documento no admitido: '+tipo)
