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
                const legacyIdentifierEnabled =
                    this.pos.config.servincom_anonymize_receipt_operator;
                const customizeOperator =
                    this.pos.config.servincom_customize_receipt_operator !==
                    undefined
                        ? this.pos.config.servincom_customize_receipt_operator
                        : legacyIdentifierEnabled;
                if (!customizeOperator) {
                    return receipt;
                }
                const displayMode =
                    this.pos.config.servincom_receipt_operator_display ||
                    (legacyIdentifierEnabled ? "identifier" : "name");
                if (displayMode === "name") {
                    return receipt;
                }
                if (displayMode === "hidden") {
                    receipt.cashier = false;
                    return receipt;
                }

                const cashier = this.cashier;
                const configuredLabel =
                    cashier && cashier.servincom_pos_receipt_operator_label;
                const fallbackLabel =
                    cashier && cashier.id
                        ? `${_t("POS operator")} ${cashier.id}`
                        : _t("POS operator");
                receipt.cashier = configuredLabel || fallbackLabel;
                return receipt;
            }
        };

    Registries.Model.extend(Order, ServincomReceiptOrder);

    return ServincomReceiptOrder;
});
