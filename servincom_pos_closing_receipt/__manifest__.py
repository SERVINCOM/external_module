# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "SERVINCOM POS Closing Receipt",
    "version": "16.0.1.0.0",
    "summary": "Improved printed POS closing session receipt",
    "category": "Point of Sale",
    "author": "SERVINCOM SOLUCIONES, S.L.",
    "license": "AGPL-3",
    "depends": [
        "point_of_sale",
    ],
    "data": [],
    "assets": {
        "point_of_sale.assets": [
            "servincom_pos_closing_receipt/static/src/js/closing_receipt_button.js",
            "servincom_pos_closing_receipt/static/src/xml/closing_receipt_templates.xml",
        ],
    },
    "installable": True,
    "application": False,
}
