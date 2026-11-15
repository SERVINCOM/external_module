# Cuadros contables SERVINCOM

Odoo 18 Community · AGPL-3 · SERVINCOM SOLUCIONES, S.L.

Instala tres niveles bajo **Contabilidad → Informes → Cuadro de mando → Resultados mensuales**: **Resumen mensual** (ingresos, compras y gastos, resultado), **Resultados mensuales desglosados** y **Detalle contable de resultados mensuales**. Utiliza MIS Builder y el tablero estándar de Odoo, sin modificar sus fuentes ni depender de Enterprise. **Evolución de clientes** y **Comparativa anual** tienen entradas independientes en la misma sección.

## Uso

En **Ajustes → Usuarios y compañías → Usuarios → Permisos de acceso → Cuadros de mando contables**, marcar **Ver cuadros de mando contables**. La casilla es independiente del rol de administrador contable y solo pueden modificarla los administradores de Ajustes. No se marca automáticamente para ningún usuario al instalar.

En la lista de Usuarios, **Añadir filtro personalizado → Ver cuadros de mando contables → está establecido** permite encontrar a quienes tienen acceso y guardar la búsqueda en Favoritos. La búsqueda consulta directamente la pertenencia al grupo, sin duplicar el permiso en una columna almacenada.

El permiso habilita los resultados, el detalle contable, los vencimientos de ventas/compras, sus exportaciones y la consulta de apuntes. Implica el grupo estándar de contabilidad de solo lectura, por lo que permite consultar también otros datos contables sujetos a las reglas existentes. No concede escritura contable. Desmarcar la casilla bloquea estos cuadros incluso para un administrador contable; no revoca otros permisos contables que el usuario ya tenga. El superusuario de Odoo omite las reglas de registro.

Elegir el año desde el primer cuadro y pulsar **Aplicar año**. Las tres tablas muestran doce meses y total anual. El resumen reutiliza los tres totales MIS de la instancia ya existente, incluidas sus fórmulas y exclusiones; no crea una tercera instancia. El año se guarda por empresa y es compartido: si otra persona lo cambia, se verá el último año aplicado al actualizar. La disposición, plegado y ocultación de tarjetas son personales. Las tablas comparten el desplazamiento vertical del tablero. Al actualizar, el nuevo resumen se inserta una sola vez al principio de cada disposición personal y conserva el plegado existente. El selector funciona con permiso de consulta, sin conceder edición sobre los informes.

## Cálculos y configuración

Las plantillas están destinadas al plan contable español basado en grupos 6 y 7. No son una cuenta de resultados universal para cualquier localización. Ingresos = saldo acreedor del grupo 7; gastos = saldo deudor del grupo 6; resultado = ingresos menos gastos. Se conservan los signos de rectificaciones, se incluyen cuentas residuales y se usan apuntes publicados por fecha contable. El acumulado de meses sin movimientos conserva el saldo anterior y no es una previsión.

Al instalar se crean plantillas e instancias independientes por empresa; para nuevas empresas se crean al abrir el cuadro. No se crean cuentas, facturas ni asientos. Cada empresa conserva su moneda, su ejercicio seleccionado y sus exclusiones.

Antes de usar las cifras, revisar **Contabilidad → Configuración → Configuración de cuadros de mando**, seleccionar los diarios de apertura/cierre que proceda excluir y pulsar **Aplicar diarios excluidos**. No se adivinan códigos de diarios ni se excluyen cierres de TPV. Las plantillas genéricas agrupan las comisiones en 626 y los intereses en 662; no incluyen códigos particulares de un cliente.

Las plantillas XML se cargan con `noupdate=1` para conservar adaptaciones posteriores. Para añadir nuevos cuadros se pueden heredar el modelo, las vistas y las plantillas desde otro addon con una responsabilidad concreta. Se mantienen el análisis de facturación nativo y los dos cuadros de vencimientos. No se añaden presupuestos.

## Comparativa anual

