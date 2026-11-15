# Cuadros contables SERVINCOM

Odoo 18 Community · AGPL-3 · SERVINCOM SOLUCIONES, S.L.

Instala un resumen mensual y un detalle por cuentas bajo **Contabilidad → Informes → Informes de contabilidad OCA → Cuadros de mando**. Utiliza MIS Builder y el tablero estándar de Odoo, sin modificar sus fuentes ni depender de Enterprise.

## Uso

En **Ajustes → Usuarios y compañías → Usuarios → Permisos de acceso → Cuadros de mando contables**, marcar **Ver cuadros de mando contables**. La casilla es independiente del rol de administrador contable y solo pueden modificarla los administradores de Ajustes. No se marca automáticamente para ningún usuario al instalar.

El permiso habilita ambos informes, sus exportaciones y la consulta de apuntes. Implica el grupo estándar de contabilidad de solo lectura, por lo que permite consultar también otros datos contables sujetos a las reglas existentes. No concede escritura contable. Desmarcar la casilla bloquea estos cuadros incluso para un administrador contable; no revoca otros permisos contables que el usuario ya tenga. El superusuario de Odoo omite las reglas de registro.

Elegir el año desde el primer cuadro y pulsar **Aplicar año**. Los dos informes muestran doce meses y total anual. El año se guarda por empresa y es compartido: si otra persona lo cambia, se verá el último año aplicado al actualizar. La disposición, plegado y ocultación de tarjetas son personales. El selector funciona con permiso de consulta, sin conceder edición sobre los informes.

## Cálculos y configuración

Las plantillas están destinadas al plan contable español basado en grupos 6 y 7. No son una cuenta de resultados universal para cualquier localización. Ingresos = saldo acreedor del grupo 7; gastos = saldo deudor del grupo 6; resultado = ingresos menos gastos. Se conservan los signos de rectificaciones, se incluyen cuentas residuales y se usan apuntes publicados por fecha contable. El acumulado de meses sin movimientos conserva el saldo anterior y no es una previsión.

Al instalar se crean plantillas e instancias independientes por empresa; para nuevas empresas se crean al abrir el cuadro. No se crean cuentas, facturas ni asientos. Cada empresa conserva su moneda, su ejercicio seleccionado y sus exclusiones.

Antes de usar las cifras, revisar **Contabilidad → Configuración → Configuración de cuadros de mando**, seleccionar los diarios de apertura/cierre que proceda excluir y pulsar **Aplicar diarios excluidos**. No se adivinan códigos de diarios ni se excluyen cierres de TPV. Las plantillas genéricas agrupan las comisiones en 626 y los intereses en 662; no incluyen códigos particulares de un cliente.

Las plantillas XML se cargan con `noupdate=1` para conservar adaptaciones posteriores. Para añadir nuevos cuadros se pueden heredar el modelo, las vistas y las plantillas desde otro addon con una responsabilidad concreta. Facturas de venta, comparativas, presupuestos y vencimientos no forman parte de esta versión.

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

Las pruebas incluidas cubren permisos, revocación, intentos de autoasignación, cambio de año con lectura, separación de compañías, preferencias de tablero, exportaciones, rectificaciones, partidas residuales, exclusión de diario y borradores. La ejecución real de la suite requiere Odoo y una base de pruebas autorizada. Las comprobaciones estáticas no sustituyen una instalación.

Este repositorio no contiene datos de clientes. Una instalación previa configurada manualmente requiere un script de adopción externo y específico del entorno para conservar sus informes, filtros y usuarios. No debe borrarse esa configuración antes de verificar la adopción.

Autor: **SERVINCOM SOLUCIONES, S.L.** · <https://www.servincom.com>.
