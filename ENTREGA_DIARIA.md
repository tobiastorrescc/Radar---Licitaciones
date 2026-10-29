# Consulta y entrega gratuita del informe

El piloto sigue en `mejora/radar-auditable`; no necesita un servidor ni una PC encendida.

Cada escaneo diario prepara todos los registros, sin tope, en Markdown, JSON, CSV y un correo `.eml` con adjuntos. Se separan publicaciones nuevas con fecha comprobada, detecciones sin fecha o del mismo día, modificaciones/datos completados y recuperaciones históricas. La primera línea de base no se envía como miles de novedades.

El último informe queda en [piloto_reportes/ultimo/informe.md](https://github.com/tobiastorrescc/Radar---Licitaciones/blob/mejora/radar-auditable/piloto_reportes/ultimo/informe.md) después del próximo escaneo diario exitoso. Si aún no existe, consultar el artefacto `radar-controlado` del último escaneo. Los commits conservan los informes anteriores; las auditorías, catálogo completo, abiertas y próximas a vencer siguen en artefactos de Actions durante 90 días. Los respaldos incrementales del historial permanecen en Git y no dependen de la expiración de artefactos.

El CSV protege contra ejecución de fórmulas provenientes del texto de terceros. No se incluye costo propio, búsqueda de proveedores ni cálculo de margen. Los presupuestos de monedas distintas se agrupan por moneda, sin convertirlos ni afirmar comparabilidad.

## Correo: preparado, sin activar

No hay destinatarios, credenciales ni llamadas SMTP en esta implementación. Un archivo `.eml` no equivale a un correo enviado. La autorización para instalar el programador no se reutiliza para enviar mensajes comerciales ni informes por correo.

| Alternativa | Servicio / permisos necesarios | Costo y límites | Estado |
|---|---|---|---|
| GitHub + informe persistido | Acceso al repositorio y suscripción a notificaciones | Sin servidor adicional; runners públicos estándar. Notificaciones nativas de fallos, no envío del informe íntegro por éxito | Consulta automática preparada; alertas del piloto ya activas |
| Cuenta personal Gmail por SMTP desde Actions | Cuenta remitente, segundo factor y contraseña de aplicación si la política de la cuenta lo permite; destinatario autorizado. Guardar remitente, destinatario y contraseña como secretos, nunca en Git | Puede utilizar una cuenta gratuita existente; cuotas y límites de adjuntos de Google. No promete entrega ni disponibilidad antes de verificar la cuenta | Opción gratuita para evaluar si la cuenta lo permite; Google recomienda OAuth sobre contraseñas de aplicación. No conectada ni activada |
| Proveedor transaccional con plan gratuito | Verificación del remitente/dominio y clave API como secreto | Cuotas, dominio propio y condiciones variables. Un dominio nuevo puede tener costo | Alternativa si Gmail no permite SMTP |

Antes de activar correo: elegir cuenta y destinatario, confirmar permisos de la cuenta, probar una entrega expresamente autorizada, verificar conectividad TLS del runner y límite de adjuntos, e incorporar un registro persistente de mensajes por corrida para evitar reenvíos. Si el informe supera un límite de adjuntos, se enviará el enlace completo y se informará la limitación; nunca se ocultarán filas. El informe publicado seguirá disponible aunque falle el correo.

## Descubrimiento periódico

El workflow del piloto ejecuta un trabajo independiente de descubrimiento después de conservar el respaldo. Cada tres días revisa hasta 36 candidatos y 12 búsquedas con un presupuesto de 180 segundos, rotando el padrón y conservando evidencia. Los límites acotan las solicitudes, nunca la cantidad de oportunidades informadas. Los candidatos dudosos no se convierten en fuentes confiables. La auditoría de desarrollo puede revisar lotes más amplios sin modificar el historial diario.

El cron de un workflow situado solamente en una rama no se ejecuta por sí mismo: por eso el descubrimiento periódico se conecta al trabajador que despacha el programador instalado en `main`. No se añade otro programador ni se reactiva el cron legado.

Referencias verificadas el 29/10/2026: [contraseñas de aplicación y sus restricciones](https://support.google.com/accounts/answer/185833), [recomendación de inicio de sesión seguro de Google](https://support.google.com/mail/answer/7126229). Nunca utilizar la contraseña normal de la cuenta.
