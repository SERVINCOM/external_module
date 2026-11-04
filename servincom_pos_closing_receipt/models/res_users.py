# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    servincom_pos_receipt_operator_label = fields.Char(
        string="Receipt operator identifier",
        compute="_compute_servincom_pos_receipt_operator_label",
        inverse="_inverse_servincom_pos_receipt_operator_label",
        store=False,
        help=(
            "Public identifier printed instead of the user's full name on "
            "customer receipts, for example: Operator 01."
        ),
    )

    def _servincom_operator_parameter_key(self):
        self.ensure_one()
        record_id = self.id if isinstance(self.id, int) else False
        if not record_id:
            return False
        return f"servincom_pos_closing_receipt.user_operator.{record_id}"

    def _compute_servincom_pos_receipt_operator_label(self):
        parameters = self.env["ir.config_parameter"].sudo()
        for user in self:
            key = user._servincom_operator_parameter_key()
            user.servincom_pos_receipt_operator_label = (
                parameters.get_param(key, "") if key else False
            )

    def _inverse_servincom_pos_receipt_operator_label(self):
        parameters = self.env["ir.config_parameter"].sudo()
        for user in self:
            key = user._servincom_operator_parameter_key()
            if key:
                parameters.set_param(
                    key, user.servincom_pos_receipt_operator_label or ""
                )
