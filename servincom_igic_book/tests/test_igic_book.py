# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import io
import zipfile
from xml.etree import ElementTree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import new_test_user, tagged


@tagged("post_install", "-at_install")
class TestIgicBook(AccountTestInvoicingCommon):
    chart_template = "es_canary_pymes"
    country_code = "ES"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.vat = "ES12345678Z"
        cls.partner_a.vat = "ES12345678Z"
        cls.env.user.groups_id |= cls.env.ref("l10n_es_aeat.group_account_aeat")
        cls.sale_tax = cls._tax("igic_r_7")
        cls.purchase_tax = cls._tax("igic_sop_7")

    @classmethod
    def _tax(cls, suffix):
        return cls.company._get_taxes_from_xmlids(["account_tax_template_" + suffix])

    def _invoice(self, tax, move_type="out_invoice", amount=100.0, post=True):
        return self._create_invoice(
            move_type=move_type,
            invoice_date="2026-01-15",
            post=post,
            invoice_line_ids=[
                Command.create(
                    {
                        "name": "IGIC test",
                        "quantity": 1,
                        "price_unit": amount,
                        "account_id": self.company_data[
                            "default_account_revenue"
                            if move_type.startswith("out")
                            else "default_account_expense"
                        ].id,
                        "tax_ids": [Command.set(tax.ids)],
                    }
                )
            ],
        )

    def _book(self, igic=True):
        return self.env["l10n.es.vat.book"].create(
            {
                "servincom_is_igic": igic,
                "company_id": self.company.id,
                "company_vat": "12345678Z",
                "contact_name": "Test contact",
                "contact_phone": "922000000",
                "year": 2026,
                "period_type": "1T",
                "date_start": "2026-01-01",
                "date_end": "2026-03-31",
            }
        )

    def test_sale_purchase_and_refunds(self):
        self._invoice(self.sale_tax)
        self._invoice(self.sale_tax, "out_refund", 20)
        self._invoice(self.purchase_tax, "in_invoice", 200)
        self._invoice(self.purchase_tax, "in_refund", 50)
        self._invoice(self.sale_tax, post=False)
        book = self._book()
        book.button_calculate()
        issued, received = book._get_igic_report_sections()
        self.assertEqual(issued["invoice_count"], 2)
        self.assertAlmostEqual(issued["base"], 80)
        self.assertAlmostEqual(issued["fee"], 5.6)
        self.assertAlmostEqual(received["base"], 150)
        self.assertAlmostEqual(received["fee"], 10.5)
        self.assertEqual(len(book.rectification_issued_line_ids), 1)
        self.assertEqual(len(book.rectification_received_line_ids), 1)
        book.button_recalculate()
        self.assertEqual(len(book.line_ids), 4)

    def test_zero_exempt_and_multiple_rates(self):
        self._invoice(self._tax("igic_r_0"))
        self._invoice(self._tax("igic_re_ex"))
        self._invoice(self._tax("igic_r_3"))
        self._invoice(self.sale_tax)
        book = self._book()
        book.button_calculate()
        section = book._get_igic_report_sections()[0]
        self.assertEqual(section["invoice_count"], 4)
        self.assertAlmostEqual(section["base"], 400)
        self.assertAlmostEqual(section["fee"], 10)

    def test_vat_books_do_not_pick_igic_maps(self):
        self._invoice(self.sale_tax)
        mapping = self.env.ref("servincom_igic_book.map_igic_issued")
        self.assertFalse(mapping.get_taxes_for_company(self.company))
        self.assertIn(
            self.sale_tax,
            mapping.with_context(servincom_igic_book=True).get_taxes_for_company(
                self.company
            ),
        )
        vat_mapping = self.env.ref("l10n_es_vat_book.aeat_vat_book_map_line_s_iva")
        self.assertFalse(
            vat_mapping.with_context(servincom_igic_book=True).get_taxes_for_company(
                self.company
            )
        )
        book = self._book(igic=False)
        book.button_calculate()
        self.assertFalse(book.line_ids)

    def test_archived_equivalent_tax(self):
        custom = self.sale_tax.copy(
            {"name": "Custom IGIC", "aeat_equivalent_tax_id": self.sale_tax.id}
        )
        self._invoice(custom)
        custom.active = False
        book = self._book()
        book.button_calculate()
        self.assertEqual(book.issued_line_ids.tax_line_ids.tax_id, custom)
        self.assertAlmostEqual(book.issued_line_ids.tax_line_ids.tax_amount, 7)

    def test_partial_deductibility(self):
        self.purchase_tax.servincom_igic_deductible_percent = 50
        self._invoice(self.purchase_tax, "in_invoice")
        book = self._book()
        book.button_calculate()
        section = book._get_igic_report_sections()[1]
        self.assertAlmostEqual(section["fee"], 7)
        self.assertAlmostEqual(section["deductible"], 3.5)
        self.purchase_tax.servincom_igic_deductible_percent = 0
        book.button_recalculate()
        self.assertAlmostEqual(book._get_igic_report_sections()[1]["deductible"], 0)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.purchase_tax.servincom_igic_deductible_percent = 101

    def test_reverse_charge_not_net_zero(self):
        self._invoice(self._tax("igic_ISP7"), "in_invoice")
        book = self._book()
        book.button_calculate()
        section = book._get_igic_report_sections()[1]
        self.assertAlmostEqual(section["base"], 100)
        self.assertAlmostEqual(section["fee"], 7)

    def test_dua_group(self):
        self._invoice(self._tax("igic_sop_i_7_group"), "in_invoice")
        book = self._book()
        book.button_calculate()
        section = book._get_igic_report_sections()[1]
        self.assertAlmostEqual(section["base"], 100)
        self.assertAlmostEqual(section["fee"], 7)
        self.assertEqual(len(section["rows"]), 1)

    def test_surcharge_does_not_duplicate_total_base(self):
        surcharge = self._tax("igic_p_re07")
        surcharge.servincom_igic_deductible_percent = 0
        self._invoice(self.purchase_tax | surcharge, "in_invoice")
        book = self._book()
        book.button_calculate()
        section = book._get_igic_report_sections()[1]
        self.assertEqual(len(section["rows"]), 2)
        self.assertAlmostEqual(section["base"], 100)
        self.assertAlmostEqual(section["fee"], 7.7)
        self.assertAlmostEqual(section["deductible"], 7)

    def test_export_guards_and_immutable_period(self):
        book = self._book()
        with self.assertRaises(UserError):
            book.action_print_igic()
        self._invoice(self.sale_tax)
        book.button_calculate()
        with self.assertRaises(UserError):
            book.write({"date_end": "2026-06-30"})
        with self.assertRaises(UserError):
            book.write({"servincom_is_igic": False})
        book.write({"date_end": "2026-03-31"})

    def test_company_domain_and_report_access(self):
        self._invoice(self.sale_tax)
        book = self._book()
        book.button_calculate()
        self.assertIn(
            ("company_id", "=", self.company.id), book._account_move_line_domain()
        )
        other = self.env["res.company"].create({"name": "Other test company"})
        user = new_test_user(
            self.env,
            login="igic_other_company",
            groups="account.group_account_user,l10n_es_aeat.group_account_aeat",
            company_id=other.id,
            company_ids=[Command.set(other.ids)],
        )
        hidden = book.with_user(user).with_context(allowed_company_ids=other.ids)
        with self.assertRaises(AccessError):
            hidden._get_igic_report_sections()
        self.assertFalse(
            self.env["l10n.es.vat.book.line"]
            .with_user(user)
            .with_context(allowed_company_ids=other.ids)
            .search([("id", "in", book.line_ids.ids)])
        )

    def test_pdf_html_and_xlsx_output(self):
        self.partner_a.name = "=1+1"
        self._invoice(self.sale_tax)
        book = self._book().with_context(lang="en_US")
        book.button_calculate()
        report = self.env.ref("servincom_igic_book.action_report_igic_pdf")
        html, _ = report._render_qweb_html(report.report_name, book.ids)
        self.assertIn(b"IGIC invoice book", html)
        self.assertIn(b"=1+1", html)
        xlsx = self.env["report.servincom_igic_book.igic_book_xlsx"]
        content, _ = xlsx.create_xlsx_report(book.ids, {})
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            for name in ("xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml"):
                sheet = ElementTree.fromstring(archive.read(name))
                self.assertFalse(sheet.findall(".//s:f", ns))
            strings = archive.read("xl/sharedStrings.xml")
            self.assertIn(b"=1+1", strings)
