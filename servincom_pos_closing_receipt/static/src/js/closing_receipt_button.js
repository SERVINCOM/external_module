odoo.define("servincom_pos_closing_receipt.ClosingReceiptButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const { renderToString } = require("@web/core/utils/render");

    class ServincomClosingReceiptButton extends PosComponent {
        _exportPaymentStates() {
            const exportedStates = {};
            const paymentStates = this.props.paymentStates || {};
            Object.keys(paymentStates).forEach((paymentId) => {
                const paymentState = paymentStates[paymentId] || {};
                exportedStates[paymentId] = {
                    counted: this._toNumber(paymentState.counted),
                    difference: this._toNumber(paymentState.difference),
                };
            });
            return exportedStates;
        }

        _toNumber(value) {
            if (value === undefined || value === null || value === "") {
                return null;
            }
            const parsed = Number(value);
            return Number.isFinite(parsed) ? parsed : null;
        }

        async onClick() {
            try {
                const receiptData = await this.rpc({
                    model: "pos.session",
                    method: "get_servincom_closing_receipt_data",
                    args: [this.env.pos.pos_session.id],
                    kwargs: {
                        closing_note: this.props.closingNote || "",
                        payment_states: this._exportPaymentStates(),
                    },
                });
                const receipt = renderToString(
                    "servincom_pos_closing_receipt.ClosingReceipt",
                    Object.assign({}, receiptData, { pos: this.env.pos })
                );
                const printResult = await this.env.proxy.printer.print_receipt(receipt);
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

        _getErrorMessage(error) {
            if (error && error.data && error.data.message) {
                return error.data.message;
            }
            if (error && error.message) {
                return error.message;
            }
            return this.env._t("Revise la configuración del TPV y la impresora.");
        }
    }

    ServincomClosingReceiptButton.template =
        "servincom_pos_closing_receipt.ClosingReceiptButton";

    Registries.Component.add(ServincomClosingReceiptButton);

    return ServincomClosingReceiptButton;
});