Entrada independiente **Comparativa anual**, con selector de año y mes de corte, totales, gráfico y tabla de doce meses más acumulado. Compara con el ejercicio anterior desde enero hasta el mismo día y mes; el ejercicio actual se limita al día de hoy. El 29 de febrero se compara hasta el 28 de febrero si el año anterior no es bisiesto. Los meses posteriores al corte se muestran sin cifras, sin previsiones. Los porcentajes solo se calculan con una base anterior positiva; para bases cero o negativas se muestra la diferencia monetaria y un guion en el porcentaje.

En Configuración, **Primer año de comparación** se establece inicialmente en el año siguiente a la instalación/actualización. Por ejemplo, al preparar el cuadro en 2026 queda pendiente para 2027 frente a 2026. Un administrador puede ajustarlo cuando haya verificado otro histórico. El cuadro avisa si el periodo aún no ha comenzado o si uno de los periodos no tiene apuntes visibles. Tener movimientos no certifica que el año base esté completo.

El resumen y la comparativa requieren los indicadores técnicos `income_total`, `expenses_total` y `monthly_result`, doce periodos mensuales relativos y un total anual. Reutilizan la instancia MIS y sus filtros; no cambian el año guardado, fechas, fórmulas ni preferencias de los informes originales. Las fórmulas erróneas se notifican, no se convierten en ceros. Los totales de resumen permiten abrir sus apuntes. La comparativa es de consulta; las exportaciones MIS existentes siguen disponibles en los cuadros desglosados.

## Evolución de clientes

Selector de ejercicio, mes de corte y comercial. Compara enero hasta el corte con el mismo periodo del año anterior. Incluye cuatro indicadores, gráfico de clientes únicos por mes, tabla buscable y paginada, filtro por situación y acceso a las facturas que justifican las dos columnas.

El selector de comercial muestra los usuarios asignados a las facturas del periodo consultado. Los activos aparecen primero y los archivados al final, identificados como «Archivado», con orden alfabético dentro de cada grupo. Archivar un usuario no elimina ni reasigna sus facturas: siguen incluidas en «Todos» y pueden consultarse con su filtro. Una cuenta técnica también puede aparecer si está asignada como comercial en documentos de origen.

- Fuente: facturas y rectificativas de cliente publicadas (`account.move`) por fecha de factura, importe sin impuestos con signo y moneda de empresa. Excluye borradores, pedidos sin factura, recibos y ventas TPV sin factura de cliente. No equivale a toda la facturación contable del grupo 7.
- Los contactos se agrupan por `commercial_partner_id`. Activo significa al menos una factura positiva en el periodo; una rectificativa sola no cuenta como compra. Los importes incluyen las rectificativas con su signo incluso en filas sin compra.
- **Con caída de compras**: cliente con compra en ambos periodos cuyo neto disminuye, redondeado a la precisión de la moneda. **Sin compra**: compró en el periodo anterior y no en el actual; no se etiqueta como perdido.
- **Primera compra registrada**: primera factura positiva visible en el histórico dentro del periodo actual. Es una aproximación a cliente nuevo dependiente del histórico importado y de los permisos. **Vuelven a comprar**: tienen compras anteriores, ninguna en el periodo comparado y compra actual.
- **Última compra**: última factura positiva hasta el corte, para toda la empresa y todos sus comerciales. No incorpora facturas posteriores al corte. El filtro de comercial se aplica al comercial asignado a la factura; la primera compra se comprueba sobre todo el histórico visible para no etiquetar como nuevo a un cliente reasignado.
- Los recuentos mensuales son distintos por mes; su suma puede superar el número de clientes activos del periodo. Los clientes con solo rectificativas se identifican aparte. Los porcentajes necesitan una base anterior positiva.
- Se respetan los permisos de facturas, contactos, histórico y compañía activa al consultar importes. El permiso común del cuadro de mando controla también ambos nuevos informes y sus enlaces directos. No se crean facturas, clientes, pagos ni asientos. La comprobación preventiva de solapamiento consulta únicamente si existen facturas, con permisos elevados para que una regla de registros no permita duplicar fuentes; no devuelve importes ni documentos ocultos.

El selector es propio de estos dos cuadros; no modifica el ejercicio compartido del tablero mensual. La búsqueda de clientes se aplica a los resultados agregados y carga 50 filas por página. Los indicadores describen el conjunto consultado, no solo la página visible.

