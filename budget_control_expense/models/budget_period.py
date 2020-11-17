# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetPeriod(models.Model):
    _inherit = "budget.period"

    expense = fields.Boolean(
        string="On Expense",
        default=False,
        help="Control budget on expense approved",
    )

    def _create_budget_move_periods(self):
        periods = super()._create_budget_move_periods()
        if self.expense:
            Period = self.env["mis.report.instance.period"]
            model = self.env.ref("budget_control_expense." "model_expense_budget_move")
            expense = Period.create(
                {
                    "name": "Expense",
                    "report_instance_id": self.report_instance_id.id,
                    "sequence": 50,
                    "source": "actuals_alt",
                    "source_aml_model_id": model.id,
                    "mode": "fix",
                    "manual_date_from": self.bm_date_from,
                    "manual_date_to": self.bm_date_to,
                }
            )
            periods.update({expense: "-"})
        return periods
