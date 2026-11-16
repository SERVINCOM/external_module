/** @odoo-module **/
// Copyright 2026 SERVINCOM SOLUCIONES, S.L.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

import { registry } from "@web/core/registry";
import { BoardController } from "@board/board_controller";
import { boardView } from "@board/board_view";

export class ResultsBoardController extends BoardController {
    static template = "servincom_account_dashboard.ResultsBoard";

    // These report cards are part of the results view. Only folding and layout
    // changes are available here; ordinary personal dashboards stay unchanged.
    closeAction() {}
}

registry.category("views").add("servincom_results_board", {
    ...boardView,
    Controller: ResultsBoardController,
});
