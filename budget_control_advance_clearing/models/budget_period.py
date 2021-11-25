# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class BudgetPeriod(models.Model):
    _inherit = "budget.period"

    advance = fields.Boolean(
        string="On Advance",
        default=True,
        readonly=True,
        help="Control budget on advance approved",
    )

    def _create_budget_move_periods(self):
        periods = super()._create_budget_move_periods()
        if self.advance:
            Period = self.env["mis.report.instance.period"]
            advance_model = self.env.ref(
                "budget_control_advance_clearing.model_advance_budget_move"
            )
            advance = Period.create(
                {
                    "name": "Advance",
                    "report_instance_id": self.report_instance_id.id,
                    "sequence": 50,
                    "source": "actuals_alt",
                    "source_aml_model_id": advance_model.id,
                    "mode": "fix",
                    "manual_date_from": self.bm_date_from,
                    "manual_date_to": self.bm_date_to,
                }
            )
            periods.update({advance: "-"})
        return periods

    def _budget_info_query(self):
        query = super()._budget_info_query()
        query["info_cols"]["amount_advance"] = ("4_av_commit", True)
        return query

    def _compute_budget_info(self, **kwargs):
        """ Add more data info budget_info, based on installed modules """
        super()._compute_budget_info(**kwargs)
        self._set_budget_info_amount(
            "amount_advance",
            [("source_aml_model_id.model", "=", "advance.budget.move")],
            kwargs,
            is_commit=True,
        )

    @api.model
    def check_budget(self, doclines, doc_type="account"):
        if not doclines:
            return
        if doclines._name == "hr.expense":
            sheet = doclines.mapped("sheet_id")
            sheet.ensure_one()
            if sheet.advance:
                doc_type = "advance"
                doclines = doclines.with_context(
                    alt_budget_move_model="advance.budget.move",
                    alt_budget_move_field="advance_budget_move_ids",
                )
        return super().check_budget(doclines, doc_type=doc_type)

    @api.model
    def check_budget_precommit(self, doclines, doc_type="account"):
        """ If the clearing has related advance, uncommit first """
        budget_moves = False
        if doclines._name == "hr.expense":
            clearings = doclines.mapped("sheet_id").filtered("advance_sheet_id")
            budget_moves = (
                clearings.mapped("expense_line_ids")
                .with_context(force_commit=True)
                .uncommit_advance_budget()
            )
        super().check_budget_precommit(doclines, doc_type=doc_type)
        if budget_moves:
            budget_moves.unlink()
