# POS Product Variant Sale Price

This Odoo 18 Community addon makes the Point of Sale compatible with the OCA
`product_variant_sale_price` addon.

Odoo checks that a POS has at least one available product by searching the
`product.product.list_price` field. The OCA addon computes that field without
storing it, so the standard POS domain logs an error every time it prepares the
session information.

## Configuration

No additional configuration is required.

## Technical scope

- Replaces only the POS product-validity check that searches the non-stored
  field.
- Uses the stored variant `fix_price` and template `list_price` fields with the
  same semantics as `product_variant_sale_price`.
- Keeps the standard POS filters for availability, activity, and special
  products.
- Does not change pricelist computation, fixed variant prices, product brands,
  price categories, discounts, or POS product loading.

## Compatibility with custom pricelist scopes

Rules based on products, variants, product categories, brands, or price
categories continue to be evaluated by the standard pricelist engine. This
addon only prevents the preliminary POS validity check from searching a
non-stored field.

## Credits

Developed and maintained by SERVINCOM SOLUCIONES, S.L.
