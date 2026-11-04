# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


RECEIPT_OPERATOR_DISPLAY_VALUES = {"name", "identifier", "hidden"}


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
    servincom_customize_receipt_operator = fields.Boolean(
        string="Customize operator on customer receipt",
        compute="_compute_servincom_receipt_options",
        inverse="_inverse_servincom_customize_receipt_operator",
        store=False,
        help=(
            "Enable custom operator display on customer receipts. When "
            "disabled, Odoo's standard receipt behavior is preserved."
        ),
    )
    servincom_receipt_operator_display = fields.Selection(
        selection=[
            ("name", "Employee full name"),
            ("identifier", "Operator identifier"),
            ("hidden", "Do not show operator"),
        ],
        string="Operator on customer receipt",
        compute="_compute_servincom_receipt_options",
        inverse="_inverse_servincom_receipt_operator_display",
        store=False,
        help="Choose how the current operator is identified on customer receipts.",
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
            display_key = config._servincom_receipt_parameter_key(
                "operator_display"
            )
            customize_key = config._servincom_receipt_parameter_key(
                "customize_operator"
            )
            legacy_operator_identifier = bool(
                operator_key
                and parameters.get_param(operator_key, "False") == "True"
            )
            operator_display = (
                parameters.get_param(display_key, "") if display_key else ""
            )
            if operator_display not in RECEIPT_OPERATOR_DISPLAY_VALUES:
                operator_display = (
                    "identifier" if legacy_operator_identifier else "name"
                )
            customize_value = (
                parameters.get_param(customize_key, "") if customize_key else ""
            )
            if customize_value in {"True", "False"}:
                customize_operator = customize_value == "True"
            else:
                customize_operator = legacy_operator_identifier or (
                    operator_display in {"identifier", "hidden"}
                )
            config.servincom_hide_receipt_taxes = bool(
                hide_key and parameters.get_param(hide_key, "False") == "True"
            )
            config.servincom_anonymize_receipt_operator = bool(
                customize_operator and operator_display == "identifier"
            )
            config.servincom_customize_receipt_operator = customize_operator
            config.servincom_receipt_operator_display = operator_display

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
                display_key = config._servincom_receipt_parameter_key(
                    "operator_display"
                )
                parameters.set_param(
                    display_key,
                    "identifier"
                    if config.servincom_anonymize_receipt_operator
                    else "name",
                )
                customize_key = config._servincom_receipt_parameter_key(
                    "customize_operator"
                )
                parameters.set_param(
                    customize_key,
                    config.servincom_anonymize_receipt_operator,
                )

    def _inverse_servincom_customize_receipt_operator(self):
        parameters = self.env["ir.config_parameter"].sudo()
        for config in self:
            customize_key = config._servincom_receipt_parameter_key(
                "customize_operator"
            )
            if customize_key:
                parameters.set_param(
                    customize_key,
                    config.servincom_customize_receipt_operator,
                )
                legacy_key = config._servincom_receipt_parameter_key(
                    "anonymize_operator"
                )
                parameters.set_param(
                    legacy_key,
                    bool(
                        config.servincom_customize_receipt_operator
                        and config.servincom_receipt_operator_display
                        == "identifier"
                    ),
                )

    def _inverse_servincom_receipt_operator_display(self):
        parameters = self.env["ir.config_parameter"].sudo()
        for config in self:
            display_key = config._servincom_receipt_parameter_key(
                "operator_display"
            )
            if display_key:
                operator_display = (
                    config.servincom_receipt_operator_display or "name"
                )
                parameters.set_param(display_key, operator_display)
                legacy_key = config._servincom_receipt_parameter_key(
                    "anonymize_operator"
                )
                parameters.set_param(
                    legacy_key,
                    bool(
                        config.servincom_customize_receipt_operator
                        and operator_display == "identifier"
                    ),
                )
