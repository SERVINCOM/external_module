# SERVINCOM Odoo Module Guidelines

These rules apply when creating or modifying Odoo modules in this repository.

## Module Scope

- Target Odoo 16 Community.
- Use the `servincom_` prefix for new SERVINCOM modules.
- Keep modules independent unless a dependency is technically required.
- Avoid changing unrelated modules or shared POS behavior when implementing a focused feature.

## Required SERVINCOM Metadata

Every new SERVINCOM module must include:

- SERVINCOM naming in the manifest `name`.
- `author`: `SERVINCOM SOLUCIONES, S.L.`
- `license`: `AGPL-3`
- Odoo/OCA-style versioning, for example `16.0.1.0.0`.
- A clear `summary`, `category`, `depends`, `data`, `assets` if needed, `installable`, and `application`.
- `static/description/icon.png` with the SERVINCOM icon.
- An `i18n/` directory with at least `es.po`.
- A README file explaining purpose, configuration, usage, and test notes.

## OCA-Oriented Quality Rules

- Follow OCA-style module structure and conventions where practical.
- Use XML IDs, security files, access rules, and views with stable naming.
- Keep manifests valid Python dictionaries.
- Keep XML files valid and parseable.
- Do not commit generated caches such as `__pycache__`.
- Validate changed Python, XML, and manifest files before committing.
- Bump the module version when behavior or assets change.

## POS Module Rules

- For POS JavaScript in Odoo 16, inspect the existing POS component/template before patching it.
- Prefer small, isolated extensions over broad overrides.
- Do not break core POS flows: product screen, payment button, customer selector, order list, return/back buttons, session opening, or session closing.
- If adding or changing POS assets, ensure they are declared in the module manifest under `point_of_sale.assets`.
- When a requested change touches the POS closing popup or printed closing receipt, first inspect the exact Odoo printing point and confirm the approach before implementing.
