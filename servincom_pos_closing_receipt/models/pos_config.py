# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    servincom_hide_receipt_taxes = fields.Boolean(
        string="Hide tax details on POS receipts",
        compute="_compute_servincom_receipt_options",
        inverse="_inverse_servincom_hide_receipt_taxes",
        store=False,
        help=(
            "Hide the tax breakdown and total taxes on customer receipts. "
            "Enable it only for tax regimes that require receipts without tax "
            "details."
        ),
    )
    servincom_anonymize_receipt_operator = fields.Boolean(
        string="Use receipt operator identifier",
        compute="_compute_servincom_receipt_options",
        inverse="_inverse_servincom_anonymize_receipt_operator",
        store=False,
        help=(
            "Replace the cashier's full name with the configured operator "
            "identifier on customer receipts."
        ),
    )

    def _servincom_receipt_parameter_key(self, option):
        self.ensure_one()
        record_id = self.id if isinstance(self.id, int) else False
        if not record_id:
            return False
        return f"servincom_pos_closing_receipt.{option}.{record_id}"

    def _compute_servincom_receipt_options(self):
        parameters = self.env["ir.config_parameter"].sudo()
        for config in self:
            hide_key = config._servincom_receipt_parameter_key("hide_taxes")
            operator_key = config._servincom_receipt_parameter_key(
                "anonymize_operator"
            )
            config.servincom_hide_receipt_taxes = bool(
                hide_key and parameters.get_param(hide_key, "False") == "True"
            )
            config.servincom_anonymize_receipt_operator = bool(
                operator_key
                and parameters.get_param(operator_key, "False") == "True"
            )

    def _inverse_servincom_hide_receipt_taxes(self):
        parameters = self.env["ir.config_parameter"].sudo()
        for config in self:
            key = config._servincom_receipt_parameter_key("hide_taxes")
            if key:
                parameters.set_param(key, config.servincom_hide_receipt_taxes)

    def _inverse_servincom_anonymize_receipt_operator(self):
        parameters = self.env["ir.config_parameter"].sudo()
        for config in self:
            key = config._servincom_receipt_parameter_key("anonymize_operator")
            if key:
                parameters.set_param(
                    key, config.servincom_anonymize_receipt_operator
                )
