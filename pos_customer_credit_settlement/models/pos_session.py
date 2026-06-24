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
            "pos_customer_credit_settlement.action_pos_customer_credit_payment"
        )
        action["domain"] = [("session_id", "=", self.id)]
        action["context"] = {"default_session_id": self.id}
        return action

    def _add_pos_credit_loader_fields(self, params, field_names):
        fields_list = params.setdefault("search_params", {}).setdefault("fields", [])
        for field_name in field_names:
            if field_name not in fields_list:
                fields_list.append(field_name)
        return params

    def _loader_params_pos_config(self):
        params = super()._loader_params_pos_config()
        return self._add_pos_credit_loader_fields(
            params,
            [
                "is_posbox",
                "iface_electronic_scale",
                "iface_print_via_proxy",
                "enable_pos_customer_credit",
                "allow_pos_credit_settlement",
                "pos_credit_payment_method_id",
            ],
        )

    def _loader_params_pos_payment_method(self):
        params = super()._loader_params_pos_payment_method()
        return self._add_pos_credit_loader_fields(
            params,
            ["is_pos_customer_credit"],
        )

    def _loader_params_res_partner(self):
        params = super()._loader_params_res_partner()
        return self._add_pos_credit_loader_fields(
            params,
            [
                "pos_credit_customer",
                "pos_credit_total_due",
                "pos_credit_ticket_count",
            ],
        )
