# SERVINCOM — Libro de IGIC

Módulo de **SERVINCOM SOLUCIONES, S.L.** para **Odoo 18 Community**.
Licencia **AGPL-3.0 o posterior**. Web: https://www.servincom.com.

Amplía `l10n_es_vat_book` de OCA, sin modificar Odoo ni los módulos de OCA.
Genera libros de facturas emitidas y recibidas con IGIC, rectificativas,
resumen por impuesto, PDF A4 horizontal y Excel con dos hojas.

## Dependencias y compatibilidad

- `l10n_es_vat_book` de `OCA/l10n-spain`, rama `18.0`.
- `report_xlsx` de `OCA/reporting-engine`, rama `18.0`.
- Sus dependencias, incluidas `l10n_es_aeat`, `account` y `l10n_es`.
- Odoo 18 actualizado con el plan contable canario oficial. **No instalar el
  antiguo `l10n_es_igic` de Odoo 16 ni cambiar el plan contable de una empresa
  que ya tiene movimientos para instalar este módulo.**

Compatible también con `l10n_es_vat_book` **18.0.2.1.2** y
`l10n_es_aeat` **18.0.1.3.8**, sin campo de equivalencias AEAT.
La versión **18.0.1.0.1** incorpora un equivalente IGIC propio para estos entornos.

El código se ha contrastado además con `l10n_es_vat_book` **18.0.2.2.1**:

- OCA/l10n-spain: `c60280bf92b242659ab5349858a1e789bd8a5c41`.
- Odoo/odoo 18.0: `50f3762a21d9cd960545a1a62c02a3b353598665`.

Antes de instalar, revisar la versión efectiva de los módulos en el servidor.
No necesita Enterprise, envío telemático, certificados ni modelos 420/425.
`l10n_es_vat_book_pos` es opcional si se necesita la adaptación OCA de operaciones
TPV sin cliente. Su combinación requiere validación específica en la base de pruebas.

## Qué incluye

- Menú **Contabilidad → Declaraciones → Libros de IGIC**.
- Mapeos explícitos para las 76 plantillas del fichero canario oficial revisado:
  tipos generales, cero, exentos, no sujetos, bienes de inversión, importaciones,
  inversión del sujeto pasivo, recargos y grupos DUA.
- Equivalencias personalizadas mediante **Impuesto IGIC equivalente**, o el
  campo OCA **Impuesto equivalente (para mapeo AEAT)** cuando esté disponible;
  se incluyen equivalentes archivados.
- Cálculo sobre apuntes **contabilizados**, por **fecha contable**, en moneda de
  la compañía y limitado a la compañía del libro.
- Rectificativas con signo negativo; exclusión de la contrapartida negativa de
  autorrepercusión para que no anule el IGIC soportado.
- En impuestos agrupados se utiliza el IGIC hijo y se excluye el ajuste auxiliar
  de base de las importaciones DUA.
- Porcentaje deducible configurable por impuesto de compra. No modifica asientos,
  cuentas, etiquetas fiscales ni posiciones fiscales.
- Los mapas IGIC se activan únicamente al calcular libros IGIC. Los libros IVA
  conservan sus mapas y sus exportaciones OCA.
- Icono corporativo SERVINCOM; el PDF utiliza el logo y los datos de la empresa
  titular del libro, también en el pie del PDF y del Excel.

## Configuración inicial

1. En una **copia de pruebas**, verificar el plan y los impuestos realmente usados.
   Los mapeos funcionan con los identificadores externos oficiales de Odoo 18.
2. Si un impuesto se creó manualmente o viene de una migración, configurar su
   **Impuesto IGIC equivalente** de la **misma compañía**. No se emparejan por nombre ni
   por porcentaje: un impuesto no mapeado queda fuera del libro.
3. En cada impuesto de compra, revisar **Porcentaje deducible de IGIC**:
   100 por defecto; 0 para cuotas no deducibles; otro valor para deducción parcial.
   Revisar expresamente recargos y regímenes especiales. El módulo no determina
   automáticamente el derecho fiscal a deducir.
4. Crear el libro desde el menú Libros de IGIC, elegir compañía, año y periodo, y
   pulsar **Calcular**. Los campos de identificación/contacto siguen siendo los
   del modelo OCA.
5. Revisar avisos y cuadrar los importes con la contabilidad; después exportar
   **PDF de IGIC** y **Excel de IGIC**. Confirmar el libro para quitar el rótulo
   de borrador. Recalcular después de corregir impuestos o deducibilidad.
6. Para otra compañía o periodo, crear un libro nuevo. No se permite cambiar
   la compañía, periodo o tipo de un libro que ya tenga líneas calculadas.

## PDF y Excel

Ambos formatos utilizan el mismo detalle calculado. Incluyen número de orden,
fecha de factura, referencias, tercero, NIF, impuesto, porcentaje, base, cuota
IGIC/recargo y cuota deducible en recibidas. Excel añade fecha contable, cuota
no deducible y avisos, con filtros, paneles inmovilizados y celdas numéricas.

