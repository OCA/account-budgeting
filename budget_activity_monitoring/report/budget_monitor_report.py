# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetMonitorReport(models.Model):
    _inherit = "budget.monitor.report"

    activity_name = fields.Char(string="Activity Name")

    # Budget
    def _select_budget(self):
        select_budget_query = super()._select_budget()
        select_budget_query = ",".join(
            [select_budget_query, "null::char as activity_name"]
        )
        return select_budget_query

    # Actual
    def _select_actual(self):
        select_actual_query = super()._select_actual()
        select_actual_query = ",".join(
            [select_actual_query, "ba.name as activity_name"]
        )
        return select_actual_query

    def _from_actual(self):
        from_actual_query = super()._from_actual()
        from_actual_query = "\n".join(
            [
                from_actual_query,
                "left outer join budget_activity ba on aml.activity_id = ba.id",
            ]
        )
        return from_actual_query