## Navegación y facturación mensual

Desde la versión 18.0.1.4.0, **Evolución de clientes** permite:

- Pulsar las cabeceras del detalle para ordenar por cliente, facturación de cada
  año, diferencia, variación porcentual, última compra o situación. Otra pulsación
  invierte el orden. Los valores no disponibles permanecen al final y la ordenación
  se aplica al conjunto filtrado antes de dividirlo en páginas.
- Ver el rango de clientes, el total de páginas, ir a la primera o última página
  y escribir un número de página. Los filtros y la ordenación vuelven a la primera.
- Marcar los dos años para comparar o dejar solo uno visible. La selección afecta
  a las gráficas, las columnas, los indicadores y los enlaces de documentos.
  Debe quedar al menos un año visible. En vista de un año se incluyen sus clientes
  con documentos, sin exigir que tengan datos del otro año.
- Consultar una gráfica y una tabla de **Facturación neta mensual**, con doce meses
  y acumulado hasta el corte, en moneda de compañía, sin impuestos y neta de abonos.
  **Clientes comparables** suma el mismo grupo de clientes en ambos años y calcula
  diferencia y variación porcentual. **Todos los datos disponibles** muestra las
  sumas visibles de cada año, sin diferencias entre poblaciones distintas. Al
  mostrar solo un año se selecciona este último alcance automáticamente.

El histórico es parcial cuando solo se han cargado coincidencias; sus sumas no
certifican la facturación completa de la empresa de origen. No se incorporan
clientes ni documentos descartados. Se respetan las reglas de facturas, contactos,
histórico, compañía y comercial, y los meses posteriores al corte quedan vacíos.
La búsqueda y el filtro de situación afectan al detalle de clientes; la tabla
mensual conserva el periodo y comercial elegidos. Las notas de alcance aparecen
al pie del informe. Este cuadro no sustituye a la comparativa de resultados
contables, que conserva sus fórmulas y configuración.

Las pruebas de lógica de interfaz pueden ejecutarse sin Odoo:

```sh
node servincom_account_dashboard/tests/test_analysis_frontend.cjs
```

El conjunto de pruebas Odoo incluye agregación mensual con abonos, contactos,
clientes sin coincidencia, permisos, corte temporal y enlaces limitados al año
visible. Deben ejecutarse en una base de prueba existente autorizada antes del
despliegue. Ver los comandos de instalación, actualización y pruebas abajo.

## Histórico estadístico de clientes

Desde la versión 18.0.1.3.0, **Contabilidad → Configuración → Histórico de clientes**
permite a administradores de Ajustes que tengan marcada la casilla de acceso al cuadro preparar lotes anuales de documentos de otro
sistema. Son modelos propios: `servincom.dashboard.history.batch` y
`servincom.dashboard.history.line`. No generan facturas, asientos, impuestos,
conciliaciones ni movimientos de stock, y no alteran el asiento inicial.
El módulo no incluye históricos, clientes reales ni ejercicios predefinidos.

1. Crear un lote en borrador para la compañía y el año, indicar origen, huella del
   archivo, número esperado de documentos e importe neto esperado.
2. Abrir **Documentos** y utilizar la importación estándar de Odoo. Cada fila requiere
   lote (`batch_id`), ID original (`source_key`), número (`name`), fecha ISO
   (`invoice_date`), cliente comercial existente (`partner_id`), tipo
   (`move_type`: `out_invoice` o `out_refund`), neto sin impuestos con signo
   (`amount_untaxed_signed`) y total con signo (`amount_total_signed`). Ambos importes
   deben estar convertidos a la moneda de la compañía antes de la carga.
3. Importar únicamente correspondencias de cliente contrastadas. No se buscan por
   similitud ni se crean contactos automáticamente. `source_customer` y
   `source_salesperson` permiten conservar referencias de origen. `salesperson_id`
   solo se rellena cuando se haya contrastado con un usuario existente.
