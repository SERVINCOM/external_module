# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "SERVINCOM SEPA PDF Template",
    "summary": "Fill company-specific AcroForm PDF templates for SEPA mandates",
    "version": "18.0.1.0.2",
    "license": "AGPL-3",
    "author": "SERVINCOM SOLUCIONES, S.L.",
    "website": "https://www.servincom.com",
    "category": "Accounting",
    "depends": ["account_banking_sepa_direct_debit"],
    "external_dependencies": {"python": ["pypdf"]},
    "data": [
        "security/ir.model.access.csv",
        "security/sepa_preview_security.xml",
        "views/res_config_settings_views.xml",
        "views/account_banking_mandate_views.xml",
        "wizard/sepa_preview_views.xml",
    ],
    "demo": [],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
}
