# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged
from pypdf import PdfReader

from ..models.ir_actions_report import SEPA_REPORT, IrActionsReport
from ..pdf_form import PdfTemplateError


@tagged("post_install", "-at_install")
class TestSepaPdf(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        examples = Path(__file__).resolve().parents[1] / "examples"
        cls.core = base64.b64encode((examples / "mandato_sepa_core.pdf").read_bytes())
        cls.b2b = base64.b64encode((examples / "mandato_sepa_b2b.pdf").read_bytes())
        cls.company = cls.env.company
        cls.company.write(
            {
                "sepa_pdf_core": cls.core,
                "sepa_pdf_core_filename": "core.pdf",
                "sepa_pdf_enabled": True,
            }
        )
        cls.other = cls.env["res.company"].create({"name": "SEPA Test Other"})
        cls.partner = cls.env["res.partner"].create(
            {"name": "SEPA Test Debtor", "email": "sepa@example.invalid"}
        )
        cls.bank = cls.env["res.bank"].create({"name": "Test Bank", "bic": "DEMOESXX"})
        cls.account = cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.partner.id,
                "acc_number": "TEST-ACCOUNT-001",
                "bank_id": cls.bank.id,
            }
        )
        cls.mandate = cls.env["account.banking.mandate"].create(
            {
                "company_id": cls.company.id,
                "partner_bank_id": cls.account.id,
                "unique_mandate_reference": "SEPA-PDF-TEST",
                "format": "sepa",
                "scheme": "CORE",
                "type": "recurrent",
            }
        )
        cls.report = cls.env.ref(SEPA_REPORT)

    def _report_parent_class(self):
        mro = type(self.env["ir.actions.report"]).__mro__
        return next(
            cls
            for cls in mro[mro.index(IrActionsReport) + 1 :]
            if "_render_qweb_pdf_prepare_streams" in cls.__dict__
        )

    def test_activation_rejects_invalid(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.company.write({"sepa_pdf_core": base64.b64encode(b"broken")})

    def test_validation_audit(self):
        self.company.write({"sepa_pdf_core": self.core})
        self.assertTrue(self.company.sepa_pdf_validation_date)
        self.assertEqual(self.company.sepa_pdf_validation_user_id, self.env.user)
        with self.assertRaises(AccessError):
            self.company.write({"sepa_pdf_validation_result": "forged"})

    def test_multi_company_and_schemes(self):
        self.assertEqual(self.mandate._sepa_pdf_template()[0], self.core)
        self.company.write({"sepa_pdf_b2b": self.b2b})
        self.mandate.scheme = "B2B"
        self.assertEqual(self.mandate._sepa_pdf_template()[0], self.b2b)
        other_mandate = self.mandate.copy(
            {"company_id": self.other.id, "unique_mandate_reference": "OTHER"}
        )
        self.assertFalse(other_mandate._sepa_render_custom_pdf())
        self.other.write({"sepa_pdf_core": self.b2b, "sepa_pdf_enabled": True})
        other_mandate.scheme = "CORE"
        self.assertEqual(other_mandate._sepa_pdf_template()[0], self.b2b)
        self.assertEqual(self.company.sepa_pdf_core, self.core)

    def test_mapping_and_date(self):
        values = self.mandate._sepa_pdf_values()
        self.assertEqual(values["mandate_reference"], "SEPA-PDF-TEST")
        self.assertEqual(values["creditor_name"], self.company.name)
        self.assertEqual(values["debtor_name"], self.partner.name)
        self.assertEqual(values["debtor_iban"], "TEST-ACCOUNT-001")
        self.assertEqual(values["debtor_bic"], "DEMOESXX")
        self.assertTrue(values["payment_recurrent"])
        self.assertFalse(values["payment_oneoff"])
        self.assertFalse(values["date_location"])
        self.mandate.write(
            {
                "type": "oneoff",
                "signature_date": "2020-01-01",
                "sepa_signature_city": "Madrid",
            }
        )
        values = self.mandate._sepa_pdf_values()
        self.assertTrue(values["payment_oneoff"])
        self.assertFalse(values["payment_recurrent"])
        self.assertIn("Madrid", values["date_location"])

    def test_dynamic_mail_attachment(self):
        template = self.env.ref(
            "account_banking_sepa_direct_debit.email_template_sepa_mandate"
        )
        result = template.with_context(
            force_report_rendering=True
        )._generate_template_attachments(self.mandate.ids, ["report_template_ids"])
        attachments = result[self.mandate.id]["attachments"]
        self.assertEqual(len(attachments), 1)
        filename, content = attachments[0]
        self.assertTrue(filename.startswith("Mandato-SEPA-PDF-TEST-"))
        reader = PdfReader(BytesIO(base64.b64decode(content)))
        self.assertEqual(len(reader.pages), 1)
        self.assertIn("SEPA-PDF-TEST", reader.pages[0].extract_text())
        self.assertFalse(reader.get_fields())
        self.assertEqual(self.company.sepa_pdf_core, self.core)

    def test_original_report_when_disabled(self):
        self.company.sepa_pdf_enabled = False
        base = self._report_parent_class()
        with patch.object(
            base,
            "_render_qweb_pdf_prepare_streams",
            return_value={
                self.mandate.id: {"stream": BytesIO(b"original"), "attachment": None}
            },
        ) as original:
            result = self.env["ir.actions.report"]._render_qweb_pdf_prepare_streams(
                self.report, {}, self.mandate.ids
            )
            self.assertEqual(result[self.mandate.id]["stream"].getvalue(), b"original")
            original.assert_called_once()

    def test_other_reports_unchanged(self):
        other = self.env["ir.actions.report"].create(
            {
                "name": "Unrelated test",
                "model": "res.partner",
                "report_type": "qweb-pdf",
                "report_name": "sepa_test.unrelated",
            }
        )
        base = self._report_parent_class()
        with patch.object(
            base, "_render_qweb_pdf_prepare_streams", return_value={}
        ) as original:
            self.env["ir.actions.report"]._render_qweb_pdf_prepare_streams(
                other, {}, [self.partner.id]
            )
            original.assert_called_once_with(other, {}, res_ids=[self.partner.id])

    def test_corrupt_pdf_uses_original(self):
        base = self._report_parent_class()
        with (
            patch.object(
                type(self.mandate),
                "_sepa_render_custom_pdf",
                side_effect=PdfTemplateError("corrupt"),
            ),
            patch.object(
                base,
                "_render_qweb_pdf_prepare_streams",
                return_value={
                    self.mandate.id: {
                        "stream": BytesIO(b"fallback"),
                        "attachment": None,
                    }
                },
            ),
        ):
            result = self.env["ir.actions.report"]._render_qweb_pdf_prepare_streams(
                self.report, {}, self.mandate.ids
            )
            self.assertEqual(result[self.mandate.id]["stream"].getvalue(), b"fallback")

    def test_regular_user_cannot_configure(self):
        user = self.env["res.users"].create(
            {
                "name": "SEPA Reader",
                "login": "sepa_reader_test",
                "groups_id": [Command.set([self.env.ref("base.group_user").id])],
            }
        )
        with self.assertRaises(AccessError):
            self.company.with_user(user).write({"sepa_pdf_enabled": False})

    def test_preview_company_guard(self):
        wizard = self.env["servincom.sepa.pdf.preview"].create(
            {"company_id": self.company.id, "mandate_id": self.mandate.id}
        )
        action = wizard.action_preview()
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertTrue(wizard.pdf_file)

    def test_spanish_code_translations(self):
        from odoo.tools.translate import code_translations

        translations = code_translations.get_python_translations(
            "servincom_sepa_pdf_template", "es_ES"
        )
        self.assertEqual(translations["PDF validation"], "Validación del modelo PDF")
        self.assertEqual(
            translations["Preview SEPA mandate"], "Previsualizar mandato SEPA"
        )
        self.assertEqual(
            translations["PDF validation successful."], "Validación del PDF correcta."
        )

    def test_spanish_related_field_occurrences(self):
        import polib

        catalog = polib.pofile(str(Path(__file__).resolve().parents[1] / "i18n/es.po"))
        for source, field in (
            ("Last PDF validation", "sepa_pdf_validation_result"),
            ("Validation date", "sepa_pdf_validation_date"),
            ("Validated by", "sepa_pdf_validation_user_id"),
        ):
            occurrence = (
                "model:ir.model.fields,field_description:servincom_sepa_pdf_template."
                "field_res_config_settings__" + field
            )
            self.assertIn(
                occurrence, [ref for ref, line in catalog.find(source).occurrences]
            )
