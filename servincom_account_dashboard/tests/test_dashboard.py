# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from datetime import date

from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestAccountDashboard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "Dashboard Test Company"})
        cls.other_company = cls.env["res.company"].create({"name": "Dashboard Other Company"})
        user_env = cls.env(context=dict(cls.env.context, no_reset_password=True))
        cls.reader = new_test_user(
            user_env, login="dashboard_reader_test", name="Dashboard Reader",
            groups="servincom_account_dashboard.group_dashboard_reader",
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)],
        )
        cls.denied = new_test_user(
            user_env, login="dashboard_denied_test", name="Dashboard Denied",
            groups="account.group_account_manager", company_id=cls.company.id,
            company_ids=[Command.set(cls.company.ids)],
        )
        cls.dashboard = cls.env["servincom.account.dashboard"].with_company(cls.company)._ensure_company_dashboard()
        cls.other_dashboard = cls.env["servincom.account.dashboard"].with_company(cls.other_company)._ensure_company_dashboard()
        cls.instances = cls.dashboard.summary_instance_id | cls.dashboard.detail_instance_id

    def _as_reader(self, record):
        return record.with_user(self.reader).with_context(allowed_company_ids=self.company.ids, lang="en_US")

    def test_independent_checkbox_and_revocation(self):
        self.assertFalse(self.reader.has_group("account.group_account_manager"))
        self.assertTrue(self.reader.has_group("account.group_account_readonly"))
        for instance in self.instances:
            self._as_reader(instance).compute()
            with self.assertRaises(AccessError):
                instance.with_user(self.denied).with_context(allowed_company_ids=self.company.ids).compute()
        with self.assertRaises(AccessError):
            self.dashboard.with_user(self.denied).get_monthly_summary()
        self.reader.servincom_dashboard_access = False
        for instance in self.instances:
            with self.assertRaises(AccessError):
                self._as_reader(instance).compute()
        self.reader.servincom_dashboard_access = True
        self._as_reader(self.dashboard.summary_instance_id).compute()

    def test_no_self_escalation_or_formula_edits(self):
        with self.assertRaises(AccessError):
            self.reader.with_user(self.reader).write({"servincom_dashboard_access": True})
        with self.assertRaises(AccessError):
            self._as_reader(self.dashboard.summary_instance_id).write({"target_move": "all"})
        with self.assertRaises(AccessError):
            self.dashboard.summary_instance_id.report_id.with_user(self.denied).write({"servincom_dashboard_report": False})

    def test_user_access_search_and_revocation(self):
        users = self.env["res.users"]
        candidates = self.reader | self.denied
        for operator, value, expected in [
            ("=", True, self.reader), ("=", False, self.denied),
            ("!=", True, self.denied), ("!=", False, self.reader),
            ("in", [True], self.reader), ("not in", [True], self.denied),
            ("in", [True, False], candidates), ("in", [], users),
            ("not in", [], candidates), ("not in", [True, False], users),
        ]:
            found = users.search([
                ("id", "in", candidates.ids),
                ("servincom_dashboard_access", operator, value),
            ])
            self.assertEqual(set(found.ids), set(expected.ids))
        self.reader.servincom_dashboard_access = False
        self.assertFalse(users.search([
            ("id", "in", candidates.ids), ("servincom_dashboard_access", "=", True),
        ]))
        self.assertTrue(users.fields_get(["servincom_dashboard_access"])[
            "servincom_dashboard_access"
        ]["searchable"])

    def test_year_selection_without_report_write_permission(self):
        for year in (2024, 2025, 2026):
            wizard = self.env["servincom.account.dashboard.year"].with_user(self.reader).with_context(
                allowed_company_ids=self.company.ids,
            ).create({"year": year})
            action = wizard.action_apply()
            self.assertEqual(action["res_model"], "board.board")
            for instance in self.instances:
                self.assertEqual(instance.date, date(year, 1, 1))
                periods = instance.period_ids.sorted("sequence")
                self.assertEqual(len(periods), 13)
                self.assertEqual(periods[0].date_from, date(year, 1, 1))
                self.assertEqual(periods[11].date_to, date(year, 12, 31))
        with self.assertRaises(ValidationError):
            self._as_reader(self.dashboard)._set_year(10000)

    def test_company_boundary(self):
        with self.assertRaises(AccessError):
            self._as_reader(self.other_dashboard).read(["year"])
        with self.assertRaises(AccessError):
            self._as_reader(self.other_dashboard.summary_instance_id).compute()
        with self.assertRaises(AccessError):
            self._as_reader(self.other_dashboard)._set_year(2025)
        with self.assertRaises(AccessError):
            self.env["servincom.account.dashboard"].with_user(self.reader).with_context(
                allowed_company_ids=self.other_company.ids,
            ).action_open()

    def test_board_preference_created_and_fold_persists(self):
        view = self.env.ref("servincom_account_dashboard.view_board")
        board = self._as_reader(self.env["board.board"])
        result = board.get_view(view.id)
        custom = self.env["ir.ui.view.custom"].browse(result["custom_view_id"])
        self.assertEqual(custom.user_id, self.reader)
        arch = etree.fromstring(result["arch"].encode())
        self.assertEqual(arch.get("js_class"), "servincom_results_board")
        arch.xpath("//board/column/action")[0].set("fold", "1")
        custom.write({"arch": etree.tostring(arch, encoding="unicode")})
        again = board.get_view(view.id)
        self.assertEqual(etree.fromstring(again["arch"].encode()).get("js_class"), "servincom_results_board")
        self.assertEqual(again["custom_view_id"], custom.id)
        self.assertEqual(etree.fromstring(again["arch"].encode()).xpath("//action")[0].get("fold"), "1")
        self.assertEqual(self.env["ir.ui.view.custom"].search_count([
            ("user_id", "=", self.reader.id), ("ref_id", "=", view.id),
        ]), 1)

    def test_personal_board_keeps_standard_controller(self):
        view = self.env["ir.ui.view"].create({
            "name": "Unrelated personal board",
            "model": "board.board",
            "arch": '<form string="Personal"><board style="1"><column/></board></form>',
        })
        result = self._as_reader(self.env["board.board"]).get_view(view.id)
        self.assertEqual(etree.fromstring(result["arch"].encode()).get("js_class"), "board")

    def test_board_upgrade_preserves_existing_fold_and_no_duplicate_summary(self):
        view = self.env.ref("servincom_account_dashboard.view_board")
        board = self._as_reader(self.env["board.board"])
        arch = etree.fromstring(view.arch_db.encode())
        compact = str(self.env.ref("servincom_account_dashboard.action_compact").id)
        action = arch.xpath("//action[@name='%s']" % compact)[0]
        action.getparent().remove(action)
        arch.xpath("//action")[0].set("fold", "1")
        custom = self.env["ir.ui.view.custom"].create({
            "ref_id": view.id, "user_id": self.reader.id,
            "arch": etree.tostring(arch, encoding="unicode"),
        })
        for attempt in range(2):
            result = etree.fromstring(board.get_view(view.id)["arch"].encode())
            actions = result.xpath("//action")
            self.assertEqual(len(actions), 3)
            self.assertEqual(actions[0].get("name"), compact)
            self.assertEqual(actions[1].get("fold"), "1")
        self.assertEqual(custom.servincom_dashboard_layout_version, 2)
        # A subsequent deliberate removal remains personal and is not undone.
        actions[0].getparent().remove(actions[0])
        custom.arch = etree.tostring(result, encoding="unicode")
        self.assertEqual(len(etree.fromstring(board.get_view(view.id)["arch"].encode()).xpath("//action")), 2)

    def test_exports_allowed_and_denied(self):
        for instance in self.instances:
            for method, xmlid, report_name in [
                ("_render_xlsx", "mis_builder.xls_export", "mis_builder.mis_report_instance_xlsx"),
                ("_render_qweb_html", "mis_builder.qweb_pdf_export", "mis_builder.report_mis_report_instance"),
            ]:
                report = self.env.ref(xmlid)
                result = getattr(self._as_reader(report), method)(report_name, instance.ids, data={"dummy": True})
                self.assertTrue(result[0])
                try:
                    getattr(report.with_user(self.denied).with_context(allowed_company_ids=self.company.ids), method)(
                        report_name, instance.ids, data={"dummy": True},
                    )
                except Exception as error:
                    cause = error
                    while cause and not isinstance(cause, AccessError):
                        cause = cause.__cause__ or cause.__context__
                    self.assertIsInstance(cause, AccessError)
                else:
                    self.fail("Unchecked user exported a protected report through %s" % method)

    def test_posted_results_refunds_and_excluded_journal(self):
        env = self.env(context=dict(self.env.context, allowed_company_ids=self.company.ids))
        account_model = env["account.account"].with_company(self.company)
        accounts = [account_model.create({
            "name": name, "code": code, "account_type": account_type,
            "company_ids": [Command.set(self.company.ids)],
        }) for code, name, account_type in [
            ("700901", "Test income", "income"),
            ("620901", "Test residual expense", "expense"),
            ("139901", "Test counterpart", "asset_current"),
        ]]
        journal = env["account.journal"].create({"name": "Test operations", "code": "DBT", "type": "general", "company_id": self.company.id})
        closing = env["account.journal"].create({"name": "Test closing", "code": "DBC", "type": "general", "company_id": self.company.id})
        self.dashboard._set_year(2026)
        self.dashboard.excluded_journal_ids = closing
        self.dashboard.action_apply_journals()

        def move(journal_record, balances, posted=True, entry_date=date(2026, 1, 15)):
            entry = env["account.move"].create({
                "journal_id": journal_record.id, "date": entry_date,
                "line_ids": [Command.create({
                    "name": "Dashboard test", "account_id": account.id,
                    "debit": max(balance, 0), "credit": max(-balance, 0),
                }) for account, balance in zip(accounts, balances)],
            })
            if posted:
                entry.action_post()
            return entry

        entry = move(journal, [-100, 40, 60])
        move(journal, [10, -5, -5])
        move(closing, [90, -35, -55])
        move(journal, [-999, 0, 999], posted=False)
        move(journal, [-200, 50, 150], entry_date=date(2025, 12, 15))
        move(journal, [-80, 30, 50], entry_date=date(2025, 1, 15))
        for instance in self.instances:
            rows = {row["label"]: row for row in self._as_reader(instance).compute()["body"]}
            self.assertAlmostEqual(rows["TOTAL INCOME"]["cells"][0]["val"], 90)
            self.assertAlmostEqual(rows["TOTAL PURCHASES AND EXPENSES"]["cells"][0]["val"], 35)
            self.assertAlmostEqual(rows["MONTHLY ACCOUNTING RESULT"]["cells"][0]["val"], 55)
            self.assertAlmostEqual(rows["MONTHLY ACCOUNTING RESULT"]["cells"][12]["val"], 55)
            if "CUMULATIVE RESULT" in rows:
                self.assertAlmostEqual(rows["CUMULATIVE RESULT"]["cells"][0]["val"], 55)
                self.assertAlmostEqual(rows["CUMULATIVE RESULT"]["cells"][11]["val"], 55)
        reader = self._as_reader(self.dashboard)
        compact = reader.get_monthly_summary()
        self.assertEqual([row["cells"][0]["value"] for row in compact["rows"]], [90, 35, 55])
        self.assertEqual(len(compact["rows"]), 3)
        self.assertTrue(all(len(row["cells"]) == 13 for row in compact["rows"]))
        self.dashboard.comparison_start_year = 2026
        snapshot = [(i.id, i.date, i.name) for i in self.instances]
        comparison = reader.get_annual_comparison(2026, 1)
        self.assertTrue(comparison["ready"])
        result = comparison["rows"][2]["cells"]
        self.assertEqual(result[0], {"current": 55, "previous": 50, "delta": 5, "percent": 10})
        self.assertIsNone(result[1]["current"])
        self.assertEqual(result[12]["current"], 55)
        self.assertEqual(snapshot, [(i.id, i.date, i.name) for i in self.instances])
        self.assertEqual(self.dashboard.year, 2026)
        self.assertEqual(reader.get_monthly_summary()["rows"][2]["cells"][0]["value"], 55)
        self.assertFalse(reader.get_annual_comparison(2025, 1)["ready"])
        with self.assertRaises(AccessError):
            self._as_reader(entry).write({"ref": "Forbidden"})
