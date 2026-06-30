# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    voxel_state = fields.Selection(
        selection_add=[("pending", "Pending send")],
        ondelete={"pending": "set default"},
    )
