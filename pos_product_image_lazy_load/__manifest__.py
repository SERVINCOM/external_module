# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "POS Product Image Lazy Loading",
    "summary": "Load POS product images only when they approach the visible area",
    "version": "18.0.1.0.0",
    "category": "Point of Sale",
    "author": "SERVINCOM SOLUCIONES, S.L.",
    "website": "https://www.servincom.com",
    "license": "AGPL-3",
    "depends": ["point_of_sale"],
    "data": [],
    "demo": [],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_product_image_lazy_load/static/src/xml/product_card.xml",
        ],
    },
    "installable": True,
    "application": False,
}
