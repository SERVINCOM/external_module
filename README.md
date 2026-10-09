# SERVINCOM — Odoo 20 Community

Repositorio público `external_module`, rama `20.0`.

Los addons se colocan directamente en la raíz. Las carpetas `docs` y `templates`
no son addons. Los módulos nuevos de SERVINCOM siguen `AGENTS.md`, incluyen
traducción española e icono corporativo, y se prueban antes del despliegue.

Flujo: carpeta local en `Documents/Odoo/repos/20.0/external_module` → commit y push
a GitHub en `20.0` → actualización controlada del servidor → instalación o
actualización únicamente de los módulos afectados.

Consultar `docs/workflow_odoo20.md`. Nunca guardar credenciales ni datos de clientes.

## Módulo provisional

`web_responsive` 20.0.1.0.0 procede de la migración de OCA/web
[PR #3679](https://github.com/OCA/web/pull/3679), aún sin integrar. Se conserva
sin cambios, con su licencia LGPL-3 y sus créditos originales. La referencia
exacta está en `docs/upstream_modules.json`. No sustituirlo por otra revisión
sin comparar cambios y validarla en Odoo 20.
