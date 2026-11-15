# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from datetime import date, timedelta

from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestAccountMaturity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "Maturity Test Company"})
        cls.other_company = cls.env["res.company"].create({"name": "Maturity Other Company"})
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=cls.company.ids))
        cls.partner = cls.env["res.partner"].create({"name": "Maturity Test Partner"})
        account = cls.env["account.account"].with_company(cls.company)
        cls.receivable = account.create({
            "name": "Maturity receivable", "code": "430901", "account_type": "asset_receivable",
            "reconcile": True, "company_ids": [Command.set(cls.company.ids)],
        })
        cls.payable = account.create({
            "name": "Maturity payable", "code": "400901", "account_type": "liability_payable",
            "reconcile": True, "company_ids": [Command.set(cls.company.ids)],
        })
        cls.income = account.create({
            "name": "Maturity income", "code": "700901", "account_type": "income",
            "company_ids": [Command.set(cls.company.ids)],
        })
        cls.expense = account.create({
            "name": "Maturity expense", "code": "600901", "account_type": "expense",
            "company_ids": [Command.set(cls.company.ids)],
        })
        cls.partner.with_company(cls.company).write({
            "property_account_receivable_id": cls.receivable.id,
            "property_account_payable_id": cls.payable.id,
        })
        cls.journal = cls.env["account.journal"].create({
            "name": "Maturity operations", "code": "MAT", "type": "general", "company_id": cls.company.id,
        })
        cls.sale_journal = cls.env["account.journal"].create({
            "name": "Maturity sales", "code": "MAS", "type": "sale", "company_id": cls.company.id,
        })
        cls.purchase_journal = cls.env["account.journal"].create({
            "name": "Maturity purchases", "code": "MAP", "type": "purchase", "company_id": cls.company.id,
        })
        user_env = cls.env(context=dict(cls.env.context, no_reset_password=True))
        cls.reader = new_test_user(
            user_env, login="maturity_reader_test", name="Maturity Reader",
            groups="servincom_account_dashboard.group_dashboard_reader,base.group_allow_export",
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)],
        )
        cls.denied = new_test_user(
            user_env, login="maturity_denied_test", name="Maturity Denied",
            groups="account.group_account_manager", company_id=cls.company.id,
            company_ids=[Command.set(cls.company.ids)],
        )
        cls.report = cls.env["servincom.account.maturity"].with_user(cls.reader)

    def _entry(self, account, installments, posted=True, currency=None):
        """A single document with independent due lines, and a balanced offset."""
        values = []
        for index, (balance, due) in enumerate(installments):
            vals = {
                "name": "Maturity installment %s" % index, "account_id": account.id,
                "partner_id": self.partner.id, "date_maturity": due,
                "debit": max(balance, 0), "credit": max(-balance, 0),
            }
            if currency:
                vals.update(currency_id=currency.id, amount_currency=balance * 2)
            values.append(vals)
        total = sum(amount for amount, due in installments)
        offset = {"name": "Counterpart", "account_id": self.income.id,
                  "debit": max(-total, 0), "credit": max(total, 0)}
        if currency:
            offset.update(currency_id=currency.id, amount_currency=-total * 2)
        move = self.env["account.move"].create({
            "journal_id": self.journal.id, "date": date(2026, 1, 1),
            "line_ids": [Command.create(vals) for vals in values + [offset]],
        })
        if posted:
            move.action_post()
        return move.line_ids.filtered(lambda line: line.account_id == account)

    def _invoice(self, move_type, amount):
        purchase = move_type.startswith("in_")
        move = self.env["account.move"].create({
            "move_type": move_type, "partner_id": self.partner.id,
            "journal_id": (self.purchase_journal if purchase else self.sale_journal).id,
            "invoice_date": date(2026, 1, 1), "invoice_date_due": date(2026, 1, 31),
            "invoice_line_ids": [Command.create({
                "name": "Maturity test invoice", "quantity": 1, "price_unit": amount,
                "account_id": (self.expense if purchase else self.income).id,
                "tax_ids": [Command.clear()],
            })],
        })
        move.action_post()
        return move

    def test_invoices_credit_notes_and_payable_sign(self):
        for move_type, expected in [
            ("out_invoice", 100), ("out_refund", -100),
            ("in_invoice", 100), ("in_refund", -100),
        ]:
            invoice = self._invoice(move_type, 100)
            rows = self.report.search([("move_id", "=", invoice.id)])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows.move_type, move_type)
            self.assertAlmostEqual(rows.amount_original, expected)
            self.assertAlmostEqual(rows.amount_pending, expected)
            self.assertEqual(rows.direction, "payable" if move_type.startswith("in_") else "receivable")

    def test_installments_partial_settlement_and_fully_paid(self):
        terms = self._entry(self.receivable, [(100, date(2026, 1, 5)), (200, date(2026, 1, 12))])
        payment = self._entry(self.receivable, [(-40, date(2026, 1, 5))])
        (terms[0] | payment).reconcile()
        rows = self.report.search([("move_id", "=", terms.move_id.id)])
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(sum(rows.mapped("amount_pending")), 260)
        self.assertAlmostEqual(self.report.browse(terms[0].id).amount_pending, 60)
        self.assertTrue(self.report.browse(terms[0].id).is_partial)
        self.assertFalse(self.report.search([("id", "in", payment.ids)]))
        final_payment = self._entry(self.receivable, [(-60, date(2026, 1, 5))])
        (terms[0] | final_payment).reconcile()
        self.assertFalse(self.report.search([("id", "=", terms[0].id)]))
        self.assertEqual(self.report.search([("move_id", "=", terms.move_id.id)]).ids, terms[1].ids)

    def test_unapplied_payments_drafts_and_week_totals(self):
        invoice = self._entry(self.payable, [(-100, date(2026, 1, 5)), (-200, date(2026, 1, 12))])
        advance = self._entry(self.payable, [(25, date(2026, 1, 5))])
        draft = self._entry(self.payable, [(-999, date(2026, 1, 5))], posted=False)
        domain = [("line_id", "in", (invoice | advance | draft).ids)]
        rows = self.report.search(domain)
        self.assertEqual(set(rows.ids), set((invoice | advance).ids))
        self.assertAlmostEqual(self.report.browse(advance.id).amount_pending, -25)
        weeks = self.report._read_group(domain, ["due_date:week"], ["amount_pending:sum"])
        self.assertEqual(sorted(amount for week, amount in weeks), [75, 200])
        starts = sorted(week for week, amount in weeks)
        self.assertEqual(starts[1] - starts[0], timedelta(days=7))

    def test_due_status_and_missing_date(self):
        today = fields.Date.context_today(self.report)
        lines = self._entry(self.receivable, [
            (10, today - timedelta(days=1)), (20, today), (30, today + timedelta(days=1)),
        ])
        rows = self.report.search([("id", "in", lines.ids)])
        self.assertEqual(set(rows.mapped("due_state")), {"overdue", "today", "upcoming"})
        # Legacy posted entries can lack a due date. This test-only SQL mutation
        # is rolled back with its fixture; no production script uses it.
        self.env.cr.execute("UPDATE account_move_line SET date_maturity = NULL WHERE id = %s", [lines[0].id])
        self.env.invalidate_all()
        row = self.report.browse(lines[0].id)
        self.assertEqual(row.due_state, "missing")
        self.assertEqual(row.due_date, row.accounting_date)

    def test_foreign_currency_is_not_summed_with_company_amounts(self):
        currency = self.env["res.currency"].create({"name": "XMT", "symbol": "X", "rounding": 0.01})
        line = self._entry(self.receivable, [(80, date(2026, 1, 5))], currency=currency)
        row = self.report.browse(line.id)
        self.assertEqual(row.currency_id, currency)
        self.assertEqual(row.company_currency_id, self.company.currency_id)
        self.assertAlmostEqual(row.amount_pending, 80)
        self.assertAlmostEqual(row.amount_pending_currency, 160)
        self.assertFalse(self.report._fields["amount_pending_currency"].aggregator)

    def test_permission_revocation_readonly_and_company_scope(self):
        line = self._entry(self.receivable, [(100, date(2026, 1, 5))])
        row = self.report.browse(line.id)
        self.assertEqual(row.amount_pending, 100)
        self.assertEqual(row.export_data(["amount_pending"])["datas"], [[100]])
        for method in ("search", "read_group"):
            with self.assertRaises(AccessError):
                if method == "search":
                    self.report.with_user(self.denied).search([])
                else:
                    self.report.with_user(self.denied).read_group([], ["amount_pending:sum"], [])
        with self.assertRaises(AccessError):
            row.write({"name": "Forbidden"})
        with self.assertRaises(AccessError):
            self.report.with_context(allowed_company_ids=self.other_company.ids).search([])
        for action in [self.report.action_open_receivables(), self.report.action_open_payables()]:
            self.assertIn(("company_id", "=", self.company.id), action["domain"])
        self.reader.servincom_dashboard_access = False
        with self.assertRaises(AccessError):
            row.export_data(["amount_pending"])
        with self.assertRaises(AccessError):
            self.report.action_open_receivables()

    def test_source_journal_item_rules_are_preserved(self):
        visible = self._entry(self.receivable, [(100, date(2026, 1, 5))])
        hidden = self._entry(self.receivable, [(200, date(2026, 1, 5))])
        cached = self.env["servincom.account.maturity"].browse(hidden.id)
        self.assertEqual(cached.amount_pending, 200)
        self.env["ir.rule"].create({
            "name": "Maturity test restricted source", "model_id": self.env["ir.model"]._get_id("account.move.line"),
            "domain_force": "[('id', '!=', %s)]" % hidden.id,
        })
        domain = [("id", "in", (visible | hidden).ids)]
        self.assertEqual(self.report.search(domain).ids, visible.ids)
        totals = self.report._read_group(domain, [], ["amount_pending:sum"])
        self.assertEqual(totals, [(100,)])
        with self.assertRaises(AccessError):
            cached.with_user(self.reader).read(["amount_pending"])
        with self.assertRaises(AccessError):
            cached.with_user(self.reader).export_data(["amount_pending"])
