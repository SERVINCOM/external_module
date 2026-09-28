# Revisión SERVINCOM SOLUCIONES: 18.0.1.0.1

Base: propuesta OCA/sale-workflow #3889, commit
`f1a3a0fda17f8fdcf2a96ecca8c2c91712fd706b` de Studio73/sale-workflow.
Se conservan la autoría OCA, la licencia AGPL-3 y el icono original.

## Correcciones

- La creación de líneas con `discount = 0` y descuentos individuales explícitos
  conserva los componentes y deja calcular el total. Un cero sin componentes
  sigue eliminando los descuentos. Se copian los valores de entrada antes de
  pasarlos al mixin de facturación, que puede modificarlos.
- Actualizar precios vuelve a cargar el primer descuento desde la tarifa después
  del recálculo estándar. Se mantiene el comportamiento estándar de reiniciar
  descuentos manuales: segundo y tercero quedan a cero.
- La excepción de tipo de descuento desconocido usa correctamente sus variables.
- La prueba de tarifa conserva el permiso de descuentos y comprueba el resultado
  automático, sin asignarlo manualmente después de cambiar cantidades.
- Traducciones españolas y plantilla POT actualizadas. La documentación aclara
  que el modo aditivo no está disponible.

## Verificación y límites

Se han comprobado sintaxis Python/XML, catálogos PO/POT, placeholders,
archivos del manifest y estilo Python. Tres reproducciones aisladas de las
rutas afectadas fallan con la versión anterior y pasan con la corrección.
Estas reproducciones no ejecutan el ORM ni validan una base Odoo.

Se incluyen tres regresiones adicionales en la suite Odoo y se corrige la
prueba de tarifa existente. No se ha ejecutado la suite ORM por no disponer de
Odoo/PostgreSQL local. No se ha accedido al servidor ni modificado una base.
La versión instalada de account_invoice_triple_discount debe verificarse
antes de la prueba; esta revisión utiliza como referencia 18.0.1.0.1.

En un entorno de pruebas aislado, tras actualizar el repositorio:

```bash
./odoo-bin -c <config_pruebas> -d <base_pruebas> -i sale_triple_discount --test-enable --test-tags /sale_triple_discount --stop-after-init
```

Si ya está instalado, sustituir `-i` por `-u`. No ejecutar en paralelo con
un proceso Odoo que atienda la misma base.

Comprobar en interfaz: 100 euros con 10/20/30 produce 50,40 antes de impuestos;
cambio de cantidades con tarifa; actualizar precios después de cambiar la
tarifa; creación/importación con descuentos explícitos; presupuesto a factura;
PDF y traducciones. Comparar documentos anteriores, pues los hooks de primera
instalación inicializan descuentos de líneas existentes. Revisar logs y la
suite antes de aprobar producción, siempre con copia/snapshot confirmado.
