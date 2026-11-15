# Cuadros contables SERVINCOM

Odoo 18 Community · AGPL-3 · SERVINCOM SOLUCIONES, S.L.

Instala un resumen mensual y un detalle por cuentas bajo **Contabilidad → Informes → Cuadro de mando → Resultados mensuales**. Utiliza MIS Builder y el tablero estándar de Odoo, sin modificar sus fuentes ni depender de Enterprise.

## Uso

En **Ajustes → Usuarios y compañías → Usuarios → Permisos de acceso → Cuadros de mando contables**, marcar **Ver cuadros de mando contables**. La casilla es independiente del rol de administrador contable y solo pueden modificarla los administradores de Ajustes. No se marca automáticamente para ningún usuario al instalar.

En la lista de Usuarios, **Añadir filtro personalizado → Ver cuadros de mando contables → está establecido** permite encontrar a quienes tienen acceso y guardar la búsqueda en Favoritos. La búsqueda consulta directamente la pertenencia al grupo, sin duplicar el permiso en una columna almacenada.

El permiso habilita los resultados, el detalle contable, los vencimientos de ventas/compras, sus exportaciones y la consulta de apuntes. Implica el grupo estándar de contabilidad de solo lectura, por lo que permite consultar también otros datos contables sujetos a las reglas existentes. No concede escritura contable. Desmarcar la casilla bloquea estos cuadros incluso para un administrador contable; no revoca otros permisos contables que el usuario ya tenga. El superusuario de Odoo omite las reglas de registro.

Elegir el año desde el primer cuadro y pulsar **Aplicar año**. Los dos informes muestran doce meses y total anual. El año se guarda por empresa y es compartido: si otra persona lo cambia, se verá el último año aplicado al actualizar. La disposición, plegado y ocultación de tarjetas son personales. Las dos tablas comparten el desplazamiento vertical del tablero, sin barras verticales interiores en las tarjetas. El selector funciona con permiso de consulta, sin conceder edición sobre los informes.

## Cálculos y configuración

Las plantillas están destinadas al plan contable español basado en grupos 6 y 7. No son una cuenta de resultados universal para cualquier localización. Ingresos = saldo acreedor del grupo 7; gastos = saldo deudor del grupo 6; resultado = ingresos menos gastos. Se conservan los signos de rectificaciones, se incluyen cuentas residuales y se usan apuntes publicados por fecha contable. El acumulado de meses sin movimientos conserva el saldo anterior y no es una previsión.

Al instalar se crean plantillas e instancias independientes por empresa; para nuevas empresas se crean al abrir el cuadro. No se crean cuentas, facturas ni asientos. Cada empresa conserva su moneda, su ejercicio seleccionado y sus exclusiones.

Antes de usar las cifras, revisar **Contabilidad → Configuración → Configuración de cuadros de mando**, seleccionar los diarios de apertura/cierre que proceda excluir y pulsar **Aplicar diarios excluidos**. No se adivinan códigos de diarios ni se excluyen cierres de TPV. Las plantillas genéricas agrupan las comisiones en 626 y los intereses en 662; no incluyen códigos particulares de un cliente.

Las plantillas XML se cargan con `noupdate=1` para conservar adaptaciones posteriores. Para añadir nuevos cuadros se pueden heredar el modelo, las vistas y las plantillas desde otro addon con una responsabilidad concreta. El análisis de facturación, las comparativas y los presupuestos no forman parte de esta versión.

## Vencimientos de ventas y compras

En **Contabilidad → Informes → Cuadro de mando**, las entradas **Ventas (cobros)** y **Compras (pagos)** muestran el pendiente actual por semana. La vista inicial es una tabla dinámica: pulsar un importe abre el detalle; los botones superiores permiten alternar tabla, lista y gráfico. Se pueden descargar los datos y guardar filtros personales mediante las funciones estándar de Odoo.

Cada fila de detalle corresponde a un plazo contable pendiente, no a una factura completa. Muestra cliente/proveedor, documento, referencia, fecha de factura, vencimiento, importe original del plazo, pendiente actual, estado y liquidación parcial. El botón **Abrir documento** lleva a la factura, rectificativa o asiento original con los permisos del usuario.

Los filtros permiten ver vencidos, vencimientos de hoy, próximos 30 días, ausencia de fecha, liquidaciones parciales y créditos/anticipos; también seleccionar años, meses o fechas de vencimiento. Por defecto se conservan todos los pendientes, incluidos ejercicios anteriores y posteriores. Solo aparecen semanas con partidas pendientes. La agrupación semanal utiliza el primer día de semana configurado para el idioma del usuario (lunes en español); una semana puede cruzar de año.