Los resúmenes muestran bases **por impuesto**; IGIC y recargo pueden compartir
base. El total general cuenta cada base contable una sola vez. La cuota total
incluye los recargos mostrados. No se presenta como total de factura: una factura
puede contener retenciones, IVA u operaciones ajenas al IGIC.

El número de orden del informe agrupa las filas de un mismo documento. No
sustituye al número original de factura. En las operaciones que OCA agrupa por
asiento (por ejemplo, determinados cierres TPV), representa el asiento agrupado.

**Son informes contables para revisión y asesoría, no un fichero oficial de
presentación ante la ATC ni un libro SII.** El Excel propio conserva los datos
y los rótulos IGIC; no reutiliza el formato BOE del libro IVA. No certifica
cumplimiento de un requerimiento administrativo concreto.

## Seguridad

Reutiliza el modelo y el grupo OCA `l10n_es_aeat.group_account_aeat`.
No crea modelos persistentes nuevos ni amplía ACL: por eso no añade un CSV de
permisos. Añade reglas de compañía para las líneas, cuotas y resúmenes IGIC.
Las acciones de informe comprueban acceso y estado calculado/confirmado.
El Excel escribe las referencias, NIF y nombres como texto, sin fórmulas.

## Instalación y actualización

Ejemplos para un entorno de prueba, adaptando rutas y nombre real de la base.
No ejecutar contra una base real sin copia/snapshot y validación previa.

Primera instalación:

```bash
./odoo-bin -c <config> -d <base_pruebas> -i servincom_igic_book --stop-after-init
```

Actualizaciones posteriores:

```bash
./odoo-bin -c <config> -d <base_pruebas> -u servincom_igic_book --i18n-overwrite --stop-after-init
```

En instalaciones anteriores, `--i18n-overwrite` recarga las traducciones del
módulo y sustituye el antiguo nombre traducido del menú. Revisar antes cualquier
traducción personalizada que se quiera conservar. Reiniciar Odoo para renovar
la caché de traducciones Python y recargar el navegador.

Pruebas automatizadas (usar una base desechable):

```bash
./odoo-bin -c <config> -d <base_pruebas_desechable> -i servincom_igic_book --test-enable --test-tags /servincom_igic_book --stop-after-init
```

## Pruebas funcionales mínimas

- Venta de base 100 con IGIC 7 %: base 100 y cuota 7; compra equivalente: mismos
  importes, con deducción según su configuración.
- Rectificativas de venta y compra: signo negativo y resumen neto correcto.
- Tipos 0 %, exentos, varios tipos en un periodo y en una factura; ninguna
  factura en borrador ni fuera de periodo debe entrar.
- Factura con IVA y factura mixta: incluir solo bases/cuotas IGIC; comprobar
  que el libro IVA mantiene su comportamiento previo.
- Compra con ISP: cuota positiva soportada, sin quedar anulada por su contraparte.
- Importación DUA: base y cuota, sin el impuesto auxiliar negativo.
- IGIC más recargo: dos líneas fiscales pero una sola base en el total.
- Impuesto manual equivalente archivado y compra total/parcialmente no deducible.
- Dos compañías activas: sin mezcla de apuntes ni acceso a líneas de otra empresa.
- PDF de varias páginas: cabeceras, referencias largas, logo, totales y pie;
  abrir Excel y comparar ambos formatos con el libro y la contabilidad.
- Recalcular: sin duplicados. Confirmar: sin avisos pendientes.

Las pruebas ORM de `tests/` cubren los casos principales y la exportación HTML/
XLSX. El 29 de septiembre de 2026 se verificaron en una base de pruebas Odoo 18
la instalación, la actualización a 18.0.1.0.1, el cálculo de un periodo sin avisos,
el renderizado HTML en español y la generación de las dos hojas Excel.
Los libros temporales se descartaron con rollback.

En la versión 18.0.1.0.2 se verificaron en Odoo las traducciones del menú, los
estados y las selecciones heredadas, así como los títulos, las hojas y las
cabeceras Excel y el pie con la empresa del libro. La exportación HTML y Excel
conserva los importes del libro existente. El fichero PO incluye la marca
`odoo-python` necesaria para las traducciones de código en Odoo 18.

También se comprobaron las descargas reales desde Odoo: cabeceras y hojas del
Excel en español, valores numéricos sin cambios y revisión visual de la primera
y última página del PDF generado con wkhtmltopdf.

Quedan pendientes la ejecución completa de la suite ORM y la conciliación de
todos los casos fiscales.
La prueba de exportación desde shell debe incluir `active_model` y `active_ids`,
igual que el contexto del botón de Odoo.

## Créditos

Desarrollo y mantenimiento: **SERVINCOM SOLUCIONES, S.L.**
Motor del libro y modelos de base: **Odoo Community Association (OCA)**.
Mapeos basados en los identificadores del plan canario oficial de Odoo 18.
