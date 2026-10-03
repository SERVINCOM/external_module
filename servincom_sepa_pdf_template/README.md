# SERVINCOM SEPA PDF Template

Módulo reutilizable de **SERVINCOM SOLUCIONES, S.L.** para **Odoo 18 Community**, AGPL-3.
Repositorio público `SERVINCOM/external_module`, rama `18.0`.

Genera mandatos a partir de formularios PDF AcroForm que se configuran por empresa y
por esquema CORE/B2B. No requiere modificar QWeb, módulos OCA ni el código de Odoo.

## Dependencias y entorno comprobado

- `account_banking_sepa_direct_debit` de OCA/bank-payment, rama 18.0.
- `account_banking_mandate` y `account_banking_pain_base`: dependencias transitivas OCA.
- Python: `pypdf`, declarado en `external_dependencies`. Versión probada: **6.10.0**.
  Se comprueba la disponibilidad real de `flatten` y `remove_annotations` antes de
  validar un modelo. Una versión sin esos métodos no permite activar el modelo.
- No se necesita reportlab ni otra dependencia Python para ejecutar el módulo.
  Los PDF de ejemplo ya están preparados; se crearon fuera del módulo con reportlab.

En la revisión local no se ha encontrado una instalación ejecutable de Odoo ni los
addons OCA de banca dentro de los repositorios locales inspeccionados. Se han
contrastado modelos, vistas, informe y plantilla de correo con las fuentes oficiales
18.0. **No se ha consultado una base de datos ni se ha instalado en ningún servidor.**
El Python del sistema tampoco tiene pypdf; las pruebas usan el runtime de Codex con
pypdf 6.10.0. Comprobar la versión en el Python que ejecuta Odoo antes de instalar.

## Configuración

1. Seleccione la empresa y vaya a **Contabilidad → Configuración → Ajustes →
   Mandatos SEPA → Modelo PDF personalizado para mandatos SEPA**.
2. Cargue el formulario CORE y/o B2B y su nombre de archivo. Los modelos se guardan
   en `res.company` con `attachment=True`; no son parámetros globales compartidos.
3. Pulse **Validar modelo PDF**. Este botón guarda únicamente la configuración SEPA
   de la empresa y registra resultado, fecha y usuario internamente. Solo se muestra
   un aviso automático al subir o sustituir un archivo, nunca al abrir Ajustes.
   Una validación correcta muestra una confirmación breve; los errores indican
   únicamente los requisitos incumplidos. No se muestran listados técnicos en Ajustes.
4. Pulse **Previsualizar mandato**, seleccione un mandato de esa empresa y revise
   empresa, esquema y archivo. El botón guarda la configuración SEPA y abre un
   asistente que genera una descarga sin enviar correo. Se puede previsualizar un
   modelo válido antes de activarlo.
5. Active el modelo personalizado y guarde. Todos los modelos cargados deben ser
   válidos; basta tener un esquema configurado. El esquema que no tenga archivo usa
   el informe original OCA. Para guardar un archivo incompatible y ver su diagnóstico,
   mantenga desactivada la configuración.

Solo responsables de contabilidad (`account.group_account_manager`) o administradores
(`base.group_system`) pueden configurar modelos. El servidor comprueba el grupo y
la empresa permitida, además de las restricciones de campos y vistas. La elevación
necesaria para escribir `res.company` se limita a los cinco campos de configuración.
Los usuarios que ya puedan imprimir mandatos mantienen ese acceso; la lectura
interna del modelo se limita a la empresa del mandato después de comprobar permisos.
El asistente tiene ACL de responsables/administradores y regla multiempresa.

## Preparar un formulario compatible

Use un editor que pueda crear y conservar **AcroForm**. Un documento exportado desde
Word o un PDF impreso normalmente será plano y no sirve. El módulo nunca busca
coordenadas automáticamente. Cree los controles sobre su propio diseño.

- PDF sin cifrar ni firmar, sin XFA, de hasta 10 MiB y 20 páginas.
- Un control visible por nombre obligatorio; no use nombres duplicados, jerarquías
  con prefijos, widgets huérfanos ni campos ocultos.
- Los campos de texto usan `/Tx`. Configure fuente compatible con los caracteres
  que vaya a imprimir y tamaño automático o suficiente espacio; revise nombres y
  direcciones largos en la previsualización.