- Fuente: apuntes publicados y no conciliados de cuentas de tipo cliente/proveedor. Se usan los residuos contables actuales: las conciliaciones parciales reducen el pendiente y las completas hacen desaparecer la partida.
- Incluye impuestos y otros importes integrados en la deuda. No es una vista de ingresos/gastos ni de bases imponibles.
- En compras se invierte el signo contable para presentar las obligaciones de pago como positivas. Las rectificativas y los cobros/pagos sin aplicar conservan signo negativo y reducen el pendiente neto. No se compensan artificialmente entre facturas; se respeta su conciliación real.
- Se incluyen asientos pendientes de apertura y otros asientos de clientes/proveedores, no solo documentos con tipo factura. Así no se ocultan saldos vivos. Se pueden distinguir por **Tipo de documento** y **Diario**.
- La fecha es el vencimiento individual del apunte. Si falta, se agrupa por fecha contable y se marca **Sin fecha de vencimiento** para revisión. No se calcula una fecha contractual nueva.
- Los totales son en moneda de la empresa activa. La moneda y el pendiente del documento están disponibles como columnas opcionales; no se suman monedas extranjeras diferentes. Al cambiar de empresa, volver a abrir la entrada correspondiente.
- Son saldos pendientes **ahora**, no una reconstrucción histórica a una fecha de corte. Filtrar un año selecciona vencimientos de ese año. No incluyen pedidos sin factura, nóminas previstas, cuotas futuras aún no contabilizadas, descuentos por pronto pago hipotéticos ni previsiones externas.
- La fuente conserva las reglas de acceso a apuntes de Odoo y de otros addons, además del permiso independiente y la separación por compañía. No se usan permisos elevados para consultar saldos. La vista es de solo lectura y no crea ni modifica facturas, pagos ni conciliaciones.

La diferencia entre cobros y pagos se puede obtener de los dos totales para el mismo periodo; esta versión mantiene los cuadros separados y no añade un tercer cuadro de tesorería combinado.

Las etiquetas semanales incluyen el intervalo completo, por ejemplo **W1 2026 (29/12/2025 – 04/01/2026)**. **Esta semana** selecciona vencimientos de la semana natural según el idioma del usuario (lunes a domingo en español), incluidos los días ya transcurridos. Se conservan **Vence hoy** y **Próximos 30 días**; los registros sin fecha de vencimiento quedan fuera de estos filtros. Los importes de las filas de resultado respetan el color de su estilo MIS también al pulsarlos.

## Seguridad y mantenimiento

Las reglas globales protegen informes marcados, instancias, indicadores, periodos y anotaciones. Las reglas de compañía de Odoo/MIS se mantienen. El cambio de año eleva permisos únicamente para fechas y títulos de las dos instancias de la empresa activa; no admite IDs de informes, fórmulas ni compañías desde el navegador. La configuración está reservada a administradores de Ajustes. Las vistas personales se crean únicamente para el usuario que abre el tablero.

Dependencias: `mis_builder` (OCA/mis-builder), `account_financial_report` (OCA/account-financial-reporting) y `board` (Odoo Community). MIS Builder aporta `report_xlsx` y sus demás dependencias. El addon debe estar directamente en una ruta de `addons_path`.

```bash
# Instalar en una base existente expresamente autorizada
./odoo-bin -c <config> -d <database> -i servincom_account_dashboard --stop-after-init

# Actualizar una instalación existente
./odoo-bin -c <config> -d <database> -u servincom_account_dashboard --stop-after-init

# Ejecutar pruebas en una base de pruebas existente y autorizada
./odoo-bin -c <config> -d <test_database> -u servincom_account_dashboard \
  --test-enable --test-tags /servincom_account_dashboard --stop-after-init
```

En un servidor con controlador SERVINCOM se debe utilizar su wrapper autorizado y la política vigente de snapshot, sin invocar estos comandos directamente. No crear ni clonar bases para probar sin permiso específico. No ejecutar la suite contable en producción.

## Validación funcional

1. Marcar la casilla de un usuario interno y comprobar ambos cuadros y sus exportaciones.
2. Desmarcarla y comprobar que los enlaces directos y exportaciones se bloquean, incluso con rol de administrador contable.
3. Cambiar 2024/2025/2026 con un usuario de consulta; verificar enero-diciembre, total y acumulado contra el mayor.
4. Plegar y desplegar ambas tablas, recargar y comprobar que se conserva la disposición sin RPC_ERROR.
5. Cambiar de empresa; verificar moneda, datos y exclusiones independientes, e impedir el acceso a empresas no autorizadas.
6. Revisar notas rectificativas, meses sin datos, diarios de cierre y los PDF de las dos tablas.
7. Abrir vencimientos de ventas/compras, revisar una semana y contrastar el pendiente con los apuntes. Probar un documento con varios plazos, una conciliación parcial, una completa, rectificativas y un anticipo sin aplicar.
8. Comprobar filtros, exportación, moneda de empresa y denegación a usuarios sin la casilla.

Las pruebas incluidas cubren permisos, revocación, intentos de autoasignación, cambio de año con lectura, separación de compañías, preferencias de tablero, exportaciones, rectificaciones, partidas residuales, exclusión de diario y borradores. Las pruebas de vencimientos añaden facturas/rectificativas de ambos sentidos, plazos múltiples, conciliaciones parciales/completas, anticipos, borradores, semanas, estados, falta de fecha, moneda extranjera, revocación y reglas adicionales de apuntes. La ejecución real de la suite requiere Odoo y una base de pruebas autorizada. Las comprobaciones estáticas no sustituyen una instalación.

Este repositorio no contiene datos de clientes. Una instalación previa configurada manualmente requiere un script de adopción externo y específico del entorno para conservar sus informes, filtros y usuarios. No debe borrarse esa configuración antes de verificar la adopción.

Autor: **SERVINCOM SOLUCIONES, S.L.** · <https://www.servincom.com>.
