# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
import math
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CustomerHistoryBatch(models.Model):
    _name = "servincom.dashboard.history.batch"
    _description = "Customer History Batch"
    _check_company_auto = True
    _order = "year desc, id desc"

    name = fields.Char(string="Description", required=True)
    company_id = fields.Many2one("res.company", string="Company", required=True,
                                 default=lambda self: self.env.company, ondelete="restrict")
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency")
    year = fields.Integer(string="Year", required=True,
                          default=lambda self: fields.Date.today().year - 1)
    source = fields.Char(string="Source reference", required=True)
    source_checksum = fields.Char(string="Source checksum")
    state = fields.Selection([("draft", "Draft"), ("active", "Active")],
                             string="Status", required=True, default="draft", copy=False)
    line_ids = fields.One2many("servincom.dashboard.history.line", "batch_id", string="Documents")
    expected_count = fields.Integer(string="Expected documents", required=True)
    expected_net = fields.Monetary(string="Expected net amount", required=True)
    document_count = fields.Integer(string="Documents", compute="_compute_totals")
    net_amount = fields.Monetary(string="Net amount", compute="_compute_totals")
    notes = fields.Text(string="Validation notes")

    _sql_constraints = [
        ("company_year_unique", "unique(company_id, year)",
         "Only one customer history batch is allowed per company and year."),
    ]

    @api.depends("line_ids.amount_untaxed_signed")
    def _compute_totals(self):
        for batch in self:
            batch.document_count = len(batch.line_ids)
            batch.net_amount = sum(batch.line_ids.mapped("amount_untaxed_signed"))

    @api.constrains("year", "company_id", "name", "source", "expected_net")
    def _check_values(self):
        for batch in self:
            if not 1901 <= batch.year <= 9998 or not math.isfinite(batch.expected_net):
                raise ValidationError(self.env._("Choose a valid history year and finite amounts."))
            if not (batch.name or "").strip() or not (batch.source or "").strip():
                raise ValidationError(self.env._("Provide a description and source reference."))
            # Changing the batch year/company must validate existing documents too.
            batch.line_ids._check_values()

    def _check_no_live_overlap(self):
        for batch in self:
            # Only an existence check bypasses accounting rules, to prevent a
            # hidden invoice from allowing duplicate sources. No amounts leave sudo.
            overlap = self.env["account.move"].sudo().search_count([
                ("company_id", "=", batch.company_id.id), ("state", "=", "posted"),
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("invoice_date", ">=", date(batch.year, 1, 1)),
                ("invoice_date", "<=", date(batch.year, 12, 31)),
            ], limit=1)
            if overlap:
                raise ValidationError(self.env._(
                    "Historical and live invoices overlap. Return the history batch to draft before comparing."))

    @api.constrains("state", "company_id")
    def _check_activation(self):
        for batch in self.filtered(lambda b: b.state == "active"):
            lines = batch.line_ids
            if not lines or batch.expected_count != len(lines):
                raise ValidationError(self.env._("The document count must match the expected count before activation."))
            if batch.currency_id.compare_amounts(sum(lines.mapped("amount_untaxed_signed")), batch.expected_net):
                raise ValidationError(self.env._("The net amount must match the expected amount before activation."))
            lines._check_values()
            batch._check_no_live_overlap()

    @api.model_create_multi
    def create(self, vals_list):
        if any(values.get("state", "draft") != "draft" for values in vals_list):
            raise ValidationError(self.env._("Create history batches in draft before activating them."))
        return super().create(vals_list)

    def write(self, values):
        if any(batch.state == "active" for batch in self) and values != {"state": "draft"}:
            raise ValidationError(self.env._("Return the history batch to draft before editing it."))
        return super().write(values)

    def unlink(self):
        if any(batch.state == "active" for batch in self):
            raise ValidationError(self.env._("Return the history batch to draft before deleting it."))
        return super().unlink()

    def action_activate(self):
        self.write({"state": "active"})
        return True

    def action_draft(self):
        self.write({"state": "draft"})
        return True

    def action_documents(self):
        self.ensure_one()
        self.check_access("read")
        return {"type": "ir.actions.act_window", "name": self.env._("Historical documents"),
                "res_model": "servincom.dashboard.history.line", "view_mode": "list,form",
                "domain": [("batch_id", "=", self.id)],
                "context": dict(self.env.context, default_batch_id=self.id,
                                create=self.state == "draft" and self.env.user.has_group("base.group_system"))}


