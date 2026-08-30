# POS Product Image Lazy Loading

This Odoo 18 Community addon keeps product images enabled in the Point of Sale
while reducing the initial burst of image requests.

Odoo renders up to 100 product cards at a time. By default, every card image is
requested immediately. This addon adds native browser lazy loading and
asynchronous image decoding to the existing POS product card, so images are
requested as they approach the visible area.

## Configuration

No additional configuration is required. Product images remain controlled by
the standard **Show Product Images** option of each Point of Sale.

## Usage

Install the addon and reopen the POS in a new browser tab. Images for visible
products load normally, while images below the visible area are deferred until
the cashier scrolls towards them.

## Technical scope

- Extends `point_of_sale.ProductCard` through an inherited Owl XML template.
- Adds `loading="lazy"` and `decoding="async"` to product card images.
- Does not modify Odoo core, image binaries, products, or POS configuration.

## Credits

Developed and maintained by SERVINCOM SOLUCIONES, S.L.
