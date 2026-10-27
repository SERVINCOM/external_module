# Sale Configurator Existing Variants

Odoo Community 18.0 · SERVINCOM SOLUCIONES, S.L. · AGPL-3

El configurador de presupuestos carga todos los valores de la plantilla incluso
cuando se han eliminado algunas combinaciones. Este addon muestra únicamente
opciones compatibles con variantes activas existentes para productos de creación
inmediata. No utiliza las existencias como criterio.

Los atributos se resuelven en el orden configurado: al cambiar el tipo de pieza,
las capacidades/medidas posteriores se ajustan a una combinación válida y se
actualizan referencia, imagen y precio mediante el RPC nativo. La confirmación
se bloquea mientras se procesa el cambio. Los productos dinámicos y combos
conservan su comportamiento nativo. Las exclusiones y los productos opcionales
siguen utilizando la lógica de Odoo.

## Alcance

- Herencia del modelo mediante el hook nativo de datos del configurador;
  extensiones Owl/XML en web.assets_backend. El hook se limita a las rutas
  del configurador de Ventas para coexistir con website_sale.
- Dependencia única: sale. Sin modelos, permisos ni campos persistentes nuevos.
- No modifica productos, stock, precios, pedidos ni la tienda web.
- No impide la regeneración nativa de combinaciones al editar atributos de una
  plantilla: este módulo se limita al configurador de Ventas.
- La matriz se obtiene al abrir el diálogo. Si se modifica el catálogo durante
  una sesión, volver a abrirlo para cargar sus cambios.

## Instalación y pruebas

```sh
./odoo-bin -c <config> -d <database> -i servincom_sale_configurator_existing_variants --stop-after-init
./odoo-bin -c <config> -d <database> -u servincom_sale_configurator_existing_variants --stop-after-init
node --test tests/combinations.test.mjs
```

Ejecutar las pruebas Odoo solamente en una base de prueba existente y autorizada:

```sh
./odoo-bin -c <config> -d <test_database> -i servincom_sale_configurator_existing_variants --test-enable --test-tags /servincom_sale_configurator_existing_variants --stop-after-init
```

Validación funcional: plantilla con dos tipos y capacidades disjuntas; cambiar
en ambos sentidos, comprobar referencias/precios, editar una línea existente,
verificar cantidades y cambios rápidos. Comprobar también producto simple,
producto dinámico, selección/lista/píldoras, exclusiones y opcionales. No enviar
ni confirmar pedidos durante las pruebas.

Destino previsto: SERVINCOM/external_module, rama 18.0, addon en la raíz del
repositorio. Desplegar con el controlador del servidor tras autorización de
commit/push e instalación y snapshot confirmado. Desinstalar revierte únicamente
el comportamiento del configurador; los datos comerciales permanecen intactos.
