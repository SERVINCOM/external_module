# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosSession(models.Model):
    _inherit = "pos.session"

    pos_credit_payment_ids = fields.One2many(
        comodel_name="pos.customer.credit.payment",
        inverse_name="session_id",
        string="Cobros deuda clientes",
    )
    pos_credit_payment_total = fields.Monetary(
        string="Total cobros deuda clientes",
        compute="_compute_pos_credit_payments",
        currency_field="currency_id",
    )
    pos_credit_payment_count = fields.Integer(
        string="Cobros deuda clientes",
        compute="_compute_pos_credit_payments",
    )

    def _compute_pos_credit_payments(self):
        for session in self:
            payments = session.pos_credit_payment_ids.filtered(
                lambda payment: payment.state == "posted"
            )
            session.pos_credit_payment_total = sum(payments.mapped("amount"))
            session.pos_credit_payment_count = len(payments)

    def action_view_pos_credit_payments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "servincom_pos_customer_credit_settlement.action_pos_customer_credit_payment"
        )
        action["domain"] = [("session_id", "=", self.id)]
        action["context"] = {"default_session_id": self.id}
        return action

    def get_closing_control_data(self):
        data = super().get_closing_control_data()
        self.ensure_one()
        posted_payments = self.pos_credit_payment_ids.filtered(
            lambda payment: payment.state == "posted"
        )
        cash_details = data.get("default_cash_details") or {}
        cash_method_id = cash_details.get("id")
        non_cash_payments = posted_payments.filtered(
            lambda payment: payment.payment_method_id.id != cash_method_id
        )
        if not non_cash_payments:
            return data

        other_method_rows = {
            method_data["id"]: method_data
            for method_data in data.get("other_payment_methods", [])
        }
        for payment_method in non_cash_payments.mapped("payment_method_id"):
            method_payments = non_cash_payments.filtered(
                lambda payment, method=payment_method: payment.payment_method_id == method
            )
            amount = sum(method_payments.mapped("amount"))
            if payment_method.id in other_method_rows:
                other_method_rows[payment_method.id]["amount"] += amount
                other_method_rows[payment_method.id]["number"] += len(method_payments)
                continue
            method_data = {
                "name": payment_method.name,
                "amount": amount,
                "number": len(method_payments),
                "id": payment_method.id,
                "type": payment_method.type,
            }
            data.setdefault("other_payment_methods", []).append(method_data)
            other_method_rows[payment_method.id] = method_data
        data["payments_amount"] = data.get("payments_amount", 0.0) + sum(
            non_cash_payments.mapped("amount")
        )
        return data
