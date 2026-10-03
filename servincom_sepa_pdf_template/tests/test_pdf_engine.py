# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""Run without Odoo: python -m unittest discover -s tests -p test_pdf_engine.py."""

import hashlib
import importlib.util
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sepa_pdf_engine", ROOT / "pdf_form.py")
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)


def serialize(writer):
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue()


class TestPdfEngine(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / "examples/mandato_sepa_core.pdf").read_bytes()
        self.values = {
            "mandate_reference": "DEMO-2026-001",
            "creditor_identifier": "DEMO-CREDITOR",
            "creditor_name": "Empresa Demostración, S.L.",
            "creditor_address": "Calle Ejemplo, 10",
            "creditor_postal_city_state": "28001 · Madrid · Madrid",
            "creditor_country": "España",
            "debtor_name": "Cliente Ficticio Muñoz",
            "debtor_address": "Avenida de Prueba, 20",
            "debtor_postal_city_state": "38001 · Santa Cruz de Tenerife",
            "debtor_country": "España",
            "debtor_iban": "ES00 0000 0000 0000 0000 0000",
            "debtor_bic": "DEMOESXX",
            "payment_recurrent": True,
            "payment_oneoff": False,
            "date_location": "Madrid, 02/10/2026",
            "debtor_signature": "MUST NEVER BE PRINTED",
        }

    def test_valid_all_fields_both_schemes(self):
        for scheme in ("core", "b2b"):
            result = engine.inspect_template(
                (ROOT / f"examples/mandato_sepa_{scheme}.pdf").read_bytes()
            )
            self.assertTrue(result["valid"], result)
            self.assertEqual(set(result["found"]), set(engine.REQUIRED_FIELDS))

    def test_flat(self):
        writer = PdfWriter()
        writer.add_blank_page(595, 842)
        self.assertIn("flat", engine.inspect_template(serialize(writer))["errors"])

    def test_missing_field(self):
        writer = PdfWriter(clone_from=BytesIO(self.template))
        field = writer.root_object["/AcroForm"]["/Fields"][0].get_object()
        field[NameObject("/T")] = TextStringObject("unknown_reference")
        result = engine.inspect_template(serialize(writer))
        self.assertFalse(result["valid"])
        self.assertIn("mandate_reference", result["missing"])
        self.assertIn("unknown_reference", result["unknown"])

    def test_non_pdf(self):
        self.assertFalse(engine.inspect_template(b"Not a PDF")["valid"])
        self.assertFalse(engine.inspect_template(b"%PDF-broken")["valid"])

    def test_encrypted(self):
        writer = PdfWriter(clone_from=BytesIO(self.template))
        writer.encrypt("test-only")
        self.assertFalse(engine.inspect_template(serialize(writer))["valid"])

    def test_wrong_checkbox_type(self):
        writer = PdfWriter(clone_from=BytesIO(self.template))
        for ref in writer.root_object["/AcroForm"]["/Fields"]:
            field = ref.get_object()
            if field.get("/T") == "payment_recurrent":
                field[NameObject("/FT")] = NameObject("/Tx")
        self.assertFalse(engine.inspect_template(serialize(writer))["valid"])

    def test_visible_values_one_page_original_intact(self):
        original_hash = hashlib.sha256(self.template).digest()
        output = engine.fill_template(self.template, self.values)
        reader = PdfReader(BytesIO(output))
        self.assertEqual(len(reader.pages), 1)
        self.assertFalse(reader.get_fields())
        self.assertNotIn("/AcroForm", reader.trailer["/Root"])
        self.assertFalse(
            any(
                a.get_object().get("/Subtype") == "/Widget"
                for a in reader.pages[0].get("/Annots", [])
            )
        )
        text = reader.pages[0].extract_text()
        for key in (
            "mandate_reference",
            "creditor_identifier",
            "creditor_name",
            "debtor_name",
            "debtor_iban",
            "debtor_bic",
        ):
            self.assertIn(self.values[key], text)
        self.assertNotIn("MUST NEVER BE PRINTED", text)
        self.assertEqual(
            original_hash,
            hashlib.sha256(
                (ROOT / "examples/mandato_sepa_core.pdf").read_bytes()
            ).digest(),
        )

    def test_payment_recurrent_visible_appearance(self):
        self._check_checkbox(True)

    def test_payment_oneoff_visible_appearance(self):
        self._check_checkbox(False)

    def _check_checkbox(self, recurrent):
        values = dict(
            self.values, payment_recurrent=recurrent, payment_oneoff=not recurrent
        )
        reader = PdfReader(BytesIO(engine.fill_template(self.template, values)))
        # Confirm actual painted appearance content, not /V values removed by flattening.
        page = reader.pages[0]
        painted = page.get_contents().get_data()
        resources = page["/Resources"]["/XObject"]
        original = PdfReader(BytesIO(self.template))
        for widget_ref in original.pages[0]["/Annots"]:
            widget = widget_ref.get_object()
            name = widget.get("/T")
            if name not in engine.CHECKBOX_FIELDS:
                continue
            appearances = widget["/AP"]["/N"]
            state = (
                next(k for k in appearances if k != "/Off") if values[name] else "/Off"
            )
            expected = appearances[state].get_object().get_data()
            matching = [
                str(key).encode()
                for key, ref in resources.items()
                if ref.get_object().get_data() == expected
            ]
            self.assertTrue(matching, name)
            self.assertTrue(any(key + b" Do" in painted for key in matching), name)

    def test_duplicate_canonical_field_rejected(self):
        writer = PdfWriter(clone_from=BytesIO(self.template))
        fields = writer.root_object["/AcroForm"]["/Fields"]
        fields.append(fields[0])
        self.assertFalse(engine.inspect_template(serialize(writer))["valid"])

    def test_orphan_widget_rejected(self):
        writer = PdfWriter(clone_from=BytesIO(self.template))
        writer.root_object["/AcroForm"]["/Fields"].pop()
        self.assertFalse(engine.inspect_template(serialize(writer))["valid"])

    def test_unsupported_runtime_rejected(self):
        with patch.object(engine, "runtime_supported", return_value=False):
            result = engine.inspect_template(self.template)
            self.assertFalse(result["valid"])
            self.assertIn("runtime", result["errors"])

    def test_signature_prefill_cleared(self):
        writer = PdfWriter(clone_from=BytesIO(self.template))
        writer.update_page_form_field_values(
            None, {"debtor_signature": "Old signature"}, auto_regenerate=False
        )
        result = PdfReader(
            BytesIO(engine.fill_template(serialize(writer), self.values))
        )
        self.assertNotIn("Old signature", result.pages[0].extract_text())


if __name__ == "__main__":
    unittest.main()
