# Alternativa externa preparada, sin activar

La opción preferida actual es [100% GitHub Actions](PROGRAMADOR_GITHUB.md). Esta alternativa se conserva como antecedente y debe permanecer desactivada.

El PR #1 continúa en `mejora/radar-auditable`. No se modifica `main` ni producción. La configuración entregada tiene `habilitado: false`: no se instaló ningún servicio, credencial ni temporizador. Los ensayos del PR ejecutan una simulación sin red del programador y auditorías aisladas de Actions; no habilitan la periodicidad.

## Arquitectura y horario

Un servidor Linux externo con systemd ≥247, Python ≥3.9 y tzdata invoca la API `workflow_dispatch` de GitHub Actions. El servidor sólo dispara y supervisa; las consultas se ejecutan en los runners de GitHub. No necesita copiar el historial de producción ni ejecutar el radar localmente.

`despliegue/systemd/radar-piloto.timer` programa **08:00 todos los días en America/Argentina/Buenos_Aires**. Actualmente equivale a 11:00 UTC; conserva la zona, no depende de la zona del servidor. `Persistent=false` evita disparar inesperadamente al encender un servidor que estuvo apagado. Un día perdido debe revisarse; no se afirma que no hubiera novedades. GitHub puede demorar el inicio por disponibilidad o cola: las 08:00 son la hora de solicitud, no una garantía de finalización.

El payload es fijo: repositorio `tobiastorrescc/Radar---Licitaciones`, workflow `radar-diario.yml`, rama `mejora/radar-auditable`, `modo=controlado`, `canal=piloto`, `inicializar=false`. No acepta elegir `main`, producción, otra URL de API o una semilla. El título usa una clave por fecha argentina para reconciliar la solicitud con Actions.

## Permisos y secretos

Crear, sólo tras autorización, un **fine-grained PAT** con acceso exclusivamente a este repositorio, **Actions: read/write**, **Contents: read** y Metadata: read implícito. Definir caducidad, responsable de rotación y aviso previo a su vencimiento; un token vencido debe producir fallo visible, no un reinicio del historial. Puede necesitar aprobación de la organización. No necesita Contents: write, Workflows: write, administración ni permiso de merge. Actions: write permite más operaciones de Actions que sólo este disparador: GitHub no ofrece un PAT limitado a un único payload o rama: técnicamente podría despachar otros workflows/refs del repositorio. El aislamiento se aplica en el script fijo y las condiciones del workflow; no se presenta como una restricción de rama del PAT. Proteger el servidor y revocar el token ante incidentes. Una GitHub App con esos permisos y tokens de corta duración es una alternativa futura.

El token queda en `/etc/radar-piloto/github-token`, propietario root, modo 0600; nunca en el repositorio, línea de comandos, URL, journal ni artefactos. systemd `LoadCredential` lo entrega al servicio. No hay token creado ni instalado. El script no sigue redirecciones con credenciales y mantiene TLS. El PAT no puede guardar ni borrar código: el job usa por separado su `GITHUB_TOKEN` con Contents: write únicamente para guardar el respaldo del piloto en su rama. Producción mantiene su propia condición y autorización, sin cambios.

## Preparación e instalación (sin habilitar)

Elegir un servidor permanentemente encendido y con reloj sincronizado; usar una única instancia del programador. Copiar desde una revisión auditada del PR los siguientes archivos a un directorio de software **no escribible por el usuario del servicio**:

- `/opt/radar-piloto/tools/programar_piloto.py`.
- `/etc/radar-piloto/piloto.json`: copia de `despliegue/piloto.json`, conservar `habilitado: false`, root:root, 0644.
- Ambos archivos de `despliegue/systemd/` a `/etc/systemd/system/`.

Crear el usuario de sistema sin login `radar-piloto` y su grupo. systemd crea `/var/lib/radar-piloto` privado. El servicio sólo puede escribir ese estado; `ProtectSystem=strict`, `ProtectHome`, `NoNewPrivileges` y `PrivateTmp` reducen privilegios. No instalar una copia que contenga secretos en el control de versiones. Verificar soporte de `LoadCredential`, Python, tzdata, DNS y HTTPS a `api.github.com`; no desactivar certificados.

Validación previa, sin token ni red:

```sh
python3 /opt/radar-piloto/tools/programar_piloto.py --config /etc/radar-piloto/piloto.json
systemd-analyze calendar '*-*-* 08:00:00 America/Argentina/Buenos_Aires'
# Una vez copiados los archivos y creado el usuario, verificar unidades:
sudo systemd-analyze verify /etc/systemd/system/radar-piloto.service /etc/systemd/system/radar-piloto.timer
sudo systemctl daemon-reload
systemctl is-enabled radar-piloto.timer
systemctl is-active radar-piloto.timer
```

Los dos últimos deben indicar deshabilitado/inactivo. **No ejecutar enable, start ni cambiar habilitado en esta etapa.** No se ejecutaron estos comandos administrativos desde el entorno de desarrollo.

