# Copyright 2020 Ecosoft - (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class BudgetInfo(models.TransientModel):
    _name = "analytic.budget.info"
    _description = "Show budget overview of selected analytic"

    budget_period_ids = fields.Many2many(
        comodel_name="budget.period",
    )
    budget_control_ids = fields.Many2many(
        comodel_name="budget.control",
        readonly=True,
    )
    filtered_control_ids = fields.Many2many(
        comodel_name="budget.control",
        compute="_compute_filtered_control_ids",
    )

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        analytic_ids = self.env.context.get("active_ids")
        analytics = self.env["account.analytic.account"].browse(analytic_ids)
        budget_controls = analytics.mapped("budget_control_ids")
        res["budget_control_ids"] = [(6, 0, budget_controls.ids)]
        return res

    @api.depends("budget_period_ids")
    def _compute_filtered_control_ids(self):
        self.ensure_one()
        if self.budget_period_ids:
            self.filtered_control_ids = self.budget_control_ids.filtered_domain(
                [("budget_period_id", "in", self.budget_period_ids.ids)]
            )
        else:
            self.filtered_control_ids = self.budget_control_ids
