odoo.define("servincom_pos_closing_receipt.ReceiptSpacing", function (require) {
    "use strict";

    const { Printer, PrinterMixin } = require("point_of_sale.Printer");

    const FOOTER_FEED =
        '<div data-servincom-receipt-feed="1"><br/><br/><br/></div>';

    function addFooterFeed(receipt) {
        if (!receipt || receipt.indexOf("data-servincom-receipt-feed") !== -1) {
            return receipt;
        }
        const closingTag = "</div>";
        const closingIndex = receipt.lastIndexOf(closingTag);
        if (closingIndex === -1) {
            return receipt + FOOTER_FEED;
        }
        return (
            receipt.slice(0, closingIndex) +
            FOOTER_FEED +
            receipt.slice(closingIndex)
        );
    }

    const originalMixinPrintReceipt = PrinterMixin.print_receipt;
    PrinterMixin.print_receipt = async function (receipt) {
        return originalMixinPrintReceipt.call(this, addFooterFeed(receipt));
    };

    const originalPrinterPrintReceipt = Printer.prototype.print_receipt;
    Printer.include({
        async print_receipt(receipt) {
            return originalPrinterPrintReceipt.call(this, addFooterFeed(receipt));
        },
    });

    return {
        addFooterFeed,
    };
});
