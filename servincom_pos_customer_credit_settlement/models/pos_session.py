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
