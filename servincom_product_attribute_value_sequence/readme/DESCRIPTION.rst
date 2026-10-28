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
