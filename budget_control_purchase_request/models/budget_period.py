# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetPeriod(models.Model):
    _inherit = "budget.period"

    purchase_request = fields.Boolean(
        string="On Purchase Request",
        default=False,
        help="Control budget on purchase request approved",
    )

    def _create_budget_move_periods(self):
        periods = super()._create_budget_move_periods()
        if self.purchase_request:
            Period = self.env["mis.report.instance.period"]
            model = self.env.ref(
                "budget_control_purchase_request.model_purchase_request_budget_move"
            )
            purchase_request = Period.create(
                {
                    "name": "Purchase Request",
                    "report_instance_id": self.report_instance_id.id,
                    "sequence": 30,
                    "source": "actuals_alt",
                    "source_aml_model_id": model.id,
                    "mode": "fix",
                    "manual_date_from": self.bm_date_from,
                    "manual_date_to": self.bm_date_to,
                }
            )
            periods.update({purchase_request: "-"})
        return periods

    def _budget_info_query(self):
        query = super()._budget_info_query()
        query["info_cols"]["amount_purchase_request"] = ("2_pr_commit", True)
        return query

    def _compute_budget_info(self, **kwargs):
        """ Add more data info budget_info, based on installed modules """
        super()._compute_budget_info(**kwargs)
        self._set_budget_info_amount(
            "amount_purchase_request",
            [
                (
                    "source_aml_model_id.model",
                    "=",
                    "purchase.request.budget.move",
                )
            ],
            kwargs,
            is_commit=True,
        )
