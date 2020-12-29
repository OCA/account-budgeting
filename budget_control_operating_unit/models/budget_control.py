# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models


class BudgetControl(models.Model):
    _inherit = "budget.control"

    operating_unit_id = fields.Many2one(
        comodel_name="operating.unit",
        compute="_compute_budget_operating_unit",
        store=True,
    )

    @api.depends("analytic_account_id")
    def _compute_budget_operating_unit(self):
        for rec in self:
            if len(rec.analytic_account_id.operating_unit_ids) == 1:
                rec.operating_unit_id = rec.analytic_account_id.operating_unit_ids.id
