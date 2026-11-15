# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from odoo import api, fields, models
from odoo.tools import SQL


class AccountMaturity(models.Model):
    _name = "servincom.account.maturity"
    _description = "Outstanding Receivables and Payables"
    _auto = False
    _log_access = False
    _rec_name = "move_id"
    _order = "due_date, move_id, id"

    line_id = fields.Many2one("account.move.line", string="Journal item", readonly=True)
    move_id = fields.Many2one("account.move", string="Document", readonly=True)
    name = fields.Char(string="Label", readonly=True)
    reference = fields.Char(string="Reference", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Customer / vendor", readonly=True)
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    journal_id = fields.Many2one("account.journal", string="Journal", readonly=True)
    account_id = fields.Many2one("account.account", string="Account", readonly=True)
    company_currency_id = fields.Many2one("res.currency", string="Company currency", readonly=True)
    currency_id = fields.Many2one("res.currency", string="Document currency", readonly=True)
    invoice_date = fields.Date(string="Invoice date", readonly=True)
    accounting_date = fields.Date(string="Accounting date", readonly=True)
    date_maturity = fields.Date(string="Document due date", readonly=True)
    due_date = fields.Date(
        string="Due date", readonly=True,
        help="The journal item's due date; the accounting date is used if no due date is set.",
    )
    direction = fields.Selection(
        [("receivable", "Receivable"), ("payable", "Payable")],
        string="Direction", readonly=True,
    )
    move_type = fields.Selection([
        ("entry", "Payment / other entry"),
        ("out_invoice", "Customer invoice"), ("in_invoice", "Vendor bill"),
        ("out_refund", "Customer credit note"), ("in_refund", "Vendor credit note"),
        ("out_receipt", "Sales receipt"), ("in_receipt", "Purchase receipt"),
    ], string="Document type", readonly=True)
    due_state = fields.Selection([
        ("overdue", "Overdue"), ("today", "Due today"),
        ("upcoming", "Not yet due"), ("missing", "No due date"),
    ], string="Due status", readonly=True)
    is_partial = fields.Boolean(string="Partially settled", readonly=True)
    amount_original = fields.Monetary(
        string="Original installment", currency_field="company_currency_id", readonly=True,
    )
    amount_pending = fields.Monetary(
        string="Outstanding amount", currency_field="company_currency_id", readonly=True,
        help="Current residual in company currency. Credit notes and unapplied payments retain their negative sign.",
    )
    amount_pending_currency = fields.Monetary(
        string="Outstanding in document currency", currency_field="currency_id",
        readonly=True, aggregator=False,
    )

    _depends = {
        "account.move.line": [
            "move_id", "name", "partner_id", "company_id", "journal_id", "account_id",
            "company_currency_id", "currency_id", "date", "date_maturity", "balance",
            "amount_currency", "amount_residual", "amount_residual_currency", "reconciled",
        ],
        "account.move": ["state", "ref", "invoice_date", "move_type"],
        "account.account": ["account_type"],
    }

    def _check_maturity_read_access(self):
        self.env["servincom.account.dashboard"]._check_dashboard_access()
        # Query-backed records filtered out by a source rule can appear to the
        # ORM as missing records. Check the real source before formatting or
        # exporting cached values, including exports that do not call read().
        self.env["account.move.line"].browse(self.ids).check_access("read")
        self.check_access("read")

    def _read_format(self, fnames, load="_classic_read"):
        self._check_maturity_read_access()
        return super()._read_format(fnames, load=load)

    def export_data(self, fields_to_export):
        self._check_maturity_read_access()
        return super().export_data(fields_to_export)

    def _check_access(self, operation):
        result = super()._check_access(operation)
        if result or operation != "read" or not self:
            return result
        # Also enforce source rules when stored report values are already in
        # the environment cache and no SQL query needs to run.
        source_result = self.env["account.move.line"].browse(self.ids)._check_access("read")
        if source_result:
            return self.browse(source_result[0].ids), source_result[1]
        return None

    @property
    def _table_query(self):
        # Build the source through the ORM to retain *all* journal-item record
        # rules (including installed extensions), not just a company SQL filter.
        self.env["servincom.account.dashboard"]._check_dashboard_access()
        source = self.env["account.move.line"]._search([
            ("parent_state", "=", "posted"), ("reconciled", "=", False),
            ("account_id.account_type", "in", ["asset_receivable", "liability_payable"]),
        ])
        sign = SQL("CASE WHEN account.account_type = 'liability_payable' THEN -1 ELSE 1 END")
        return SQL("""
            SELECT line.id, line.id AS line_id, line.move_id, line.name,
                   move.ref AS reference, line.partner_id, line.company_id,
                   line.journal_id, line.account_id, line.company_currency_id,
                   line.currency_id, move.invoice_date, line.date AS accounting_date,
                   line.date_maturity, COALESCE(line.date_maturity, line.date) AS due_date,
                   move.move_type,
                   CASE WHEN account.account_type = 'liability_payable'
                        THEN 'payable' ELSE 'receivable' END AS direction,
                   CASE WHEN line.date_maturity IS NULL THEN 'missing'
                        WHEN line.date_maturity < %(today)s THEN 'overdue'
                        WHEN line.date_maturity = %(today)s THEN 'today'
                        ELSE 'upcoming' END AS due_state,
                   (line.amount_residual != line.balance OR
                    line.amount_residual_currency != line.amount_currency) AS is_partial,
                   %(sign)s * line.balance AS amount_original,
                   %(sign)s * line.amount_residual AS amount_pending,
                   %(sign)s * line.amount_residual_currency AS amount_pending_currency
              FROM account_move_line line
              JOIN account_move move ON move.id = line.move_id
              JOIN account_account account ON account.id = line.account_id
             WHERE line.id IN (%(source)s)
        """, today=fields.Date.context_today(self), sign=sign, source=source.select())

    @api.model
    def _open_maturities(self, direction):
        company = self.env["servincom.account.dashboard"]._check_dashboard_access()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "servincom_account_dashboard.action_maturity"
        )
        action["name"] = (
            self.env._("Sales maturities - receivables") if direction == "receivable"
            else self.env._("Purchase maturities - payables")
        ) + " · " + company.currency_id.name
        # One active company per screen: totals must never mix currencies.
        action["domain"] = [("direction", "=", direction), ("company_id", "=", company.id)]
        action["context"] = dict(self.env.context, search_default_group_week=1)
        return action

    @api.model
    def action_open_receivables(self):
        return self._open_maturities("receivable")

    @api.model
    def action_open_payables(self):
        return self._open_maturities("payable")

    def action_open_document(self):
        self.ensure_one()
        self.check_access("read")
        self.move_id.check_access("read")
        return {
            "type": "ir.actions.act_window", "res_model": "account.move",
            "res_id": self.move_id.id, "view_mode": "form", "views": [(False, "form")],
        }
