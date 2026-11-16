# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from datetime import date
from unittest.mock import patch

from psycopg2 import IntegrityError

from odoo import Command, fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestCustomerEvolution(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "Customer Evolution Test"})
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=cls.company.ids))
        account = cls.env["account.account"].with_company(cls.company)
        cls.receivable = account.create({"name": "Evolution receivable", "code": "430912",
            "account_type": "asset_receivable", "reconcile": True, "company_ids": [Command.set(cls.company.ids)]})
        cls.income = account.create({"name": "Evolution income", "code": "700912",
            "account_type": "income", "company_ids": [Command.set(cls.company.ids)]})
        cls.journal = cls.env["account.journal"].create({"name": "Evolution sales", "code": "EVO",
            "type": "sale", "company_id": cls.company.id})
        user_env = cls.env(context=dict(cls.env.context, no_reset_password=True))
        cls.reader = new_test_user(user_env, login="evolution_reader_test",
            groups="servincom_account_dashboard.group_dashboard_reader",
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.other_salesperson = new_test_user(user_env, login="evolution_other_test",
            groups="base.group_user", company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.dashboard = cls.env["servincom.account.dashboard"].with_user(cls.reader)
        cls.customer = cls._partner("Existing customer")
        cls.child = cls._partner("Delivery contact", parent_id=cls.customer.id)
        cls.new_customer = cls._partner("First purchase customer")
        cls.lapsed = cls._partner("No purchase customer")
        cls.returned = cls._partner("Returning customer")
        cls.credit = cls._partner("Credit only customer")

    @classmethod
    def _partner(cls, name, **values):
        return cls.env["res.partner"].create({"name": name,
            "property_account_receivable_id": cls.receivable.id, **values})

    def _invoice(self, partner, amount, invoice_date, refund=False, posted=True, salesperson=None):
        move = self.env["account.move"].create({
            "move_type": "out_refund" if refund else "out_invoice", "partner_id": partner.id,
            "journal_id": self.journal.id, "invoice_date": invoice_date,
            "invoice_user_id": (salesperson or self.reader).id,
            "invoice_line_ids": [Command.create({"name": "Evolution test", "quantity": 1,
                "price_unit": amount, "account_id": self.income.id, "tax_ids": [Command.clear()]})],
        })
        if posted:
            move.action_post()
        return move

    def _populate(self):
        self._invoice(self.customer, 100, date(2025, 1, 10))
        self._invoice(self.child, 40, date(2025, 1, 15), salesperson=self.other_salesperson)
        self._invoice(self.customer, 80, date(2026, 1, 10))
        self._invoice(self.child, 20, date(2026, 1, 15), salesperson=self.other_salesperson)
        self._invoice(self.customer, 10, date(2026, 1, 20), refund=True)
        self._invoice(self.new_customer, 50, date(2026, 1, 12))
        self._invoice(self.lapsed, 60, date(2025, 1, 10))
        self._invoice(self.returned, 20, date(2024, 1, 10))
        self._invoice(self.returned, 30, date(2026, 1, 10))
        self._invoice(self.credit, 15, date(2026, 1, 10), refund=True)
        self._invoice(self.customer, 999, date(2026, 2, 10))
        self._invoice(self.customer, 777, date(2026, 1, 10), posted=False)

    def test_cohorts_net_refunds_contacts_and_cutoff(self):
        self._populate()
        data = self.dashboard.get_customer_evolution(2026, 1)
        rows = {row["id"]: row for row in data["rows"]}
        self.assertNotIn(self.child.id, rows)
        self.assertEqual(rows[self.customer.id]["current"], 90)
        self.assertEqual(rows[self.customer.id]["previous"], 140)
        self.assertEqual(rows[self.customer.id]["status"], "decline")
        self.assertEqual(rows[self.customer.id]["last_purchase"], "2026-01-15")
        self.assertEqual(rows[self.new_customer.id]["status"], "new")
        self.assertIsNone(rows[self.new_customer.id]["percent"])
        self.assertEqual(rows[self.lapsed.id]["status"], "no_purchase")
        self.assertEqual(rows[self.lapsed.id]["percent"], -100)
        self.assertEqual(rows[self.returned.id]["status"], "recovered")
        self.assertEqual(rows[self.credit.id]["status"], "credits")
        self.assertEqual(rows[self.credit.id]["current"], -15)
        self.assertEqual(data["counts"], {"active": 3, "decline": 1, "no_purchase": 1, "new": 1})
        self.assertEqual(data["trend"][0], {"month": 1, "current": 3, "previous": 2})
        self.assertIsNone(data["trend"][1]["current"])

    def test_salesperson_and_drilldown_match(self):
        self._populate()
        data = self.dashboard.get_customer_evolution(2026, 1, self.reader.id)
        row = next(row for row in data["rows"] if row["id"] == self.customer.id)
        self.assertEqual(row["current"], 70)
        self.assertEqual(row["previous"], 100)
        self.assertEqual(data["salesperson_id"], self.reader.id)
        action = self.dashboard.action_customer_invoices(self.customer.id, 2026, 1, self.reader.id)
        moves = self.env["account.move"].with_user(self.reader).search(action["domain"])
        self.assertEqual(len(moves), 3)
        self.assertEqual(sum(moves.filtered(lambda m: m.invoice_date.year == 2026).mapped("amount_untaxed_signed")), row["current"])

    def test_rule_revocation_and_company_boundary(self):
        invoice = self._invoice(self.customer, 100, date(2026, 1, 10))
        self.assertEqual(self.dashboard.get_customer_evolution(2026, 1)["counts"]["active"], 1)
        self.env["ir.rule"].create({"name": "Evolution restricted invoice", "model_id": self.env["ir.model"]._get_id("account.move"),
            "domain_force": "[('id', '!=', %s)]" % invoice.id})
        self.assertEqual(self.dashboard.get_customer_evolution(2026, 1)["rows"], [])
        other = self.env["res.company"].create({"name": "Evolution forbidden company"})
        with self.assertRaises(AccessError):
            self.dashboard.with_context(allowed_company_ids=other.ids).get_customer_evolution(2026, 1)
        self.reader.servincom_dashboard_access = False
        for method, args in [("get_customer_evolution", [2026, 1]), ("get_monthly_summary", []),
                             ("get_annual_comparison", [2026, 1]), ("action_customer_invoices", [self.customer.id, 2026, 1]),
                             ("action_customer_history", [self.customer.id, 2026, 1])]:
            with self.assertRaises(AccessError):
                getattr(self.dashboard, method)(*args)

    def _history_batch(self, documents, year=2025):
        batch = self.env["servincom.dashboard.history.batch"].create({
            "name": "Verified history test", "company_id": self.company.id, "year": year,
            "source": "Fictitious test source", "expected_count": len(documents),
            "expected_net": sum(doc[1] for doc in documents),
        })
        self.env["servincom.dashboard.history.line"].create([
            {"batch_id": batch.id, "source_key": str(index), "name": "TEST/%s" % index,
             "invoice_date": date(year, 1, 10), "partner_id": partner.id,
             "move_type": "out_invoice" if amount >= 0 else "out_refund",
             "amount_untaxed_signed": amount, "amount_total_signed": amount}
            for index, (partner, amount) in enumerate(documents)
        ])
        return batch

    def _opening_entry(self, partner, year=2025):
        journal = self.env["account.journal"].create({"name": "Opening test", "code": "OPH",
            "type": "general", "company_id": self.company.id})
        entry = self.env["account.move"].create({"journal_id": journal.id, "date": date(year, 1, 1),
            "line_ids": [Command.create({"name": "Opening receivable", "partner_id": partner.id,
                "account_id": self.receivable.id, "debit": 40}),
                Command.create({"name": "Opening counterpart", "account_id": self.income.id, "credit": 40})]})
        entry.action_post()
        return entry

    def test_history_matches_only_and_preserves_accounting(self):
        self._invoice(self.customer, 80, date(2026, 1, 10))
        self._invoice(self.new_customer, 50, date(2026, 1, 10))
        opening = self._opening_entry(self.credit)
        moves_before = self.env["account.move"].search([]).read(["state", "amount_total", "date"])
        opening_before = opening.line_ids.read(["balance", "partner_id", "account_id"])
        batch = self._history_batch([(self.customer, 100), (self.customer, -10), (self.lapsed, 60)])
        batch.action_activate()
        data = self.dashboard.get_customer_evolution(2026, 1)
        rows = {row["id"]: row for row in data["rows"]}
        self.assertTrue(data["matched_history"])
        self.assertNotIn(self.credit.id, rows)  # An opening entry is not a sale.
        self.assertEqual(rows[self.customer.id]["previous"], 90)
        self.assertEqual(rows[self.customer.id]["delta"], -10)
        self.assertTrue(rows[self.customer.id]["has_history"])
        self.assertEqual(rows[self.customer.id]["status"], "decline")
        for key in ("previous", "delta", "percent"):
            self.assertIsNone(rows[self.new_customer.id][key])
        self.assertEqual(rows[self.new_customer.id]["status"], "unavailable")
        self.assertEqual(rows[self.lapsed.id]["status"], "no_purchase")
        self.assertEqual(data["counts"], {"active": 2, "decline": 1, "no_purchase": 1, "new": 0, "unavailable": 1})
        self.assertEqual(data["trend"][0], {"month": 1, "current": 1, "previous": 2})
        action = self.dashboard.action_customer_history(self.customer.id, 2026, 1)
        lines = self.env[action["res_model"]].with_user(self.reader).search(action["domain"])
        self.assertEqual(sum(lines.mapped("amount_untaxed_signed")), 90)
        self.assertEqual(self.env["account.move"].search([]).read(["state", "amount_total", "date"]), moves_before)
        self.assertEqual(opening.line_ids.read(["balance", "partner_id", "account_id"]), opening_before)

    def test_history_draft_security_and_read_rules(self):
        batch = self._history_batch([(self.customer, 100)])
        line = batch.line_ids
        model = self.env["servincom.dashboard.history.line"].with_user(self.reader)
        self.assertFalse(model.search([("batch_id", "=", batch.id)]))
        with self.assertRaises(AccessError):
            batch.with_user(self.reader).action_activate()
        batch.action_activate()
        self.assertEqual(model.search([("batch_id", "=", batch.id)]).ids, line.ids)
        with self.assertRaises(AccessError):
            line.with_user(self.reader).write({"amount_untaxed_signed": 200})
        with self.assertRaises(AccessError):
            line.with_user(self.reader).unlink()
        with self.assertRaises(AccessError):
            batch.with_user(self.reader).write({"name": "Forbidden change"})
        with self.assertRaises(AccessError):
            batch.with_user(self.reader).unlink()
        with self.assertRaises(AccessError):
            self.env["servincom.dashboard.history.line"].with_user(self.other_salesperson).search([])
        settings_user = new_test_user(self.env(context=dict(self.env.context, no_reset_password=True)),
            login="history_settings_without_access_test", groups="base.group_system",
            company_id=self.company.id, company_ids=[Command.set(self.company.ids)])
        self.assertFalse(line.with_user(settings_user).search([("id", "=", line.id)]))
        with self.assertRaises(AccessError):
            line.with_user(settings_user).read(["amount_untaxed_signed"])
        self._invoice(self.customer, 80, date(2026, 1, 10))
        self.env["ir.rule"].create({"name": "Restricted historical document",
            "model_id": self.env["ir.model"]._get_id("servincom.dashboard.history.line"),
            "domain_force": "[('id', '!=', %s)]" % line.id})
        data = self.dashboard.get_customer_evolution(2026, 1)
        self.assertIsNone(data["rows"][0]["previous"])
        self.assertEqual(data["rows"][0]["status"], "unavailable")
        other = self.env["res.company"].create({"name": "History forbidden company"})
        with self.assertRaises(AccessError):
            model.with_context(allowed_company_ids=other.ids).search([])
        self.reader.servincom_dashboard_access = False
        with self.assertRaises(AccessError):
            model.search([])

    def test_history_activation_checks_and_immutability(self):
        batch = self._history_batch([(self.customer, 100)])
        line = batch.line_ids
        batch.expected_count = 2
        with self.assertRaises(ValidationError), self.cr.savepoint():
            batch.action_activate()
        batch.write({"expected_count": 1, "expected_net": 99})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            batch.action_activate()
        batch.expected_net = 100
        batch.action_activate()
        with self.assertRaises(ValidationError):
            line.write({"amount_untaxed_signed": 110})
        with self.assertRaises(ValidationError):
            line.unlink()
        with self.assertRaises(ValidationError):
            batch.write({"year": 2024})
        with self.assertRaises(ValidationError):
            batch.unlink()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["servincom.dashboard.history.line"].with_context(default_batch_id=batch.id).create({
                "name": "Not allowed", "source_key": "extra", "invoice_date": date(2025, 1, 10),
                "partner_id": self.customer.id, "move_type": "out_invoice",
                "amount_untaxed_signed": 1, "amount_total_signed": 1})
        batch.action_draft()
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            line.copy()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            line.write({"invoice_date": date(2024, 1, 1)})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            line.write({"partner_id": self.child.id})
        line.write({"amount_untaxed_signed": 90})
        batch.expected_net = 90
        batch.action_activate()

    def test_history_overlap_and_unmapped_salesperson(self):
        batch = self._history_batch([(self.customer, 100)])
        batch.action_activate()
        self._invoice(self.customer, 80, date(2026, 1, 10))
        data = self.dashboard.get_customer_evolution(2026, 1, self.reader.id)
        self.assertIsNone(data["rows"][0]["previous"])
        self.assertEqual(data["rows"][0]["status"], "unavailable")
        batch.action_draft()
        batch.line_ids.salesperson_id = self.reader
        batch.action_activate()
        data = self.dashboard.get_customer_evolution(2026, 1, self.reader.id)
        self.assertEqual(data["rows"][0]["previous"], 100)
        self._invoice(self.customer, 100, date(2025, 1, 10))
        with self.assertRaises(ValidationError):
            self.dashboard.get_customer_evolution(2026, 1)
        batch.action_draft()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            batch.action_activate()

    def test_history_equal_cutoff_and_missing_older_year(self):
        self._invoice(self.customer, 80, date(2026, 1, 10))
        self._invoice(self.new_customer, 50, date(2026, 1, 10))
        batch = self._history_batch([(self.customer, 100), (self.new_customer, 200)])
        batch.line_ids.filtered(lambda line: line.partner_id == self.new_customer).invoice_date = date(2025, 2, 1)
        batch.action_activate()
        data = self.dashboard.get_customer_evolution(2026, 1)
        rows = {row["id"]: row for row in data["rows"]}
        self.assertEqual(rows[self.customer.id]["previous"], 100)
        self.assertIsNone(rows[self.new_customer.id]["previous"])
        data = self.dashboard.get_customer_evolution(2025, 1)
        self.assertIsNone(data["rows"][0]["previous"])
        self.assertIsNone(data["rows"][0]["delta"])

    def test_archived_salesperson_last_without_losing_invoices(self):
        dashboard = self.dashboard.with_context(lang="en_US")
        self.reader.name = "Zeta salesperson"
        self.other_salesperson.name = "Alfa salesperson"
        current = self._invoice(self.customer, 80, date(2026, 1, 10))
        archived = self._invoice(self.customer, 20, date(2026, 1, 11),
                                 salesperson=self.other_salesperson)
        before = dashboard.get_customer_evolution(2026, 1)
        self.assertEqual([user["id"] for user in before["salespeople"]],
                         [self.other_salesperson.id, self.reader.id])

        self.other_salesperson.active = False
        after = dashboard.get_customer_evolution(2026, 1)
        self.assertEqual([user["id"] for user in after["salespeople"]],
                         [self.reader.id, self.other_salesperson.id])
        self.assertTrue(after["salespeople"][0]["active"])
        self.assertFalse(after["salespeople"][1]["active"])
        self.assertEqual(after["salespeople"][1]["name"], "Alfa salesperson (Archived)")
        for key in ("rows", "counts", "trend"):
            self.assertEqual(before[key], after[key])

        filtered = dashboard.get_customer_evolution(2026, 1, self.other_salesperson.id)
        self.assertEqual(filtered["rows"][0]["current"], 20)
        action = dashboard.action_customer_invoices(
            self.customer.id, 2026, 1, self.other_salesperson.id)
        self.assertEqual(self.env["account.move"].with_user(self.reader).search(action["domain"]), archived)
        self.assertEqual(current.invoice_user_id, self.reader)
        self.assertEqual(archived.invoice_user_id, self.other_salesperson)

    def test_period_validation_leap_year_and_future(self):
        with patch.object(fields.Date, "context_today", return_value=date(2024, 2, 29)):
            start, end, previous_start, previous_end = self.dashboard._analysis_period(2024, 2)
            self.assertEqual(end, date(2024, 2, 29))
            self.assertEqual(previous_end, date(2023, 2, 28))
            self.assertFalse(self.dashboard.get_customer_evolution(2025, 1)["ready"])
        with patch.object(fields.Date, "context_today", return_value=date(2026, 11, 15)):
            start, end, previous_start, previous_end = self.dashboard._analysis_period(2026, 12)
            self.assertEqual(end, date(2026, 11, 15))
            self.assertEqual(previous_end, date(2025, 11, 15))
        for year, month in [(1900, 1), (True, 1), (2026, 0), (2026, 13), (2026, "1")]:
            with self.assertRaises(ValidationError):
                self.dashboard._analysis_period(year, month)

    def test_monthly_invoicing_same_cohort_and_available_totals(self):
        self._invoice(self.customer, 80, date(2026, 1, 10))
        self._invoice(self.child, 20, date(2026, 1, 11))
        self._invoice(self.new_customer, 50, date(2026, 1, 12))
        self._invoice(self.customer, 999, date(2026, 3, 1))
        self._invoice(self.customer, 777, date(2026, 1, 10), posted=False)
        self._opening_entry(self.credit)
        batch = self._history_batch([(self.customer, 100), (self.customer, -10),
                                     (self.lapsed, 60), (self.customer, 40)])
        batch.line_ids.filtered(lambda line: line.source_key == "3").invoice_date = date(2025, 2, 5)
        batch.action_activate()
        data = self.dashboard.get_customer_evolution(2026, 2)
        comparable = data["sales"]["comparable"]
        available = data["sales"]["available"]
        self.assertEqual(data["comparable_customer_count"], 2)
        self.assertEqual({key: comparable[0][key] for key in ["month", "current", "previous", "delta"]},
                         {"month": 1, "current": 100, "previous": 150, "delta": -50})
        self.assertAlmostEqual(comparable[0]["percent"], -100 / 3)
        self.assertEqual(comparable[1]["current"], 0)
        self.assertEqual(comparable[1]["previous"], 40)
        self.assertEqual(comparable[12]["current"], 100)
        self.assertEqual(comparable[12]["previous"], 190)
        self.assertEqual(available[12]["current"], 150)
        self.assertEqual(available[12]["previous"], 190)
        self.assertIsNone(available[12]["delta"])
        self.assertIsNone(available[12]["percent"])
        self.assertIsNone(comparable[2]["current"])
        self.assertIsNone(available[2]["previous"])
        for scope in [comparable, available]:
            for key in ["current", "previous"]:
                self.assertAlmostEqual(sum(row[key] or 0 for row in scope[:12]), scope[12][key])
        self.assertEqual(data["period_trend"][0], {"month": 1, "current": 2, "previous": 2})
        self.assertEqual(data["period_counts"], {"current": 2, "previous": 2})
        rows = {row["id"]: row for row in data["rows"]}
        self.assertEqual(rows[self.customer.id]["last_purchase_previous"], "2025-02-05")
        self.assertTrue(rows[self.new_customer.id]["has_current"])
        self.assertFalse(rows[self.new_customer.id]["has_previous"])

    def test_monthly_invoicing_respects_partner_rules_and_salesperson(self):
        self._invoice(self.customer, 80, date(2026, 1, 10))
        self._invoice(self.new_customer, 50, date(2026, 1, 10), salesperson=self.other_salesperson)
        batch = self._history_batch([(self.customer, 100), (self.new_customer, 60)])
        batch.line_ids.filtered(lambda line: line.partner_id == self.customer).salesperson_id = self.reader
        batch.action_activate()
        data = self.dashboard.get_customer_evolution(2026, 1, self.reader.id)
        self.assertEqual(data["sales"]["available"][12]["current"], 80)
        self.assertEqual(data["sales"]["available"][12]["previous"], 100)
        self.env["ir.rule"].create({"name": "Hidden historical customer",
            "model_id": self.env["ir.model"]._get_id("res.partner"),
            "domain_force": "[('id', '!=', %s)]" % self.customer.id})
        data = self.dashboard.get_customer_evolution(2026, 1)
        self.assertEqual(data["sales"]["available"][12]["current"], 50)
        self.assertEqual(data["sales"]["available"][12]["previous"], 60)
        self.assertEqual(data["comparable_customer_count"], 1)

    def test_document_detail_limits_selected_year(self):
        old = self._invoice(self.customer, 100, date(2025, 1, 10))
        new = self._invoice(self.customer, 80, date(2026, 1, 10))
        for period, expected in [("current", new), ("previous", old), ("both", old | new)]:
            action = self.dashboard.action_customer_invoices(self.customer.id, 2026, 1, None, period)
            found = self.env["account.move"].with_user(self.reader).search(action["domain"])
            self.assertEqual(set(found.ids), set(expected.ids))
        batch = self._history_batch([(self.customer, 70)], year=2024)
        batch.action_activate()
        for period, count in [("current", 0), ("previous", 1), ("both", 1)]:
            action = self.dashboard.action_customer_history(self.customer.id, 2025, 1, None, period)
            self.assertEqual(self.env[action["res_model"]].with_user(self.reader).search_count(action["domain"]), count)
        with self.assertRaises(ValidationError):
            self.dashboard.action_customer_history(self.customer.id, 2026, 1, None, "invalid")

    def test_manual_full_year_keeps_december_and_recorded_future_invoices(self):
        self._invoice(self.customer, 80, date(2026, 1, 10))
        future = self._invoice(self.customer, 20, date(2026, 12, 10))
        self._invoice(self.customer, 999, date(2026, 12, 15), posted=False)
        batch = self._history_batch([(self.customer, 100), (self.customer, 60), (self.customer, -10)])
        batch.line_ids.filtered(lambda line: line.source_key != "0").invoice_date = date(2025, 12, 15)
        batch.action_activate()
        dates = dict(date_from="2026-01-01", date_to="2026-12-31",
                     comparison_date_from="2025-01-01", comparison_date_to="2025-12-31")
        with patch.object(fields.Date, "context_today", return_value=date(2026, 11, 15)):
            data = self.dashboard.get_customer_evolution(**dates)
        self.assertEqual(data["date_to"], "2026-12-31")
        self.assertEqual(data["comparison_date_to"], "2025-12-31")
        self.assertTrue(data["periods_aligned"])
        self.assertEqual(data["sales"]["available"][11]["previous"], 50)
        self.assertEqual(data["sales"]["available"][11]["current"], 20)
        self.assertEqual(data["sales"]["available"][12]["previous"], 150)
        self.assertEqual(data["sales"]["available"][12]["current"], 100)
        action = self.dashboard.action_customer_invoices(self.customer.id, period="current", **dates)
        self.assertIn(future, self.env["account.move"].search(action["domain"]))
        action = self.dashboard.action_customer_history(self.customer.id, period="previous", **dates)
        self.assertEqual(set(self.env[action["res_model"]].search(action["domain"]).ids), set(batch.line_ids.ids))

    def test_manual_independent_ranges_and_inclusive_drilldown(self):
        self._invoice(self.customer, 900, date(2026, 2, 9))
        first = self._invoice(self.customer, 80, date(2026, 2, 10))
        last = self._invoice(self.child, 20, date(2026, 3, 5))
        self._invoice(self.customer, 800, date(2026, 3, 6))
        batch = self._history_batch([(self.customer, 100), (self.customer, 40), (self.customer, -10)])
        batch.line_ids.filtered(lambda line: line.source_key == "1").invoice_date = date(2025, 12, 31)
        batch.action_activate()
        dates = dict(date_from="2026-02-10", date_to="2026-03-05",
                     comparison_date_from="2025-01-10", comparison_date_to="2025-12-31")
        data = self.dashboard.get_customer_evolution(**dates)
        self.assertFalse(data["periods_aligned"])
        self.assertEqual(data["rows"][0]["current"], 100)
        self.assertEqual(data["rows"][0]["previous"], 130)
        self.assertEqual(data["rows"][0]["last_purchase_current"], "2026-03-05")
        self.assertIsNone(data["trend"][0]["current"])
        self.assertEqual(data["trend"][11]["previous"], 1)
        cells = data["sales"]["comparable"]
        self.assertIsNone(cells[0]["current"])
        self.assertEqual(cells[0]["previous"], 90)
        self.assertEqual(cells[1]["current"], 80)
        self.assertEqual(cells[2]["current"], 20)
        self.assertIsNone(cells[11]["current"])
        self.assertEqual(cells[11]["previous"], 40)
        self.assertIsNone(cells[11]["delta"])
        self.assertEqual(cells[12]["delta"], -30)
        for key in ["current", "previous"]:
            self.assertEqual(sum(cell[key] or 0 for cell in cells[:12]), cells[12][key])
        action = self.dashboard.action_customer_invoices(self.customer.id, period="current", **dates)
        self.assertEqual(set(self.env["account.move"].search(action["domain"]).ids), {first.id, last.id})
        self.env["ir.rule"].create({"name": "Hidden manual range invoice",
            "model_id": self.env["ir.model"]._get_id("account.move"), "domain_force": "[('id', '!=', %s)]" % last.id})
        self.assertEqual(self.dashboard.get_customer_evolution(**dates)["rows"][0]["current"], 80)
        self.reader.servincom_dashboard_access = False
        with self.assertRaises(AccessError):
            self.dashboard.get_customer_evolution(**dates)
        with self.assertRaises(AccessError):
            self.dashboard.action_customer_history(self.customer.id, **dates)

    def test_manual_range_validation_and_leap_day(self):
        periods = self.dashboard._customer_periods(date_from="2024-02-29", date_to="2024-03-02")
        self.assertEqual(periods, (date(2024, 2, 29), date(2024, 3, 2), date(2023, 2, 28), date(2023, 3, 2)))
        good = dict(date_from="2026-01-01", date_to="2026-12-31",
                    comparison_date_from="2025-01-01", comparison_date_to="2025-12-31")
        for overrides in [dict(date_from=""), dict(date_to="not-a-date"), dict(date_to="2026-02-30"),
                          dict(date_to="2025-12-31"), dict(date_to="2027-01-01"),
                          dict(comparison_date_to="2026-01-01"), dict(comparison_date_from=None),
                          dict(comparison_date_from="2026-01-01", comparison_date_to="2026-12-31"),
                          dict(date_from=True)]:
            with self.assertRaises(ValidationError):
                self.dashboard.get_customer_evolution(**dict(good, **overrides))
        with patch.object(fields.Date, "context_today", return_value=date(2026, 11, 15)):
            future = self.dashboard.get_customer_evolution(date_from="2027-01-01", date_to="2027-12-31")
        self.assertTrue(future["ready"])
        self.assertEqual(future["rows"], [])

    def test_manual_comparison_can_use_an_older_imported_year(self):
        self._invoice(self.customer, 80, date(2026, 1, 10))
        batch = self._history_batch([(self.customer, 100)], year=2024)
        batch.action_activate()
        dates = dict(date_from="2026-01-01", date_to="2026-01-31",
                     comparison_date_from="2024-01-01", comparison_date_to="2024-12-31")
        data = self.dashboard.get_customer_evolution(**dates)
        self.assertEqual(data["previous_year"], 2024)
        self.assertEqual(data["historical_years"], [2024])
        self.assertEqual(data["rows"][0]["previous"], 100)
        action = self.dashboard.action_customer_history(self.customer.id, period="previous", **dates)
        self.assertEqual(self.env[action["res_model"]].search(action["domain"]), batch.line_ids)
