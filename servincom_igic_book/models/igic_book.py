# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.exceptions import UserError


class L10nEsVatBook(models.Model):
    _inherit = "l10n.es.vat.book"

    servincom_is_igic = fields.Boolean(string="IGIC book", copy=True)

    def write(self, vals):
        protected = {
            "servincom_is_igic",
            "company_id",
            "date_start",
            "date_end",
            "year",
            "period_type",
        }
        if protected.intersection(vals):
            for book in self:
                if (
                    book.servincom_is_igic or vals.get("servincom_is_igic")
                ) and book.line_ids:
                    changed = False
                    for field in protected.intersection(vals):
                        old_value = (
                            book[field].id if field == "company_id" else book[field]
                        )
                        new_value = vals[field]
                        if field in ("date_start", "date_end"):
                            new_value = fields.Date.to_date(new_value)
                        changed |= old_value != new_value
                    if changed:
                        raise UserError(
                            self.env._(
                                "Create a new book to change the company, "
                                "period or tax system "
                                "of a calculated IGIC book."
                            )
                        )
        return super().write(vals)

    def _calculate_vat_book(self):
        for book in self:
            current = book.with_context(servincom_igic_book=book.servincom_is_igic)
            if book.servincom_is_igic:
                book.check_access("write")
                current = current.with_company(book.company_id).with_context(
                    allowed_company_ids=[book.company_id.id]
                )
                maps = current.env["aeat.vat.book.map.line"].search(
                    [("servincom_is_igic", "=", True)]
                )
                taxes = current.env["account.tax"]
                for mapping in maps:
                    taxes |= mapping.get_taxes_for_company(book.company_id)
                if not taxes:
                    raise UserError(
                        self.env._(
                            "No mapped IGIC taxes were found for this company. "
                            "Check the Canary Islands chart and equivalent taxes."
                        )
                    )
            super(L10nEsVatBook, current)._calculate_vat_book()
        return True

    def _account_move_line_domain(self, taxes=None, account=None):
        domain = super()._account_move_line_domain(taxes=taxes, account=account)
        if self.servincom_is_igic:
            domain.append(("company_id", "=", self.company_id.id))
        return domain

    def get_special_taxes_dic(self):
        if not self.servincom_is_igic:
            return super().get_special_taxes_dic()
        result = {}
        mappings = (
            self.env["aeat.vat.book.map.line"]
            .with_context(servincom_igic_book=True)
            .search(
                [("servincom_is_igic", "=", True), ("special_tax_group", "!=", False)]
            )
        )
        for mapping in mappings:
            for tax in mapping.get_taxes_for_company(self.company_id):
                result[tax.id] = {
                    "name": mapping.name,
                    "book_type": mapping.book_type,
                    "special_tax_group": mapping.special_tax_group,
                    "fee_type_xlsx_column": False,
                    "fee_amount_xlsx_column": False,
                }
        return result

    def upsert_book_line_tax(self, move_line, vat_book_line, implied_taxes):
        if not self.servincom_is_igic:
            return super().upsert_book_line_tax(move_line, vat_book_line, implied_taxes)
        sign = 1 if vat_book_line["line_type"] == "received" else -1
        tax_lines = vat_book_line["tax_lines"]

        def get_values(tax):
            key = self.get_book_line_tax_key(move_line, tax)
            return tax_lines.setdefault(
                key,
                {
                    "tax_id": tax.id,
                    "base_amount": 0.0,
                    "tax_amount": 0.0,
                    "deductible_amount": 0.0,
                    "base_move_line_ids": [],
                    "move_line_ids": [],
                    "special_tax_group": False,
                },
            )

        if (
            move_line.tax_line_id in implied_taxes
            and move_line.tax_repartition_line_id.factor_percent >= 0
        ):
            tax = move_line.tax_line_id
            values = get_values(tax)
            fee = move_line.balance * sign
            values["tax_amount"] += fee
            if sign == 1:
                values["deductible_amount"] += self.currency_id.round(
                    fee * tax.servincom_igic_deductible_percent / 100.0
                )
            values["move_line_ids"].append((4, move_line.id))
        # Group taxes (DUA) must be flattened; never treat the auxiliary
        # negative base-adjustment tax as IGIC or count the invoice base twice.
        leaves = move_line.tax_ids.flatten_taxes_hierarchy()
        relevant = leaves & implied_taxes
        if relevant:
            base = move_line.balance * sign
            vat_book_line["base_amount"] += base
            for tax in relevant:
                values = get_values(tax)
                values["base_amount"] += base
                values["base_move_line_ids"].append((4, move_line.id))
                values["other_tax_ids"] = (relevant - tax).ids

    def _check_igic_export(self):
        self.ensure_one()
        self.check_access("read")
        if not self.servincom_is_igic or self.state not in ("calculated", "done"):
            raise UserError(self.env._("Calculate an IGIC book before exporting it."))

    def action_print_igic(self):
        self._check_igic_export()
        return self.env.ref("servincom_igic_book.action_report_igic_pdf").report_action(
            self
        )

    def export_xlsx(self):
        self.ensure_one()
        if not self.servincom_is_igic:
            return super().export_xlsx()
        self._check_igic_export()
        return self.env.ref(
            "servincom_igic_book.action_report_igic_xlsx"
        ).report_action(self)

    def _get_igic_report_sections(self):
        """One snapshot feeds both formats; totals never sum duplicate tax bases."""
        self._check_igic_export()
        sections = []
        for kind, title in (
            ("issued", self.env._("Issued invoices")),
            ("received", self.env._("Received invoices")),
        ):
            lines = self.line_ids.filtered(
                lambda line, kind=kind: (
                    line.line_type in (kind, "rectification_" + kind)
                )
            ).sorted(
                lambda line: (
                    line.invoice_date or fields.Date.from_string("1900-01-01"),
                    line.ref or "",
                    line.id,
                )
            )
            rows = []
            summary = {}
            for number, line in enumerate(lines, 1):
                for tax_line in line.tax_line_ids.sorted(
                    lambda tax_line: tax_line.tax_id.id
                ):
                    tax = tax_line.tax_id
                    row = {
                        "number": number,
                        "date": line.invoice_date,
                        "accounting_date": line.move_id.date,
                        "reference": line.ref or "",
                        "external_reference": line.external_ref or "",
                        "partner": line.partner_id.display_name or "",
                        "vat": line.vat_number or "",
                        "tax": tax.description or tax.name,
                        "rate": tax_line.tax_rate,
                        "base": tax_line.base_amount,
                        "fee": tax_line.tax_amount,
                        "deductible": tax_line.deductible_amount
                        if kind == "received"
                        else 0.0,
                        "refund": line.line_type.startswith("rectification_"),
                        "warning": line.exception_text or "",
                    }
                    rows.append(row)
                    total = summary.setdefault(
                        tax.id,
                        {
                            "tax": row["tax"],
                            "rate": row["rate"],
                            "base": 0.0,
                            "fee": 0.0,
                            "deductible": 0.0,
                        },
                    )
                    for key in ("base", "fee", "deductible"):
                        total[key] += row[key]
            sections.append(
                {
                    "kind": kind,
                    "title": title,
                    "rows": rows,
                    "summary": list(summary.values()),
                    "invoice_count": len(lines),
                    "base": sum(lines.mapped("base_amount")),
                    "fee": sum(row["fee"] for row in rows),
                    "deductible": sum(row["deductible"] for row in rows),
                }
            )
        return sections
