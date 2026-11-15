/** @odoo-module **/
// Copyright 2026 SERVINCOM SOLUCIONES, S.L.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";

// Native board actions pass the report through active_id, but do not forward
// res_id to the form. Bind our cards to that existing record so the standard
// form controller cannot auto-save an incomplete new MIS report on unload.
export const dashboardCardView = {
    ...formView,
    props(genericProps, view) {
        const props = formView.props(genericProps, view);
        const resId = props.context.active_id;
        return { ...props, resId, resIds: [resId], mode: "readonly" };
    },
};

registry.category("views").add("servincom_dashboard_card", dashboardCardView);
