# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from lxml import etree

from odoo import api, fields, models


class DashboardCustomView(models.Model):
    _inherit = "ir.ui.view.custom"

    servincom_dashboard_layout_version = fields.Integer(string="Dashboard layout version", default=0)


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
        compact_id = self.env.ref("servincom_account_dashboard.action_compact").id
        upgrade_layout = custom and custom.servincom_dashboard_layout_version < 2
        if upgrade_layout and not arch.xpath("//action[@name='%s']" % compact_id):
            column = arch.find("board/column")
            if column is None:
                column = etree.SubElement(arch.find("board"), "column")
            column.insert(0, etree.Element("action", name=str(compact_id),
                                          string=self.env._("Monthly summary"), view_mode="form"))
        mapping = {
            compact_id: dashboard.summary_instance_id,
            self.env.ref("servincom_account_dashboard.action_summary").id: dashboard.summary_instance_id,
            self.env.ref("servincom_account_dashboard.action_detail").id: dashboard.detail_instance_id,
        }
        titles = {
            compact_id: self.env._("Monthly summary"),
            self.env.ref("servincom_account_dashboard.action_summary").id: self.env._("Detailed monthly results"),
            self.env.ref("servincom_account_dashboard.action_detail").id: self.env._("Accounting detail of monthly results"),
        }
        for element in arch.xpath("//board/column/action"):
            instance = mapping.get(int(element.get("name", 0)))
            if instance:
                element.set("string", titles[int(element.get("name"))])
                element.set("context", repr({
                    "active_model": "mis.report.instance", "active_id": instance.id,
                    "active_ids": instance.ids, "allowed_company_ids": [dashboard.company_id.id],
                    "default_name": self.env._("Accounting dashboards"),
                    "default_display_name": self.env._("Accounting dashboards"),
                }))
        arch.set("js_class", "servincom_results_board")
        arch_text = etree.tostring(arch, encoding="unicode")
        if not custom:
            # Native BoardController.saveBoard requires custom_view_id even on
            # the first visit. This record belongs only to the current user.
            custom = self.env["ir.ui.view.custom"].sudo().create({
                "user_id": self.env.uid, "ref_id": board_view.id, "arch": arch_text,
                "servincom_dashboard_layout_version": 2,
            })
        elif upgrade_layout:
            custom.write({"arch": arch_text, "servincom_dashboard_layout_version": 2})
        result.update(custom_view_id=custom.id, arch=arch_text)
        return result
