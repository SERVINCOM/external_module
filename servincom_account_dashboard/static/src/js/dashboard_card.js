/** @odoo-module **/
// Copyright 2026 SERVINCOM SOLUCIONES, S.L.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";

// Native board actions pass the report through active_id, but do not forward
// res_id to the form. Bind our cards to that existing record so the standard
// form controller cannot auto-save an incomplete new MIS report on unload.
export class DashboardCardController extends FormController {
    get modelParams() {
        const params = super.modelParams;
        // View supplies context to the controller after parsing view props.
        const resId = this.props.context.active_id;
        return {
            ...params,
            config: { ...params.config, resId, resIds: [resId], mode: "readonly" },
        };
    }
}

export const dashboardCardView = { ...formView, Controller: DashboardCardController };

registry.category("views").add("servincom_dashboard_card", dashboardCardView);
