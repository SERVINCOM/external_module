odoo.define("servincom_pos_customer_credit_settlement.CreditButton", function (require) {
    "use strict";

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
            await this.showPopup("PosCreditPaymentPopup", {
                title: _t("Cobrar deuda"),
            });
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
    return CreditButton;
});
