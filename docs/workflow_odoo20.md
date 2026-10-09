# Flujo Odoo 20 — SERVINCOM SOLUCIONES

1. Trabajar en `Documents/Odoo/repos/20.0/external_module`, rama `20.0`.
2. Revisar `git status`, `git diff`, manifest, imports, XML, assets, traducciones y pruebas.
3. Añadir únicamente archivos del cambio, hacer un commit concreto y `git push origin 20.0`.
4. En el servidor, actualizar el repositorio correspondiente con avance directo (`git pull --ff-only`). Comprobar commit, permisos y dependencias.
5. Instalar o actualizar solo los módulos solicitados y en la base autorizada. En bases reales, confirmar snapshot antes de cambios.
6. Revisar logs y probar en navegador.

## Repositorios y bases

El código y las rutas `addons_path` pertenecen al servidor; los módulos instalados
y sus datos pertenecen a cada base. Duplicar una base conserva sus módulos
instalados y usa las mismas rutas del servidor. Una copia completa del servidor
conserva los checkouts y la configuración que existían al tomarla. Crear un
servidor nuevo desde Ubuntu requiere repetir su aprovisionamiento.

No se crean ni duplican bases para una prueba sin autorización específica.
Las copias de servidor conservan sus claves de despliegue: son solo de lectura
y deben revisarse si el nuevo servidor cambia de propietario o ámbito.

## Ejemplo de instalación o actualización

Desde una sesión root autorizada, adaptar `<base>` y `<modulo>`:

```sh
systemctl stop odoo20
runuser -u odoo20 -- /opt/odoo20/venv/bin/python /opt/odoo20/20.0/odoo/odoo-bin -c /opt/odoo20/config/odoo20.conf -d <base> -u <modulo> --stop-after-init
systemctl start odoo20
systemctl status odoo20 --no-pager
```

Para la primera instalación usar `-i` en lugar de `-u`. Si falla, revisar el
registro antes de repetir. Los cambios de un módulo ya instalado no se aplican
por copiar el código: requieren su actualización.
