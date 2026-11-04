odoo.define("servincom_pos_closing_receipt.OrderReceipt", function (require) {
    "use strict";

    const { Order } = require("point_of_sale.models");
    const Registries = require("point_of_sale.Registries");
    const core = require("web.core");

    const _t = core._t;

    const ServincomReceiptOrder = (Order) =>
        class extends Order {
            export_for_printing() {
                const receipt = super.export_for_printing(...arguments);
                if (!this.pos.config.servincom_anonymize_receipt_operator) {
                    return receipt;
                }

                const cashier = this.cashier;
                const configuredLabel =
                    cashier && cashier.servincom_pos_receipt_operator_label;
                const fallbackLabel =
                    cashier && cashier.id
                        ? `${_t("Operator")} ${cashier.id}`
                        : _t("Operator");
                receipt.cashier = configuredLabel || fallbackLabel;
                return receipt;
            }
        };

    Registries.Model.extend(Order, ServincomReceiptOrder);

    return ServincomReceiptOrder;
});
