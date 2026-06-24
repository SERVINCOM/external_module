# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "SERVINCOM POS Customer Credit Settlement",
    "version": "16.0.3.3.0",
    "summary": "Customer credit tickets and debt settlement from the Point of Sale",
    "category": "Point of Sale",
    "author": "SERVINCOM SOLUCIONES, S.L.",
    "license": "AGPL-3",
    "depends": [
        "account",
        "contacts",
        "point_of_sale",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "views/res_partner_views.xml",
        "views/pos_payment_method_views.xml",
        "views/pos_config_views.xml",
        "views/pos_customer_credit_line_views.xml",
        "views/pos_customer_credit_payment_views.xml",
        "views/pos_session_views.xml",
        "views/pos_menu_views.xml",
    ],
    "installable": True,
    "application": False,
}
