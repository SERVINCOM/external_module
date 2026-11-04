# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    servincom_hide_receipt_taxes = fields.Boolean(
        string="Hide taxes on POS receipts",
        help=(
            "Hide the tax breakdown and total taxes on printed POS receipts. "
            "Use this only for tax regimes where the customer receipt must not "
            "show them."
        ),
    )
    servincom_anonymize_receipt_operator = fields.Boolean(
        string="Use operator identifier on POS receipts",
        help=(
            "Replace the cashier's name with the configured operator identifier "
            "on customer receipts."
        ),
    )
