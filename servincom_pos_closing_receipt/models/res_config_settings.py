# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_servincom_hide_receipt_taxes = fields.Boolean(
        related="pos_config_id.servincom_hide_receipt_taxes",
        readonly=False,
    )
    pos_servincom_anonymize_receipt_operator = fields.Boolean(
        related="pos_config_id.servincom_anonymize_receipt_operator",
        readonly=False,
    )
    pos_servincom_receipt_operator_display = fields.Selection(
        related="pos_config_id.servincom_receipt_operator_display",
        readonly=False,
    )
