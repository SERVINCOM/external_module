odoo.define("servincom_pos_customer_credit_settlement.CreditButton", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const PosComponent = require("point_of_sale.PosComponent");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const { _t } = require("web.core");

    class CreditButton extends PosComponent {
        async onClick() {
            if (!this.env.pos.config.enable_pos_customer_credit) {
                await this.showPopup("ErrorPopup", {
                    title: _t("Crédito TPV no activo"),
                    body: _t(
                        "Active la gestión de crédito de clientes en la configuración del punto de venta."
                    ),
                });
                return;
            }
            if (!this.env.pos.config.allow_pos_credit_settlement) {
                await this.showPopup("ErrorPopup", {
                    title: _t("Cobro de deuda no permitido"),
                    body: _t(
                        "Este punto de venta no permite cobrar deudas de clientes."
                    ),
                });
                return;
            }
            await this.showTempScreen("PosCreditPaymentScreen");
        }
    }

    CreditButton.template = "servincom_pos_customer_credit_settlement.CreditButton";

    ProductScreen.addControlButton({
        component: CreditButton,
        condition: function () {
            return this.env.pos.config.enable_pos_customer_credit;
        },
    });

    Registries.Component.add(CreditButton);

    const CreditPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async validateOrder(isForceValidate) {
                const order = this.currentOrder;
                const creditLines = order
                    .get_paymentlines()
                    .filter((line) => line.payment_method.is_pos_customer_credit);
                if (creditLines.length) {
                    const partner = order.get_partner();
                    if (!this.env.pos.config.enable_pos_customer_credit) {
                        await this.showPopup("ErrorPopup", {
                            title: _t("Crédito TPV no activo"),
                            body: _t(
                                "El punto de venta no tiene activada la gestión de crédito de clientes."
                            ),
                        });
                        return;
                    }
                    if (!partner) {
                        await this.showPopup("ErrorPopup", {
                            title: _t("Cliente obligatorio"),
                            body: _t(
                                "Seleccione un cliente antes de validar una venta a crédito."
                            ),
                        });
                        return;
                    }
                    if (!partner.pos_credit_customer) {
                        await this.showPopup("ErrorPopup", {
                            title: _t("Cliente no autorizado"),
                            body:
                                partner.display_name +
                                _t(" no está autorizado para crédito TPV."),
                        });
                        return;
                    }
                }
                return super.validateOrder(isForceValidate);
            }
        };

    Registries.Component.extend(PaymentScreen, CreditPaymentScreen);

    return CreditButton;
});
