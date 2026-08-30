# POS Product Image Lazy Loading

This Odoo 18 Community addon keeps product images enabled in the Point of Sale
while reducing the initial burst of image requests.

Odoo renders up to 100 product cards at a time. By default, every card image is
requested immediately. This addon observes the existing POS product cards and
queues their images as they approach the visible area. At most eight images are
requested concurrently in each browser tab.

## Configuration

No additional configuration is required. Product images remain controlled by
the standard **Show Product Images** option of each Point of Sale.

## Usage

Install the addon and reopen the POS in a new browser tab. Images for visible
products load normally, while images below the visible area are deferred until
the cashier scrolls towards them. Changing category cancels pending requests for
cards that are no longer rendered.

## Technical scope

- Extends `point_of_sale.ProductCard` through an inherited Owl XML template.
- Uses `IntersectionObserver` to start loading images close to the viewport.
- Limits active image downloads to eight per browser tab.
- Cancels queued cards cleanly when Owl unmounts them.
- Keeps native `loading="lazy"` and asynchronous image decoding as secondary
  browser optimizations.
- Does not modify Odoo core, image binaries, products, or POS configuration.

## Credits

Developed and maintained by SERVINCOM SOLUCIONES, S.L.
