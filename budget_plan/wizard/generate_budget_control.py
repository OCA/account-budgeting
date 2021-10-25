# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class GenerateBudgetControl(models.TransientModel):
    _inherit = "generate.budget.control"

    budget_plan_id = fields.Many2one(
        comodel_name="budget.plan",
    )

    def _get_existing_budget(self):
        """ Update allocated amount from budget plan """
        if self.budget_plan_id:  # create from budget plan
            return self.budget_plan_id.budget_control_ids
        else:  # create from budget period
            return super()._get_existing_budget()