4. Revisar los totales y pulsar **Validar y activar**. Se exige un único lote por
   compañía y año, claves originales únicas, fechas del ejercicio, clientes
   comerciales de la compañía o compartidos, importes finitos y recuento/neto
   coincidentes con los controles del lote. Un año con facturas o rectificativas
   contabilizadas en la base actual no se puede activar como histórico. Los
   asientos ordinarios, incluido el inicial, no se consideran facturas.
5. Los lotes activos quedan bloqueados para edición. **Volver a borrador** retira
   sus datos de los cuadros y permite corregirlos. Si después se contabilizan
   facturas en el mismo año, el cuadro bloquea la comparación para evitar duplicados.

Los usuarios autorizados al cuadro pueden consultar los documentos históricos
activos de sus compañías; no pueden importarlos ni editarlos. El histórico tiene
reglas propias de registro, distintas de las de facturas. El servicio de análisis
respeta además las restricciones de contactos al mostrar nombres e importes.

Al comparar con un lote de coincidencias, un cliente sin documentos históricos en
el periodo seleccionado muestra **Sin datos comparables** y guiones en la base,
variación y porcentaje. No se le clasifica como nuevo ni como crecimiento desde
cero. El indicador de primera compra pasa a indicar **Sin datos comparables**.
El gráfico se limita a la cohorte con datos comparables; el indicador **Clientes
activos** conserva todos los compradores actuales visibles. Las primeras y últimas
compras siguen limitadas al histórico disponible y a los permisos.

**Ver histórico** abre los registros estadísticos; **Ver facturas** conserva el
acceso a las facturas de esta base. El filtro por comercial solo incluye documentos
históricos con un usuario contrastado; el cuadro avisa de esta limitación.
Los datos históricos de ventas alimentan exclusivamente **Evolución de clientes**,
no la comparativa de beneficios, el resumen mensual, el detalle contable ni los
vencimientos. La información privada se carga por separado en cada base y nunca
se añade a `data/`, `demo/`, pruebas o al repositorio del addon.

## Vencimientos de ventas y compras

En **Contabilidad → Informes → Cuadro de mando**, las entradas **Vencimientos cobros** y **Vencimientos pagos** muestran el pendiente actual por semana. La vista inicial es una tabla dinámica: pulsar un importe abre el detalle; los botones superiores permiten alternar tabla, lista y gráfico. Se pueden descargar los datos y guardar filtros personales mediante las funciones estándar de Odoo.

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
9. Contrastar las tres filas del resumen con los totales de los informes existentes. Verificar su inserción inicial, plegado y desplazamiento sin restaurar tarjetas que el usuario oculte después.
10. En comparativa, comprobar el aviso previo al primer ejercicio, el corte equivalente, ausencia de previsiones y porcentajes sin base positiva. Comprobar que consultar otro año no cambia el año del tablero mensual.
11. En evolución, contrastar facturas y rectificativas, contactos del mismo cliente, filtro de comercial, clientes sin compra, primera compra registrada, fechas límite, meses sin datos, búsqueda, paginación y acceso a facturas.
12. Probar un lote ficticio: borrador invisible para lectores, activación con totales correctos, rechazo de duplicados/solapamientos, consulta del histórico y guiones para clientes sin coincidencia. Verificar el mismo corte de fechas y que los asientos iniciales conservan sus importes.

Las pruebas incluidas cubren permisos, revocación, intentos de autoasignación, cambio de año con lectura, separación de compañías, preferencias de tablero, exportaciones, rectificaciones, partidas residuales, exclusión de diario y borradores. Las pruebas de vencimientos añaden facturas/rectificativas de ambos sentidos, plazos múltiples, conciliaciones parciales/completas, anticipos, borradores, semanas, estados, falta de fecha, moneda extranjera, revocación y reglas adicionales de apuntes. La ejecución real de la suite requiere Odoo y una base de pruebas autorizada. Las comprobaciones estáticas no sustituyen una instalación.

Este repositorio no contiene datos de clientes. Una instalación previa configurada manualmente requiere un script de adopción externo y específico del entorno para conservar sus informes, filtros y usuarios. No debe borrarse esa configuración antes de verificar la adopción.

Autor: **SERVINCOM SOLUCIONES, S.L.** · <https://www.servincom.com>.
