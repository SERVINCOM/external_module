# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from odoo import Command, api, fields, models
from odoo.exceptions import AccessError

from .dashboard import GROUP


class ResUsers(models.Model):
    _inherit = "res.users"

    servincom_dashboard_access = fields.Boolean(
        string="View accounting dashboards", compute="_compute_dashboard_access",
        inverse="_inverse_dashboard_access", groups="base.group_system",
        search="_search_dashboard_access",
        help="Allow both dashboards and read-only accounting detail. This does not grant accounting edit rights.",
    )

    @api.depends("groups_id")
    def _compute_dashboard_access(self):
        group = self.env.ref(GROUP)
        for user in self:
            user.servincom_dashboard_access = group in user.groups_id

    @api.model
    def _search_dashboard_access(self, operator, value):
        if operator in ("=", "!="):
            matches = {bool(value)}
        elif operator in ("in", "not in"):
            matches = {bool(item) for item in value}
        else:
            return NotImplemented
        if operator in ("!=", "not in"):
            matches = {False, True} - matches
        if len(matches) == 2:
            return []
        if not matches:
            return [("id", "=", 0)]
        group = self.env.ref(GROUP)
        return [("groups_id", "in" if True in matches else "not in", group.ids)]

    def _inverse_dashboard_access(self):
        if not self.env.su and not self.env.user.has_group("base.group_system"):
            raise AccessError(self.env._("Only settings administrators can grant dashboard access."))
        group = self.env.ref(GROUP)
        for user in self:
            if user.share and user.servincom_dashboard_access:
                raise AccessError(self.env._("Dashboard access is restricted to internal users."))
            command = Command.link(group.id) if user.servincom_dashboard_access else Command.unlink(group.id)
            user.write({"groups_id": [command]})
