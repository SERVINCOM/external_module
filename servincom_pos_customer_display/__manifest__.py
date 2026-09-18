# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "SERVINCOM POS Customer Display",
    "summary": "Improved and configurable POS customer-facing display",
    "version": "16.0.1.0.3",
    "category": "Point of Sale",
    "author": "SERVINCOM SOLUCIONES, S.L.",
    "website": "https://www.servincom.com",
    "license": "AGPL-3",
    "depends": [
        "point_of_sale",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "demo": [],
    "assets": {
        "point_of_sale.assets": [
            "servincom_pos_customer_display/static/src/xml/customer_display_templates.xml",
        ],
    },
    "installable": True,
    "application": False,
}
