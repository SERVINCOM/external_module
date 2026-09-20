# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


def _merge_credit_payment_totals(closing_data, payment_totals):
    """Add debt settlements to their real payment-method closing rows."""
    method_rows = {
        method_data["id"]: method_data
        for method_data in closing_data.get("other_payment_methods", [])
    }
    for payment_method_id, totals in payment_totals.items():
        method_data = method_rows.get(payment_method_id)
        if not method_data:
            method_data = {
                "name": totals["name"],
                "amount": 0.0,
                "number": 0,
                "id": payment_method_id,
                "type": totals["type"],
            }
            closing_data.setdefault("other_payment_methods", []).append(method_data)
            method_rows[payment_method_id] = method_data
        method_data["amount"] = method_data.get("amount", 0.0) + totals["amount"]
        method_data["number"] = method_data.get("number", 0) + totals["number"]
    return closing_data


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

    def _get_pos_credit_non_cash_closing_totals(self):
        self.ensure_one()
        payments = self.sudo().pos_credit_payment_ids.filtered(
            lambda payment: payment.state == "posted"
            and not payment.payment_method_id.is_cash_count
        )
        totals = {}
        for payment in payments:
            payment_method = payment.payment_method_id
            method_totals = totals.setdefault(
                payment_method.id,
                {
                    "name": payment_method.name,
                    "type": payment_method.type,
                    "amount": 0.0,
                    "number": 0,
                },
            )
            method_totals["amount"] += payment.amount
            method_totals["number"] += 1
        return totals

    def get_closing_control_data(self):
        closing_data = super().get_closing_control_data()
        return _merge_credit_payment_totals(
            closing_data,
            self._get_pos_credit_non_cash_closing_totals(),
        )
