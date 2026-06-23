# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "SERVINCOM Voxel IGIC Tax Type",
    "version": "18.0.1.4.0",
    "summary": "Adds IGIC tax type and keeps Voxel XML on failed sends",
    "category": "Accounting/EDI",
    "author": "SERVINCOM SOLUCIONES, S.L.",
    "license": "AGPL-3",
    "depends": [
        "edi_voxel_oca",
        "edi_voxel_account_invoice_oca",
    ],
    "data": [
        "views/voxel_template.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
}