class CustomerHistoryLine(models.Model):
    _name = "servincom.dashboard.history.line"
    _description = "Historical Customer Document"
    _check_company_auto = True
    _order = "invoice_date desc, id desc"

    batch_id = fields.Many2one("servincom.dashboard.history.batch", string="History batch",
                               required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="batch_id.company_id", string="Company", store=True, index=True)
    currency_id = fields.Many2one(related="batch_id.currency_id", string="Currency")
    state = fields.Selection(related="batch_id.state", string="Status")
    source_key = fields.Char(string="Original document ID", required=True, index=True)
    name = fields.Char(string="Document number", required=True)
    invoice_date = fields.Date(string="Invoice date", required=True, index=True)
    partner_id = fields.Many2one("res.partner", string="Verified customer", required=True,
                                 ondelete="restrict", check_company=True, index=True)
    source_customer = fields.Char(string="Original customer reference")
    move_type = fields.Selection([("out_invoice", "Invoice"), ("out_refund", "Credit note")],
                                 string="Document type", required=True)
    amount_untaxed_signed = fields.Monetary(string="Signed untaxed amount", required=True)
    amount_total_signed = fields.Monetary(string="Signed total amount", required=True)
    salesperson_id = fields.Many2one("res.users", string="Verified salesperson", ondelete="restrict")
    source_salesperson = fields.Char(string="Original salesperson")

    _sql_constraints = [
        ("source_key_unique", "unique(batch_id, source_key)",
         "The original document already exists in this history batch."),
    ]

    @api.constrains("batch_id", "invoice_date", "partner_id", "source_key", "name",
                    "amount_untaxed_signed", "amount_total_signed", "salesperson_id")
    def _check_values(self):
        for line in self:
            if line.invoice_date.year != line.batch_id.year:
                raise ValidationError(self.env._("The invoice date must belong to the history batch year."))
            if line.partner_id != line.partner_id.commercial_partner_id:
                raise ValidationError(self.env._("Select an existing commercial customer for each historical document."))
            if line.partner_id.company_id and line.partner_id.company_id != line.company_id:
                raise ValidationError(self.env._("The historical customer must belong to the batch company or be shared."))
            if line.salesperson_id and line.company_id not in line.salesperson_id.company_ids:
                raise ValidationError(self.env._("The verified salesperson must have access to the batch company."))
            if not (line.source_key or "").strip() or not (line.name or "").strip():
                raise ValidationError(self.env._("Provide the original document ID and number."))
            if not all(math.isfinite(value) for value in (line.amount_untaxed_signed, line.amount_total_signed)):
                raise ValidationError(self.env._("Historical amounts must be finite numbers."))

    @api.model_create_multi
    def create(self, vals_list):
        default_batch = self.default_get(["batch_id"]).get("batch_id")
        batches = self.env["servincom.dashboard.history.batch"].browse(
            {values.get("batch_id", default_batch) for values in vals_list
             if values.get("batch_id", default_batch)})
        batches.check_access("read")
        if any(batch.state != "draft" for batch in batches):
            raise ValidationError(self.env._("Historical documents can only be changed in draft batches."))
        return super().create(vals_list)

    def write(self, values):
        batches = self.batch_id
        if values.get("batch_id"):
            batches |= self.env["servincom.dashboard.history.batch"].browse(values["batch_id"])
        if any(batch.state != "draft" for batch in batches):
            raise ValidationError(self.env._("Historical documents can only be changed in draft batches."))
        return super().write(values)

    def unlink(self):
        if any(batch.state != "draft" for batch in self.batch_id):
            raise ValidationError(self.env._("Historical documents can only be changed in draft batches."))
        return super().unlink()