- Las dos casillas deben ser `/Btn` de tipo checkbox, con apariencia `/Off` y un
  único estado marcado (por ejemplo `/Yes`). No sirven botones de radio.
- `debtor_signature`: cuadro de texto vacío o campo `/Sig` sin firmar. El resultado
  se aplana y deja la zona de firma vacía, sin conservar un campo de firma digital.
  El cliente puede firmar en papel o con una herramienta externa. El modelo no debe
  llevar una firma dibujada en el fondo.
- Los campos desconocidos se enumeran, no se rellenan con datos del mandato y se
  vacían en el resultado. No se reparan automáticamente formularios ambiguos.
- Conserve el PDF original editable: el módulo nunca lo sobrescribe. El PDF generado
  tiene los datos pintados sobre la página, sin widgets ni árbol AcroForm.

Nombres exactos, distinguiendo mayúsculas y minúsculas:

| Campo AcroForm | Datos de Odoo |
| --- | --- |
| `mandate_reference` | `unique_mandate_reference` |
| `creditor_identifier` | `company_id.sepa_creditor_identifier` |
| `creditor_name` | `company_id.name` |
| `creditor_address` | `company_id.partner_id.street` y `street2` |
| `creditor_postal_city_state` | Código postal, localidad y provincia del acreedor |
| `creditor_country` | País del acreedor |
| `debtor_name` | `partner_id.name` |
| `debtor_address` | `partner_id.street` y `street2` |
| `debtor_postal_city_state` | Código postal, localidad y provincia del deudor |
| `debtor_country` | País del deudor |
| `debtor_bic` | `partner_bank_id.bank_bic` |
| `debtor_iban` | `partner_bank_id.acc_number` |
| `payment_recurrent` | Casilla marcada si `type == "recurrent"` |
| `payment_oneoff` | Casilla marcada si `type == "oneoff"` |
| `date_location` | `signature_date` y `sepa_signature_city`; vacío si falta cualquiera |
| `debtor_signature` | Siempre vacío |

OCA 18.0 dispone de fecha de firma pero no de localidad de firma. Este módulo añade
`sepa_signature_city` junto a `signature_date` en el formulario del mandato; no
supone que la localidad de firma sea la dirección fiscal del deudor.

## Ejemplos corporativos

- `examples/mandato_sepa_core.pdf`: AcroForm CORE vacío, A4 de una página.
- `examples/mandato_sepa_b2b.pdf`: AcroForm B2B vacío, A4 de una página.
- `examples/mandato_sepa_demo_cumplimentado.pdf`: resultado estático con datos
  inventados; no sirve como plantilla rellenable y no debe usarse como mandato real.
- `examples/servincom_logo.jpg`: logotipo original extraído de la muestra aportada.
- `static/description/icon.png`: icono corporativo original del workspace.

Para adaptar otro cliente, abra una copia del formulario vacío, sustituya logotipo,
colores, títulos y textos de fondo en el editor PDF, y conserve los nombres técnicos
y tipos de los 16 campos. Puede cambiar el tamaño y posición de los controles.
Guarde conservando el formulario, valide en Odoo y previsualice datos representativos.
No seleccione imprimir como PDF ni aplanar al guardar la plantilla.

La muestra aportada era plana y contenía datos reales: no se ha incorporado al
repositorio ni se han copiado esos datos en los ejemplos. Solo se reutiliza el logo
corporativo y la referencia visual. Los textos CORE y B2B son distintos: B2B no
ofrece reembolso de adeudos autorizados. Los ejemplos son modelos de preparación;
confirme con su entidad el texto y requisitos aplicables antes de uso real.

