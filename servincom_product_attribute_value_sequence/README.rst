Product Attribute Value Sequence
================================

.. Generated from the fragments in readme/.

Odoo Community 18.0 · SERVINCOM SOLUCIONES · AGPL-3.

Permite arrastrar los valores desde **Producto → Atributos y variantes →
Configurar**. Escribe la secuencia del valor compartido: el cambio afecta a
TODOS los productos que usan ese valor. También puede editarse el número
**Secuencia global** en la ficha del valor.

Los selectores estándar de Odoo (incluida la web cuando website_sale está
instalado) leen ese orden compartido. No se requiere website_sale para instalar.
El botón **Variantes** del producto abre una lista ordenada por las líneas de
atributos del producto y, dentro de ellas, por la secuencia global de valores.
El listado general de productos conserva su orden habitual. Un orden manual
por encabezado de columna puede sustituir temporalmente el orden inicial.

El arrastre mueve los valores visibles. Los valores no incluidos en ese producto
no aparecen en esa pantalla; para revisar el orden completo de un atributo,
utilice Configuración → Atributos. Los empates se resuelven por ID, como en Odoo.
No se crean, eliminan ni regeneran variantes al cambiar la secuencia. No se
modifican referencias, existencias, precios ni el modo de creación de variantes.
No se amplían permisos: se usan los permisos existentes de producto/atributos.

Installation
------------

.. code-block:: bash

    ./odoo-bin -c <config> -d <base_existente> -i servincom_product_attribute_value_sequence --stop-after-init
    ./odoo-bin -c <config> -d <base_existente> -u servincom_product_attribute_value_sequence --stop-after-init

Para pruebas, use una base de pruebas existente y autorizada:

.. code-block:: bash

    ./odoo-bin -c <config> -d <base_pruebas_existente> -u servincom_product_attribute_value_sequence --test-enable --test-tags /servincom_product_attribute_value_sequence --stop-after-init

Usage
-----

1. Elegir dos productos que compartan valores del mismo atributo.
2. En Configurar, arrastrar un valor y volver a abrir ambas fichas.
3. Comprobar que ambos muestran el nuevo orden y conservan sus variantes e IDs.
4. Abrir Variantes y comprobar el orden de las combinaciones con dos atributos.
5. Recargar las fichas web públicas y comprobar sus selectores.
6. Cambiar la secuencia también desde Configuración → Atributos; comprobar ambos
   productos de nuevo. Probar con permisos de un usuario operativo habitual.

Known issues / Roadmap
----------------------

La instalación añade dos campos almacenados y calcula la clave de orden para
las variantes existentes. El coste depende del catálogo. Validar primero en
una base de pruebas autorizada. Las personalizaciones de la web pueden imponer
otro orden y requieren validación en navegador. Desinstalar retira la interfaz
y la clave de orden; las secuencias globales que haya cambiado el usuario se
conservan en el campo nativo de Odoo.

Credits
-------

Desarrollado y mantenido por SERVINCOM SOLUCIONES, S.L.
https://www.servincom.com

Licencia GNU Affero General Public License v3 (https://www.gnu.org/licenses/agpl-3.0.html).
Estructura y convenciones OCA; este módulo pertenece al repositorio de SERVINCOM.
No introduce modelos nuevos ni requiere ampliar las ACL existentes.
