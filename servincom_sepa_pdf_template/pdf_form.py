# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""Pure PDF engine; no Odoo dependency and no mutation of input bytes.

Requires flatten and remove_annotations APIs; tested with pypdf 6.10.0.
"""

import inspect
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

REQUIRED_FIELDS = (
    "mandate_reference",
    "creditor_identifier",
    "creditor_name",
    "creditor_address",
    "creditor_postal_city_state",
    "creditor_country",
    "debtor_name",
    "debtor_address",
    "debtor_postal_city_state",
    "debtor_country",
    "debtor_bic",
    "debtor_iban",
    "payment_recurrent",
    "payment_oneoff",
    "date_location",
    "debtor_signature",
)
CHECKBOX_FIELDS = {"payment_recurrent", "payment_oneoff"}
MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 20


class PdfTemplateError(ValueError):
    pass


def runtime_supported():
    return "flatten" in inspect.signature(
        PdfWriter.update_page_form_field_values
    ).parameters and hasattr(PdfWriter, "remove_annotations")


def _field_name(widget):
    names, visited = [], set()
    while widget:
        if id(widget) in visited:
            raise PdfTemplateError("Cyclic field hierarchy")
        visited.add(id(widget))
        if widget.get("/T"):
            names.insert(0, str(widget["/T"]))
        parent = widget.get("/Parent")
        widget = parent.get_object() if parent else None
    return ".".join(names)


def inspect_template(content):
    """Return diagnostics even for invalid input; never repair the source."""
    result = {"valid": False, "found": [], "missing": [], "unknown": [], "errors": []}
    try:
        if not runtime_supported():
            result["errors"].append("runtime")
        if not content or len(content) > MAX_BYTES or not content.startswith(b"%PDF-"):
            raise PdfTemplateError("Invalid PDF or size exceeds 10 MiB")
        reader = PdfReader(BytesIO(content), strict=True)
        if reader.is_encrypted or not 1 <= len(reader.pages) <= MAX_PAGES:
            raise PdfTemplateError("Encrypted PDF or invalid page count")
        form = reader.trailer["/Root"].get("/AcroForm")
        fields = reader.get_fields() or {}
        if not form or not fields:
            result["errors"].append("flat")
        elif form.get_object().get("/XFA"):
            result["errors"].append("xfa")
        result["found"] = sorted(fields)
        result["missing"] = sorted(set(REQUIRED_FIELDS) - set(fields))
        result["unknown"] = sorted(set(fields) - set(REQUIRED_FIELDS))
        canonical = {}

        def collect_fields(nodes, prefix=""):
            for ref in nodes:
                obj = ref.get_object()
                part = str(obj.get("/T", ""))
                name = ".".join(filter(None, [prefix, part]))
                if part:
                    if name in canonical:
                        raise PdfTemplateError("Duplicate canonical field")
                    canonical[name] = obj
                collect_fields(obj.get("/Kids", []), name)

        if form:
            collect_fields(form.get_object().get("/Fields", []))
        widgets = {}
        for page in reader.pages:
            for ref in page.get("/Annots", []):
                widget = ref.get_object()
                if widget.get("/Subtype") == "/Widget":
                    name = _field_name(widget)
                    owner = widget
                    while "/T" not in owner and owner.get("/Parent"):
                        owner = owner["/Parent"]
                    if name not in canonical or owner is not canonical[name]:
                        raise PdfTemplateError("Orphan or ambiguous widget")
                    widgets.setdefault(name, []).append(widget)
        for name, field in fields.items():
            if field.get("/FT") == "/Sig" and field.get("/V"):
                result["errors"].append("signed")
            if name not in REQUIRED_FIELDS:
                continue
            field_type = field.get("/FT")
            if name in CHECKBOX_FIELDS:
                valid_type = field_type == "/Btn" and not int(field.get("/Ff", 0)) & (
                    (1 << 15) | (1 << 16)
                )
            elif name == "debtor_signature":
                valid_type = field_type in ("/Tx", "/Sig")
            else:
                valid_type = field_type == "/Tx"
            visible = widgets.get(name, [])
            if not valid_type or len(visible) != 1:
                result["errors"].append("field:" + name)
                continue
            widget = visible[0]
            rect = widget.get("/Rect", [])
            if (
                len(rect) != 4
                or rect[2] <= rect[0]
                or rect[3] <= rect[1]
                or int(widget.get("/F", 0)) & 35
            ):
                result["errors"].append("field:" + name)
            if name in CHECKBOX_FIELDS:
                appearances = widget.get("/AP", {}).get("/N", {})
                if hasattr(appearances, "get_object"):
                    appearances = appearances.get_object()
                if "/Off" not in appearances or len(set(appearances) - {"/Off"}) != 1:
                    result["errors"].append("field:" + name)
        result["valid"] = not result["errors"] and not result["missing"]
    except Exception:
        result["errors"].append("invalid")
    return result


def fill_template(content, values):
    diagnostics = inspect_template(content)
    if not diagnostics["valid"]:
        raise PdfTemplateError("Incompatible PDF template")
    try:
        writer = PdfWriter(clone_from=BytesIO(content))
        fields = writer.get_fields() or {}
        payload = {}
        for name, field in fields.items():
            if field.get("/FT") == "/Sig":
                continue  # blank signature area is retained on the page
            if field.get("/FT") == "/Btn":
                states = [s for s in field.get("/_States_", []) if s != "/Off"]
                payload[name] = (
                    states[0]
                    if name in CHECKBOX_FIELDS and values.get(name) and states
                    else "/Off"
                )
            else:
                payload[name] = (
                    str(values.get(name) or "") if name in REQUIRED_FIELDS else ""
                )
        payload["debtor_signature"] = ""
        writer.update_page_form_field_values(
            None, payload, auto_regenerate=False, flatten=True
        )
        writer.remove_annotations(subtypes="/Widget")
        writer.root_object.pop(NameObject("/AcroForm"), None)
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception as exc:
        raise PdfTemplateError("PDF rendering failed") from exc
