# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    pos_credit_customer = fields.Boolean(string="Cliente de crédito TPV")
    pos_credit_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moneda crédito TPV",
        compute="_compute_pos_credit_amounts",
        compute_sudo=True,
    )
    pos_credit_total_due = fields.Monetary(
        string="Pendiente crédito TPV",
        compute="_compute_pos_credit_amounts",
        compute_sudo=True,
        currency_field="pos_credit_currency_id",
    )
    pos_credit_ticket_count = fields.Integer(
        string="Tickets pendientes TPV",
        compute="_compute_pos_credit_amounts",
        compute_sudo=True,
    )

    @api.depends(
        "pos_credit_line_ids.amount_residual",
        "pos_credit_line_ids.state",
    )
    def _compute_pos_credit_amounts(self):
        credit_model = self.env["pos.customer.credit.line"].sudo()
        grouped = credit_model.read_group(
            [
                ("partner_id", "in", self.ids),
                ("state", "in", ("open", "partial")),
            ],
            ["partner_id", "amount_residual:sum"],
            ["partner_id"],
        )
        amounts = {
            item["partner_id"][0]: item["amount_residual"]
            for item in grouped
            if item.get("partner_id")
        }
        counts = {
            item["partner_id"][0]: item["partner_id_count"]
            for item in grouped
            if item.get("partner_id")
        }
        for partner in self:
            partner.pos_credit_currency_id = partner.company_id.currency_id or self.env.company.currency_id
            partner.pos_credit_total_due = amounts.get(partner.id, 0.0)
            partner.pos_credit_ticket_count = counts.get(partner.id, 0)

    pos_credit_line_ids = fields.One2many(
        comodel_name="pos.customer.credit.line",
        inverse_name="partner_id",
        string="Deudas TPV",
    )

    def action_view_pos_credit_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "servincom_pos_customer_credit_settlement.action_pos_customer_credit_line"
        )
        action["domain"] = [("partner_id", "=", self.id)]
        action["context"] = {
            "default_partner_id": self.id,
            "search_default_pending": 1,
        }
        return action

    @api.model
    def get_pos_credit_summary(self, partner_id):
        partner = self.browse(partner_id).exists()
        if not partner:
            return {}
        return {
            "partner_id": partner.id,
            "name": partner.display_name,
            "pos_credit_total_due": partner.pos_credit_total_due,
            "pos_credit_ticket_count": partner.pos_credit_ticket_count,
            "currency_id": partner.currency_id.id,
        }

    @api.model
    def get_pos_credit_lines(self, partner_id):
        lines = self.env["pos.customer.credit.line"].sudo().search(
            [
                ("partner_id", "=", partner_id),
                ("state", "in", ("open", "partial")),
            ],
            order="date_order asc, id asc",
        )
        return lines._pos_export_data()
