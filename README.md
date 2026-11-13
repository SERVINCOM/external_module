# SERVINCOM — Odoo 20 Community

Repositorio público `external_module`, rama `20.0`.

Los addons se colocan directamente en la raíz. Las carpetas `docs` y `templates`
no son addons. Los módulos nuevos de SERVINCOM siguen `AGENTS.md`, incluyen
traducción española e icono corporativo, y se prueban antes del despliegue.

Flujo: carpeta local en `Documents/Odoo/repos/20.0/external_module` → commit y push
a GitHub en `20.0` → actualización controlada del servidor → instalación o
actualización únicamente de los módulos afectados.

Consultar `docs/workflow_odoo20.md`. Nunca guardar credenciales ni datos de clientes.

## Dependencia del menú de aplicaciones

El menú de aplicaciones de SERVINCOM utiliza `web_responsive` de la rama
`20.0` de [OCA/web](https://github.com/OCA/web/tree/20.0/web_responsive).
Antes de desplegar esta revisión en una instalación que usaba la copia
provisional, actualiza OCA/web y comprueba que está en `addons_path`.
