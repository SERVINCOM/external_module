SERVINCOM POS Customer Credit Settlement
========================================

Módulo para Odoo 16 Community que permite vender tickets del TPV a
crédito de cliente y cobrar posteriormente esas deudas desde el propio
TPV sin crear una venta nueva, sin líneas de producto ficticias y sin
volver a generar impuestos.

Configuración
=============

1. Active el módulo ``servincom_pos_customer_credit_settlement``.
2. En cada contacto autorizado marque ``Cliente de crédito TPV`` en la
   pestaña ``TPV / Crédito``.
3. Cree o edite un método de pago de TPV para deuda, por ejemplo
   ``A cuenta``, y marque ``Pago a crédito de cliente``.
4. En el punto de venta active:

   * ``Activar crédito de clientes TPV``.
   * ``Permitir cobro de deuda desde TPV``.
   * Opcionalmente, configure el método de pago de crédito por defecto y
     la cuenta contable orientativa de crédito.

5. Asegúrese de que los métodos reales de cobro, como efectivo o
   tarjeta, tienen diario contable configurado si quiere que el cobro
   posterior genere ``account.payment``.

Venta a crédito
===============

En el TPV, seleccione un cliente marcado como ``Cliente de crédito TPV``
y pague todo o parte del ticket con un método marcado como
``Pago a crédito de cliente``.

Validaciones aplicadas:

* No se permite usar el método de crédito sin cliente.
* No se permite usarlo con clientes no autorizados.
* La deuda creada es solo el importe pagado con el método de crédito.
  Si un ticket de 25 EUR se paga con 10 EUR en efectivo y 15 EUR a
  crédito, la deuda será de 15 EUR.

Cobro de deuda desde TPV
========================

Use el botón ``Cobrar deuda`` en la pantalla principal del TPV.

El popup permite:

* buscar clientes de crédito por nombre, NIF/VAT, teléfono o referencia;
* ver tickets pendientes;
* seleccionar uno o varios tickets;
* cobrar el total seleccionado o un importe parcial;
* elegir un método real de cobro;
* impedir que el método de cobro sea otro método de crédito.

El importe cobrado se aplica a los tickets seleccionados por orden de
fecha más antigua primero.

Revisión backend
================

En ``TPV > Crédito de clientes`` encontrará:

* ``Tickets pendientes``: deudas generadas por tickets TPV pagados a
  crédito.
* ``Cobros de deuda``: cobros registrados posteriormente desde el TPV.

Cada sesión TPV muestra una sección ``Cobros deuda clientes`` con el
total y número de cobros de deuda registrados en esa sesión.

Contabilidad
============

El módulo no usa productos ficticios ni crea nuevos pedidos TPV para
cobrar deuda. El cobro posterior crea un registro operativo
``pos.customer.credit.payment`` y, cuando el método real de cobro tiene
diario, intenta crear un ``account.payment`` de cliente::

    570 Caja / Banco
        a 430 Cliente

La venta original y sus impuestos se generan en el ticket TPV original.
El cobro posterior no genera ventas ni impuestos nuevos.

La conciliación automática se intenta contra los apuntes de cliente del
asiento del ticket TPV original cuando Odoo deja trazabilidad contable
suficiente. Si la configuración del TPV o del método de crédito no deja
una cuenta de cliente conciliable, el módulo conserva trazabilidad
operativa completa para conciliación posterior.

Seguridad
=========

El módulo crea dos grupos:

* ``Usuario crédito clientes TPV``: puede ver y registrar cobros
  operativos.
* ``Responsable crédito clientes TPV``: puede cancelar registros y hacer
  correcciones.

Limitaciones conocidas
======================

* La contabilidad final depende de cómo esté configurado el método de
  pago de crédito del TPV. Para un comportamiento contable limpio,
  configure el método de crédito de forma que el pendiente quede en una
  cuenta conciliable de cliente o en una cuenta puente claramente
  revisable.
* Odoo POS no permite crear un ``pos.payment`` limpio sin ``pos.order``;
  por eso los cobros de deuda se registran en modelos propios y, si
  procede, mediante ``account.payment``.
* Las devoluciones o anulaciones con deudas ya cobradas requieren
  revisión de un responsable.