Referencia oficial: [mandatos SEPA del EPC](https://www.europeanpaymentscouncil.eu/what-we-do/epc-payment-schemes/sepa-direct-debit/sdd-mandate).

## Informe y correo

Únicamente se intercepta la acción
`account_banking_sepa_direct_debit.report_sepa_direct_debit_mandate`.
Se compara su ID real, no un patrón de nombres ni todos los informes del modelo.
La herencia actúa en `_render_qweb_pdf_prepare_streams`: genera cada mandato según
su empresa/esquema y permite mezclar en un lote PDFs personalizados y originales.
Si un modelo se corrompe se registra una advertencia sin datos bancarios y se llama
al informe OCA para ese mandato. Los errores de permisos nunca se silencian.
El respaldo no puede solucionar una avería independiente del informe OCA o wkhtmltopdf.

La plantilla de correo OCA ya incluye esa acción en `report_template_ids`. Odoo
llama al mismo motor para generar el adjunto dinámico; no se añade ningún adjunto
estático ni se cambia el cuerpo o destinatarios del correo. Las plantillas propias
deben asociar el mismo informe en sus informes dinámicos.

Nombre individual: `Mandato-<referencia>-<cliente>.pdf`, con caracteres de ruta
saneados. En impresión múltiple Odoo utiliza el nombre habitual del lote.
El hook de instalación guarda la expresión previa de nombre del informe y la
sustituye; el hook de desinstalación la restaura si sigue siendo la de este módulo.
Las vistas QWeb y archivos OCA permanecen intactos.

## Instalación y actualización (ejemplos, no ejecutados)

Primero compruebe los addons OCA en la rama 18.0 y el Python del proceso Odoo:

```bash
<python_de_odoo> -c "import pypdf; print(pypdf.__version__)"
```

Si falta la dependencia, instálela en ese entorno virtual mediante el procedimiento
de despliegue autorizado; la versión de referencia es `pypdf==6.10.0`.

Instalar en una base de pruebas:

```bash
./odoo-bin -c <config> -d <database_test> -i servincom_sepa_pdf_template --stop-after-init
```

Actualizar un módulo ya instalado:

```bash
./odoo-bin -c <config> -d <database_test> -u servincom_sepa_pdf_template --stop-after-init
```

Ejecutar las pruebas de integración en esa base con OCA y sus dependencias:

```bash
./odoo-bin -c <config> -d <database_test> -i servincom_sepa_pdf_template --test-enable --test-tags /servincom_sepa_pdf_template --stop-after-init
```

Pruebas del motor sin Odoo, desde la carpeta del módulo:

```bash
python -m unittest discover -s tests -p test_pdf_engine.py -v
```

No ejecutar sobre una base real sin copia/snapshot confirmado. No hay migraciones
ni cambios en mandatos existentes; los modelos personalizados comienzan desactivados.
Se modifica la expresión del nombre del informe SEPA durante la instalación.

## Pruebas y límites de la entrega

Véase `VALIDATION.md` para el resultado exacto y las comprobaciones pendientes.
Las pruebas de integración preparadas cubren selección multiempresa/CORE/B2B,
mapa de datos, fecha/localidad, activación, auditoría, generación dinámica de correo,
respaldo al informe original, corrupción, otros informes, permisos y previsualización.
No se han ejecutado sin Odoo: un chequeo Python/XML no equivale a una instalación.

Pruebas funcionales mínimas en una base duplicada:

1. Validar ambos ejemplos y rechazar un PDF plano, otro incompleto y un archivo falso.
2. Imprimir CORE recurrente y B2B único; comprobar referencia, acreedor, deudor,
   IBAN/BIC, casillas, ñ/tildes, una página y firma vacía. Probar textos largos.
3. Alternar dos empresas con modelos distintos y usuarios con acceso limitado.
4. Comprobar que un usuario contable sin permisos de responsable no cambia modelos.
5. Previsualizar con la opción desactivada; comprobar empresa, esquema y nombre.
6. Abrir el compositor de correo y revisar el PDF dinámico sin enviar mensajes reales.
7. Desactivar o dejar sin modelo un esquema: debe imprimirse el informe original.
8. Verificar el respaldo ante corrupción mediante el test automatizado de integración.
9. Imprimir una factura y un presupuesto y verificar que no han cambiado.
10. Abrir el resultado en Vista Previa, navegador y lector PDF habitual. Probar también
    actualización y desinstalación en la copia para comprobar la restauración del nombre.

## Archivos

`pdf_form.py` contiene el motor independiente. `models/` añade configuración, mapa de
datos y herencia del informe. `wizard/` y `security/` implementan previsualización y
permisos. `views/` contiene las vistas heredadas. `hooks.py` gestiona el nombre del
informe. `i18n/es.po` traduce todos los textos añadidos. `tests/`, `examples/` y
`VALIDATION.md` permiten revisar y reproducir la entrega.

## Autor y licencia

SERVINCOM SOLUCIONES, S.L. · https://www.servincom.com · AGPL-3.
