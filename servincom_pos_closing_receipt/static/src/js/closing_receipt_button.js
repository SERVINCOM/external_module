odoo.define("servincom_pos_closing_receipt.ClosingReceiptButton", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const SaleDetailsButton = require("point_of_sale.SaleDetailsButton");
    const { renderToString } = require("@web/core/utils/render");
    const { parse } = require("web.field_utils");

    const ServincomClosingReceiptSaleDetailsButton = (SaleDetailsButton) =>
        class extends SaleDetailsButton {
            async onClick() {
                const popup = this._getClosingPopup();
                if (!popup) {
                    return super.onClick();
                }
                try {
                    const receiptData = await this.rpc({
                        model: "pos.session",
                        method: "get_servincom_closing_receipt_data",
                        args: [this.env.pos.pos_session.id],
                        kwargs: {
                            closing_note: this._getClosingNote(popup),
                            counted_values: this._getCountedValues(popup),
                        },
                    });
                    const receipt = renderToString(
                        "servincom_pos_closing_receipt.ClosingReceipt",
                        Object.assign({}, receiptData, { pos: this.env.pos })
                    );
                    const printResult = await this.env.proxy.printer.print_receipt(
                        receipt
                    );
                    if (!printResult.successful) {
                        await this.showPopup("ErrorPopup", {
                            title: printResult.message.title,
                            body: printResult.message.body,
                        });
                    }
                } catch (error) {
                    await this.showPopup("ErrorPopup", {
                        title: this.env._t("No se pudo imprimir el cierre"),
                        body: this._getErrorMessage(error),
                    });
                }
            }

            _getClosingPopup() {
                if (this.el && this.el.closest) {
                    return this.el.closest(".close-pos-popup");
                }
                return document.querySelector(".close-pos-popup");
            }

            _getClosingNote(popup) {
                const closingNote = popup.querySelector(".closing-notes");
                return closingNote ? closingNote.value : "";
            }

            _getCountedValues(popup) {
                const inputs = popup.querySelectorAll(
                    ".payment-methods-overview input.pos-input"
                );
                return Array.from(inputs).map((input) =>
                    this._parseCountedValue(input.value)
                );
            }

            _parseCountedValue(value) {
                if (value === undefined || value === null || value === "") {
                    return null;
                }
                try {
                    return parse.float(value);
                } catch (error) {
                    const normalized = String(value)
                        .replace(/\s/g, "")
                        .replace(",", ".");
                    const parsed = Number(normalized);
                    return Number.isFinite(parsed) ? parsed : null;
                }
            }

            _getErrorMessage(error) {
                if (error && error.data && error.data.message) {
                    return error.data.message;
                }
                if (error && error.message) {
                    return error.message;
                }
                return this.env._t("Revise la configuración del TPV y la impresora.");
            }
        };

    Registries.Component.extend(
        SaleDetailsButton,
        ServincomClosingReceiptSaleDetailsButton
    );

    return ServincomClosingReceiptSaleDetailsButton;
});
