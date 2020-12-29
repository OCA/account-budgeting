# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetMonitorReport(models.Model):
    _inherit = "budget.monitor.report"

    operating_unit_id = fields.Many2one(comodel_name="operating.unit")

    # Budget
    def _select_budget(self):
        select_budget_query = super()._select_budget()
        select_budget_query = ",".join([select_budget_query, "bc.operating_unit_id"])
        return select_budget_query

    # Actual
    def _select_actual(self):
        select_actual_query = super()._select_actual()
        select_actual_query = ",".join([select_actual_query, "aml.operating_unit_id"])
        return select_actual_query
