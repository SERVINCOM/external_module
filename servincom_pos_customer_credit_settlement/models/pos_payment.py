# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PosPayment(models.Model):
    _inherit = "pos.payment"

    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)
        payments.mapped("pos_order_id")._create_pos_customer_credit_lines()
        return payments

    def write(self, vals):
        orders_before = self.mapped("pos_order_id")
        result = super().write(vals)
        orders = orders_before | self.mapped("pos_order_id")
        if {"amount", "payment_method_id", "pos_order_id"} & set(vals):
            orders._create_pos_customer_credit_lines()
        return result
