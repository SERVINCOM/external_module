# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    products = env["product.product"].with_context(active_test=False).search([])
    for offset in range(0, len(products), 1000):
        batch = products[offset : offset + 1000]
        batch._compute_attribute_value_order_key()
        batch.flush_recordset(["attribute_value_order_key"])
