odoo.define("pos_customer_credit_settlement.CreditPaymentPopup", function (require) {
    "use strict";

    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const Registries = require("point_of_sale.Registries");
    const rpc = require("web.rpc");
    const { _t } = require("web.core");
    const { useState } = owl;

    class PosCreditPaymentPopup extends AbstractAwaitablePopup {
        setup() {
            super.setup();
            this.state = useState({
                query: "",
                customers: [],
                selectedPartner: null,
                lines: [],
                selectedLineIds: {},
                amount: "0.00",
                payment_method_id: "",
                loading: false,
            });
            const firstMethod = this.paymentMethods[0];
            if (firstMethod) {
                this.state.payment_method_id = String(firstMethod.id);
            }
            this.searchCustomers();
        }

        get paymentMethods() {
            return (this.env.pos.payment_methods || []).filter(
                (method) => !method.is_pos_customer_credit
            );
        }

        get selectedLines() {
            return this.state.lines.filter(
                (line) => this.state.selectedLineIds[line.id]
            );
        }

        get selectedTotal() {
            return this.selectedLines.reduce(
                (total, line) => total + line.amount_residual,
                0.0
            );
        }

        formatCurrency(amount) {
            if (this.env.pos.format_currency) {
                return this.env.pos.format_currency(amount);
            }
            return Number(amount || 0).toFixed(2);
        }

        getErrorMessage(error) {
            return (
                (error && error.data && error.data.message) ||
                (error && error.message) ||
                String(error)
            );
        }

        async onQueryInput(event) {
            this.state.query = event.target.value;
            await this.searchCustomers();
        }

        async searchCustomers() {
            this.state.loading = true;
            try {
                this.state.customers = await rpc.query({
                    model: "pos.customer.credit.payment",
                    method: "pos_search_credit_customers",
                    args: [this.state.query, 30],
                });
            } catch (error) {
                await this.showPopup("ErrorPopup", {
                    title: _t("Error buscando clientes"),
                    body: this.getErrorMessage(error),
                });
            } finally {
                this.state.loading = false;
            }
        }

        async selectPartner(partner) {
            this.state.selectedPartner = partner;
            this.state.selectedLineIds = {};
            this.state.lines = [];
            this.state.amount = "0.00";
            await this.loadCreditLines(partner.id);
        }

        async loadCreditLines(partnerId) {
            this.state.loading = true;
            try {
                this.state.lines = await rpc.query({
                    model: "pos.customer.credit.payment",
                    method: "pos_get_credit_lines",
                    args: [partnerId],
                });
            } catch (error) {
                await this.showPopup("ErrorPopup", {
                    title: _t("Error cargando deuda"),
                    body: this.getErrorMessage(error),
                });
            } finally {
                this.state.loading = false;
            }
        }

        toggleLine(line, event) {
            this.state.selectedLineIds[line.id] = event.target.checked;
            this.state.amount = this.selectedTotal.toFixed(2);
        }

        onAmountInput(event) {
            this.state.amount = event.target.value;
        }

        onPaymentMethodChange(event) {
            this.state.payment_method_id = event.target.value;
        }

        async confirmPayment() {
            if (!this.state.selectedPartner) {
                await this.showPopup("ErrorPopup", {
                    title: _t("Seleccione un cliente"),
                    body: _t("Debe seleccionar un cliente de crédito."),
                });
                return;
            }
            const selectedIds = this.selectedLines.map((line) => line.id);
            if (!selectedIds.length) {
                await this.showPopup("ErrorPopup", {
                    title: _t("Seleccione tickets"),
                    body: _t("Debe seleccionar al menos un ticket pendiente."),
                });
                return;
            }
            const amount = parseFloat(String(this.state.amount).replace(",", "."));
            if (!amount || amount <= 0) {
                await this.showPopup("ErrorPopup", {
                    title: _t("Importe no válido"),
                    body: _t("El importe a cobrar debe ser mayor que cero."),
                });
                return;
            }
            if (amount > this.selectedTotal + 0.00001) {
                await this.showPopup("ErrorPopup", {
                    title: _t("Importe no válido"),
                    body: _t(
                        "El importe a cobrar no puede superar el pendiente seleccionado."
                    ),
                });
                return;
            }
            if (!this.state.payment_method_id) {
                await this.showPopup("ErrorPopup", {
                    title: _t("Método de cobro obligatorio"),
                    body: _t("Seleccione un método real de cobro."),
                });
                return;
            }

            this.state.loading = true;
            try {
                const result = await rpc.query({
                    model: "pos.customer.credit.payment",
                    method: "pos_register_credit_payment",
                    args: [
                        this.state.selectedPartner.id,
                        selectedIds,
                        amount,
                        parseInt(this.state.payment_method_id, 10),
                        this.env.pos.pos_session.id,
                    ],
                });
                this.state.lines = result.lines;
                this.state.selectedLineIds = {};
                this.state.amount = "0.00";
                this.state.selectedPartner.total_due = result.remaining_due;
                await this.showPopup("ConfirmPopup", {
                    title: _t("Cobro registrado"),
                    body:
                        _t("Se ha registrado el cobro ") +
                        result.name +
                        _t(" por ") +
                        this.formatCurrency(result.amount) +
                        ".",
                });
            } catch (error) {
                await this.showPopup("ErrorPopup", {
                    title: _t("No se pudo registrar el cobro"),
                    body: this.getErrorMessage(error),
                });
            } finally {
                this.state.loading = false;
            }
        }
    }

    PosCreditPaymentPopup.template =
        "pos_customer_credit_settlement.PosCreditPaymentPopup";
    PosCreditPaymentPopup.defaultProps = {
        confirmText: _t("Cobrar"),
        cancelText: _t("Cerrar"),
        title: _t("Cobrar deuda"),
    };

    Registries.Component.add(PosCreditPaymentPopup);

    return PosCreditPaymentPopup;
});
