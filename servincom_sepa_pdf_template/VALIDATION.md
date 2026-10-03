# Validación local — 2 de octubre de 2026

## Comprobaciones superadas

- 13/13 pruebas del motor PDF con pypdf 6.10.0.
- Ruff: imports, errores Python y formato; F401 excluido solo en __init__.py.
- Sintaxis Python, XML, rutas del manifest, dependencias y XPath OCA 18.0.
- 39 traducciones, sin duplicados ni entradas vacías o fuzzy.
- Icono corporativo original y ausencia de bytecode generado.
- CORE/B2B: una página A4 y 16 campos por formulario.
- PDF cumplimentado: datos ficticios visibles, firma vacía, sin AcroForm ni widgets.
- Original conservado. Casillas recurrente/único comprobadas por apariencia pintada.
- Renderizado Poppler y revisión visual sin cortes ni superposiciones; fecha corregida.
  Poppler emitió un aviso de fontconfig, pero generó los PNG correctamente.

## Pendiente

Las pruebas de integración de Odoo están preparadas pero no ejecutadas: no hay
Odoo ejecutable ni addons bancarios OCA en los repositorios locales inspeccionados.
No se ha confirmado qué dependencias están instaladas en una base de datos ni
la versión de pypdf del Python de un servidor Odoo.

Falta comprobar instalación, actualización, vistas, ACL, multiempresa, compositor
de correo, respaldo OCA y desinstalación en una base de pruebas.
No se ha conectado ni instalado nada en servidores.

La herramienta de escritorio no arranca por el enlace simbólico del workspace.
La apertura en Vista Previa, navegador y lector habitual sigue pendiente.
Poppler y pypdf sí han procesado los PDF correctamente.

## Git

Repositorio público: SERVINCOM/external_module (checkout local de Odoo 18.0).
Rama 18.0, remote https://github.com/SERVINCOM/external_module.git.

Último estado comprobado:

```text
?? account_invoice_triple_discount/
?? docs/
?? servincom_sepa_pdf_template/
```

Sin modificaciones de archivos versionados ni staging. El diff normal está vacío
porque el módulo es nuevo y no tiene seguimiento; su contenido se revisó directamente.
No se ha hecho commit ni push. Se han conservado los cambios ajenos.

Antes de producción, ejecutar las pruebas y la lista funcional del README en una
base duplicada, confirmar el texto con la entidad y disponer de copia/snapshot.
