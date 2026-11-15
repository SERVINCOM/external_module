# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from lxml import etree

from odoo import api, models


class Board(models.AbstractModel):
    _inherit = "board.board"

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        result = super().get_view(view_id, view_type, **options)
        board_view = self.env.ref("servincom_account_dashboard.view_board", raise_if_not_found=False)
        if not board_view or (view_id or result.get("id")) != board_view.id:
            return result
        dashboard = self.env["servincom.account.dashboard"]._ensure_company_dashboard()
        custom = self.env["ir.ui.view.custom"].sudo().search([
            ("user_id", "=", self.env.uid), ("ref_id", "=", board_view.id),
        ], limit=1)
        arch = etree.fromstring((custom.arch if custom else result["arch"]).encode())
        mapping = {
            self.env.ref("servincom_account_dashboard.action_summary").id: dashboard.summary_instance_id,
            self.env.ref("servincom_account_dashboard.action_detail").id: dashboard.detail_instance_id,
        }
        for element in arch.xpath("//board/column/action"):
            instance = mapping.get(int(element.get("name", 0)))
            if instance:
                element.set("context", repr({
                    "active_model": "mis.report.instance", "active_id": instance.id,
                    "active_ids": instance.ids, "allowed_company_ids": [dashboard.company_id.id],
                    "default_name": self.env._("Accounting dashboards"),
                    "default_display_name": self.env._("Accounting dashboards"),
                }))
        arch.set("js_class", "board")
        arch_text = etree.tostring(arch, encoding="unicode")
        if not custom:
            # Native BoardController.saveBoard requires custom_view_id even on
            # the first visit. This record belongs only to the current user.
            custom = self.env["ir.ui.view.custom"].sudo().create({
                "user_id": self.env.uid, "ref_id": board_view.id, "arch": arch_text,
            })
        result.update(custom_view_id=custom.id, arch=arch_text)
        return result
