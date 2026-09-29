# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "SERVINCOM IGIC Book",
    "summary": "IGIC invoice books with PDF and Excel reports",
    "version": "18.0.1.0.1",
    "category": "Accounting/Localizations/Reporting",
    "author": "SERVINCOM SOLUCIONES, S.L.",
    "website": "https://www.servincom.com",
    "license": "AGPL-3",
    "depends": ["l10n_es_vat_book", "report_xlsx"],
    "data": [
        "security/igic_book_rules.xml",
        "data/igic_tax_maps.xml",
        "views/account_tax_views.xml",
        "views/igic_book_views.xml",
        "reports/igic_book_templates.xml",
        "reports/igic_book_actions.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
}
