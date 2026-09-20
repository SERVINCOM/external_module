SERVINCOM POS Closing Receipt
=============================

Módulo independiente para Odoo 16 Community que mejora el ticket impreso
desde el botón de impresora del popup de cierre de sesión del TPV.

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
2. Verifique que el punto de venta tiene impresora configurada mediante
   proxy/IoT, igual que para los recibos estándar de Odoo.

Uso
===

1. Abra una sesión TPV.
2. Desde el popup ``Cerrar sesión``, revise los importes contados.
3. Escriba la nota en ``Añadir una nota de cierre...`` si procede.
4. Pulse el botón de impresora del popup.

El módulo sustituye únicamente la impresión de ese botón dentro del
popup de cierre. No modifica el botón de pago, el selector de cliente,
la lista de pedidos, el botón de regresar ni la lógica contable.

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

Pruebas
=======

Pruebas recomendadas:

* abrir el TPV y confirmar que la entrada al TPV no muestra errores;
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
