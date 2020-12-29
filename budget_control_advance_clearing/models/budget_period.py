# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetPeriod(models.Model):
    _inherit = "budget.period"

    advance = fields.Boolean(
        string="On Advance",
        default=False,
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
