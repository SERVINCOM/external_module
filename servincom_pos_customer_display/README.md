# SERVINCOM POS Customer Display

Mejora la pantalla de cliente del Punto de Venta de Odoo 16 Community para que
la información de compra se presente sobre un fondo visual cuidado y legible.

## Objetivo

- Sustituir el gran bloque oscuro del visor estándar por una composición más clara.
- Mostrar un fondo a pantalla completa con paneles translúcidos para productos y totales.
- Mantener visibles el logotipo de la compañía, el total, los pagos y el cambio.
- Permitir un fondo y un mensaje comercial distintos para cada Punto de Venta.
- Mantener intactos los flujos de venta, cliente, pago, reembolso y cierre de sesión.

## Configuración

1. Instale el módulo `servincom_pos_customer_display`.
2. Acceda a **Punto de venta > Configuración > Ajustes**.
3. Seleccione el Punto de Venta que desea configurar.
4. En **Dispositivos conectados > Pantalla del cliente**, active el visor local.
5. Opcionalmente, cargue un fondo personalizado y escriba el mensaje comercial.
6. Si el fondo ya contiene el logotipo, desactive **Mostrar logotipo sobre el fondo**.
7. Guarde los ajustes y abra una sesión nueva del TPV.

Si no se carga un fondo personalizado, el módulo utiliza la imagen incluida por
SERVINCOM. Para una carga rápida se recomienda una imagen horizontal 16:9,
preferiblemente JPEG o WebP y de menos de 1 MB.

## Uso

Desde el TPV, pulse el icono de pantalla del cliente. El visor se abre en una
ventana independiente que puede trasladarse a la pantalla anexa. Sin líneas de
pedido se prioriza el fondo; al añadir productos aparecen la lista y el resumen
de pago sobre paneles de alto contraste.

## Pruebas

- Abrir el visor con el pedido vacío y comprobar fondo, logotipo, mensaje y total.
- Añadir uno y varios productos y revisar nombre, cantidad, precio y desplazamiento.
- Añadir líneas de pago y comprobar total, métodos de pago y cambio.
- Probar una imagen personalizada y volver después al fondo predeterminado.
- Comprobar el visor en pantalla horizontal y vertical.
- Confirmar que producto, cliente, pago, pedidos, reembolso y cierre no cambian.

## Compatibilidad

- Odoo 16 Community.
- Dependencia exclusiva de `point_of_sale`.
- Licencia AGPL-3.

## Créditos

Desarrollado por SERVINCOM SOLUCIONES, S.L.

https://www.servincom.com
