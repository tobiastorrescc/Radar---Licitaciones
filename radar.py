name: Radar diario de licitaciones

on:
  workflow_dispatch:
  schedule:
    - cron: '0 11 * * *'

permissions:
  contents: write

concurrency:
  group: radar-diario
  cancel-in-progress: false

jobs:
  ejecutar-radar:
    runs-on: ubuntu-latest

    steps:
      - name: Descargar archivos
        uses: actions/checkout@v4
        with:
          ref: main
          persist-credentials: true

      - name: Preparar Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Ejecutar radar
        run: python radar.py

      - name: Guardar resultados descargables
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: radar-resultados
          path: |
            radar_estado.json
            licitaciones_nuevas.json
            auditoria_fuentes.json
          if-no-files-found: warn
          retention-days: 30

      - name: Persistir historial en el repositorio
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
          git add radar_estado.json licitaciones_nuevas.json auditoria_fuentes.json
          if ! git diff --cached --quiet; then
            git commit -m 'Actualizar historial de licitaciones [skip ci]'
            git push origin HEAD:main
          else
            echo 'Sin cambios para guardar'
          fi
