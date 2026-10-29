# Programador diario 100% GitHub Actions

**Instalado y habilitado tras autorización y prueba real.** Main: `dfca1a52c5371929ce6c07741a88fd209a7da852`. Agente e historial diario: `mejora/radar-auditable`. PR #1 abierto y sin merge; historial de producción intacto.

- 08:00 Argentina: despacho único del piloto, con GITHUB_TOKEN y sin servidor/PAT.
- Al terminar: aviso repository_dispatch del worker, verificación por API y alertas.
- 09:30 Argentina: revisión de presencia, cierre y respaldo, sin repetir consultas.
- Cron antiguo radar-diario.yml deshabilitado, sin editar su archivo ni sus datos.

[Informe de instalación, regresiones, pruebas reales y límites](INSTALACION_PILOTO.md) · [Archivo exacto instalado](despliegue/github-actions/programar-piloto.yml.instalado) · [Manifiesto con hash](despliegue/github-actions/manifesto.json).

El coordinador de main sólo usa contents:read, actions:write e issues:write. No hace checkout ni ejecuta código/artefactos de la rama del piloto. El worker escribe únicamente su respaldo en la rama y usa un job pequeño para avisar con un ID; main vuelve a comprobar los metadatos y los pasos de restauración, continuidad y guardado. El horario se habilitó después de comprobar una alerta real y que varios despachos reconocieran una sola consulta.

La preparación anterior, incluida la limitación de workflow_run, queda documentada en los informes históricos; el mecanismo desplegado usa repository_dispatch. No se requiere la alternativa de servidor externo. Las notificaciones de correo dependen de las preferencias del usuario, y GitHub no garantiza puntualidad exacta ni avisos durante una caída total propia.

Fuentes: [GITHUB_TOKEN y eventos de dispatch](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow), [cron y zona horaria](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [costos de Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
