SERVINCOM POS Closing Receipt
=============================

Módulo independiente para Odoo 16 Community que mejora tanto el ticket de
venta entregado al cliente como el ticket impreso desde el botón de impresora
del popup de cierre de sesión del TPV.

Objetivo
========

El ticket de cierre imprime la información operativa necesaria para
revisar la caja al finalizar una sesión TPV:

* punto de venta;
* sesión TPV;
* usuario/cajero;
* fecha y hora;
* total de pedidos;
* total vendido;
* métodos de pago con importe esperado, contado y diferencia cuando
  aplica;
* desglose por método de ventas TPV, cobros de deuda de clientes y
  reembolsos con referencia del pedido cuando esos datos están
  disponibles;
* efectivo esperado, contado y diferencia;
* desglose de efectivo con apertura, entradas, salidas, pagos en
  efectivo y movimientos de caja;
* nota de apertura;
* nota de cierre escrita en el popup.

Configuración
=============

1. Instale el módulo ``servincom_pos_closing_receipt``.
2. En la configuración de cada punto de venta, active ``Ticket de comerciante
   minorista`` cuando no deba mostrarse en el ticket el desglose de impuestos
   ni su total. Esta opción solo cambia la presentación del ticket y no altera
   los impuestos ni la contabilidad.
3. Active ``Personalizar el operario en el ticket`` únicamente si desea
   modificar el comportamiento estándar de Odoo.
4. Elija si el ticket debe mostrar el nombre completo del empleado, un
   identificador público o ningún operario.
5. Si elige el identificador, configúrelo, por ejemplo ``Operario 01``, en el
   usuario o en el empleado usado para acceder al TPV. Cuando se trabaja con
   empleados del TPV, prevalece el identificador de la ficha del empleado.
6. Verifique que el punto de venta tiene impresora configurada mediante
   proxy/IoT, igual que para los recibos estándar de Odoo.

Uso
===

1. Abra una sesión TPV.
2. Desde el popup ``Cerrar sesión``, revise los importes contados.
3. Escriba la nota en ``Añadir una nota de cierre...`` si procede.
4. Pulse el botón de impresora del popup.

La personalización del ticket de cierre sustituye únicamente la impresión de
ese botón dentro del popup. Las opciones del ticket de venta solo modifican su
contenido visible. El módulo no cambia el botón de pago, el selector de
cliente, la lista de pedidos, el botón de regresar ni la lógica contable.

También amplía visualmente el popup estándar de cierre para explicar el
importe neto de cada método. El total esperado y el campo contado siguen
siendo los originales de Odoo; las nuevas líneas son únicamente un
desglose informativo y no intervienen en el cierre contable.

Notas técnicas
==============

El módulo extiende el componente POS estándar ``SaleDetailsButton``. Si
el botón se pulsa dentro del popup ``ClosePosPopup``, imprime el ticket
de cierre SERVINCOM; fuera de ese popup conserva el comportamiento
estándar de Odoo. El componente llama a
``pos.session.get_servincom_closing_receipt_data`` y renderiza un
template de recibo propio antes de enviarlo a
``env.proxy.printer.print_receipt``.

La nota de cierre se toma del estado actual del popup en el momento de
imprimir, por lo que aparece en el ticket aunque la sesión aún no se
haya cerrado.

El ticket de cierre añade además dos saltos finales tras la fecha
inferior para que no quede pegada al corte de papel.

En el ticket de venta estándar, el módulo carga el identificador público del
usuario o empleado y, cuando corresponde, sustituye el nombre completo del
cajero. La ocultación del bloque fiscal se controla por cada punto de venta y
se limita a la plantilla del recibo del cliente.

Pruebas
=======

Pruebas recomendadas:

* abrir el TPV y confirmar que la entrada al TPV no muestra errores;
* activar ``Ticket de comerciante minorista`` y confirmar que no aparecen el
  desglose ni el total de impuestos en el ticket de venta;
* confirmar que los impuestos y apuntes contables de la venta no cambian;
* activar ``Personalizar el operario en el ticket``, seleccionar
  ``Identificador de operario`` y comprobar que el ticket muestra
  el identificador configurado sin revelar el nombre completo;
* seleccionar ``No mostrar operario`` y comprobar que el ticket no contiene la
  línea del cajero;
* desactivar ambas opciones y comprobar que el ticket estándar mantiene el
  nombre del cajero y el desglose fiscal;
* abrir el popup de cierre;
* introducir efectivo contado y una nota de cierre;
* imprimir el ticket desde el botón de impresora;
* comprobar que se imprimen nota de apertura y nota de cierre cuando
  existen;
* comprobar métodos efectivo, banco, a cuenta de cliente y otros
  métodos de pago;
* comprobar que una devolución en efectivo y otra por datáfono aparecen
  como ``Reembolso`` con su pedido y mantienen el total neto correcto;
* comprobar que un cobro de deuda por datáfono aparece separado de las
  ventas TPV;
* cerrar la sesión TPV después de imprimir.
