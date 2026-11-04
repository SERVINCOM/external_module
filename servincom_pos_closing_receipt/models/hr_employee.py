# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    servincom_pos_receipt_operator_label = fields.Char(
        string="Operator identifier on POS receipts",
        copy=False,
        help=(
            "Public identifier printed instead of the employee's full name, "
            "for example: Operator 1."
        ),
    )
