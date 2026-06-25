odoo.define("servincom_pos_customer_credit_settlement.ClosingReport", function (require) {
    "use strict";

    const SaleDetailsButton = require("point_of_sale.SaleDetailsButton");
    const Registries = require("point_of_sale.Registries");
    const { renderToString } = require("@web/core/utils/render");

    const ClosingReportSaleDetailsButton = (OriginalSaleDetailsButton) =>
        class extends OriginalSaleDetailsButton {
            _toNumber(value) {
                return Number(value || 0);
            }

            _getPaymentState(paymentId) {
                const state = this.props.state || {};
                const payments = state.payments || {};
                return payments[paymentId] || {};
            }

            _getClosingReportData() {
                if (!this.props.ordersDetails) {
                    return false;
                }
                const cashDetails = this.props.defaultCashDetails || false;
                const closingData = {
                    orders: {
                        quantity: this._toNumber(this.props.ordersDetails.quantity),
                        amount: this._toNumber(this.props.ordersDetails.amount),
                    },
                    openingNotes: this.props.openingNotes || "",
                    notes: (this.props.state && this.props.state.notes) || "",
                    cashControl: Boolean(this.props.cashControl),
                    cash: false,
                    paymentMethods: [],
                };

                if (cashDetails) {
                    const cashState = this._getPaymentState(cashDetails.id);
                    closingData.cash = {
                        name: cashDetails.name,
                        expected: this._toNumber(cashDetails.amount),
                        counted: this._toNumber(cashState.counted),
                        difference: this._toNumber(cashState.difference),
                        opening: this._toNumber(cashDetails.opening),
                        paymentAmount: this._toNumber(cashDetails.payment_amount),
                        moves: (cashDetails.moves || []).map((move) => ({
                            name: move.name || "",
                            amount: this._toNumber(move.amount),
                        })),
                    };
                }

                closingData.paymentMethods = (this.props.otherPaymentMethods || []).map(
                    (paymentMethod) => {
                        const paymentState = this._getPaymentState(paymentMethod.id);
                        return {
                            id: paymentMethod.id,
                            name: paymentMethod.name,
                            expected: this._toNumber(paymentMethod.amount),
                            counted: this._toNumber(paymentState.counted),
                            difference: this._toNumber(paymentState.difference),
                            number: this._toNumber(paymentMethod.number),
                            type: paymentMethod.type,
                            showDifference:
                                paymentMethod.type === "bank" &&
                                this._toNumber(paymentMethod.number) !== 0,
                        };
                    }
                );
                return closingData;
            }

            async onClick() {
                const saleDetails = await this.rpc({
                    model: "report.point_of_sale.report_saledetails",
                    method: "get_sale_details",
                    args: [false, false, false, [this.env.pos.pos_session.id]],
                });
                const report = renderToString(
                    "SaleDetailsReport",
                    Object.assign({}, saleDetails, {
                        date: new Date().toLocaleString(),
                        pos: this.env.pos,
                        closingData: this._getClosingReportData(),
                    })
                );
                const printResult = await this.env.proxy.printer.print_receipt(report);
                if (!printResult.successful) {
                    await this.showPopup("ErrorPopup", {
                        title: printResult.message.title,
                        body: printResult.message.body,
                    });
                }
            }
        };

    Registries.Component.extend(SaleDetailsButton, ClosingReportSaleDetailsButton);

    return ClosingReportSaleDetailsButton;
});
