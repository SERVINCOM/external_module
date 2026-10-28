.. code-block:: bash

    ./odoo-bin -c <config> -d <base_existente> -i servincom_product_attribute_value_sequence --stop-after-init
    ./odoo-bin -c <config> -d <base_existente> -u servincom_product_attribute_value_sequence --stop-after-init

Para pruebas, use una base de pruebas existente y autorizada:

.. code-block:: bash

    ./odoo-bin -c <config> -d <base_pruebas_existente> -u servincom_product_attribute_value_sequence --test-enable --test-tags /servincom_product_attribute_value_sequence --stop-after-init
