odoo.define("servincom_pos_customer_credit_settlement.CreditButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const rpc = require("web.rpc");
    const { _t } = require("web.core");

    class CreditButton extends PosComponent {
        async onClick() {
            let creditConfig;
            try {
                creditConfig = await rpc.query({
                    model: "pos.customer.credit.payment",
                    method: "pos_get_credit_config",
                    args: [this.env.pos.config.id],
                });
            } catch (error) {
                await this.showPopup("ErrorPopup", {
                    title: _t("No se pudo abrir crédito TPV"),
                    body:
                        (error && error.data && error.data.message) ||
                        (error && error.message) ||
                        _t("Revise la configuración del punto de venta."),
                });
                return;
            }
            if (!creditConfig.enable_pos_customer_credit) {
                await this.showPopup("ErrorPopup", {
                    title: _t("Crédito TPV no activo"),
                    body: _t(
                        "Active la gestión de crédito de clientes en la configuración del punto de venta."
                    ),
                });
                return;
            }
            if (!creditConfig.allow_pos_credit_settlement) {
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
            return true;
        },
    });

    Registries.Component.add(CreditButton);
    return CreditButton;
});