Después de una autorización expresa: instalar el PAT, cambiar `habilitado` a true y habilitar/iniciar el timer. La primera prueba supervisada del servicio y la revisión de su resultado deben preceder a dejarlo operando solo. Esto autoriza únicamente el piloto; producción requiere autorización separada. Para detenerlo, deshabilitar/detener el timer y volver a false; una ejecución ya aceptada en Actions no se cancela automáticamente ni pierde resultados.

## Persistencia, fallos y simultaneidad

- Antes de enviar, comprueba acceso al workflow activo y existencia del índice diario en Git. Una falta de acceso o respaldo impide disparar. La integridad completa de los segmentos se verifica dentro del job antes de consultar fuentes; no se inicializa silenciosamente una base vacía.
- `flock` local + servicio oneshot evitan disparadores simultáneos en el servidor. Detecta ejecuciones recientes activas del mismo workflow/rama y no añade otra. El grupo de concurrencia existente `radar-${github.ref}` serializa todos los despachos en la rama sin cancelar un piloto activo. No instalar dos programadores en hosts diferentes: no hay bloqueo distribuido externo.
- Journal atómico por fecha argentina, archivo y directorio sincronizados a disco; guardar **antes** del POST. Si GitHub acepta pero se pierde la respuesta, una ejecución manual posterior reconcilia por título. Si no puede confirmarla, no reenvía el POST; requiere revisar Actions. Un resultado fallido tampoco causa un segundo despacho automático ese día.
- Peticiones HTTPS con timeout de 20 segundos, respuestas hasta 2 MB, consulta de ejecuciones de los últimos dos días hasta cinco páginas, espera acotada de 50 minutos y corte exterior systemd a 55 minutos. Sin reintentos automáticos de POST ni `Restart=always`. Una consulta API fallida deja evidencia local, no declara éxito. El tiempo total del servicio está limitado aunque una operación se atasque.
- El resultado se supervisa hasta `completed/success`; cancelación, fallo o plazo agotado producen salida no cero, visible como unidad fallida. Una consulta con incidencias por fuente puede terminar correctamente: significa que se conservaron auditoría y datos, **no** que todos los portales funcionen. Consultar `cobertura_estricta` y errores en el artefacto.
- Un fallo de fuente no borra procedimientos anteriores. El job conserva resultados parciales y artefactos incluso si falla; cada respaldo incremental exige continuidad y restauración de prueba, y el push sin force debe completarse. Si falla el push, Actions falla; conservar artefacto y corregir la persistencia antes de continuar. No declarar durable un artefacto que vence.
- El historial diario restaurable sigue en `piloto_respaldo/diario/`: base, incrementos gzip, índice, hashes SHA-256, cadena y hash lógico. Artefactos adicionales: 90 días. El journal del programador sólo conserva control de despachos; no sustituye estos respaldos. Para protección fuera de GitHub, copiar regularmente el repositorio completo a almacenamiento independiente y ensayar restauración. Esa copia externa no está instalada ni se afirma redundancia entre proveedores.

## Consulta, alertas y costo

`journalctl -u radar-piloto.service` y `/var/lib/radar-piloto/AAAA-MM-DD.json` muestran el estado y el enlace al run. En Actions, revisar resumen y descargar `radar-controlado`, abrir `index.html`. Contiene catálogo completo, todas las novedades/cambios, abiertas, próximas a vencer, pagos comprobados o no informados y enlaces; no hay filtros por monto/rubro ni cálculos de rentabilidad. Los cierres históricos y fuentes no observadas siguen visibles.

La unidad fallida y la ausencia del journal del día deben monitorizarse desde el servidor; no se configuró envío de correo ni otro canal de alertas. GitHub puede emitir sus notificaciones según preferencias del usuario, sin garantía de aviso externo. Antes de operar autónomamente conviene configurar una alerta de ausencia/fracaso en la herramienta de monitoreo que se elija.

**Requiere infraestructura externa a este repositorio**: servidor propio, NAS o VPS Linux disponible a las 08:00. systemd y el script no tienen cargo ni requieren contratar un SaaS. Si ya existe ese equipo, no hay suscripción nueva por el programador; un VPS nuevo, energía y almacenamiento pueden tener costo del proveedor. La API de dispatch no tiene tarifa por llamada, sujeta a límites de GitHub. El repositorio es público y GitHub suele ofrecer runners estándar gratuitos para repositorios públicos; verificar las condiciones vigentes y cuotas de artefactos/minutos antes de activar. No se contrató ningún servicio ni se puede asegurar costo total cero. Un servicio de cron SaaS podría sustituir el servidor, pero requeriría custodiar el token y reproducir estos controles; no se configuró uno.

Referencias oficiales consultadas: [permisos de workflow_dispatch](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event), [facturación de Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions). La documentación confirma Actions: write para dispatch y runners estándar gratuitos en repositorios públicos; artefactos/cache tienen condiciones propias que deben revisarse.
