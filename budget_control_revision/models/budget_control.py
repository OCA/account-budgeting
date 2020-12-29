# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetControl(models.Model):
    _name = "budget.control"
    _inherit = ["budget.control", "base.revision"]

    current_revision_id = fields.Many2one(
        comodel_name="budget.control",
    )
    old_revision_ids = fields.One2many(
        comodel_name="budget.control",
    )
    revision_number = fields.Integer(readonly=True)

    _sql_constraints = [
        (
            "budget_control_uniq",
            "UNIQUE(budget_id, analytic_account_id, name)",
            "Duplicated analytic account for the same budget!",
        ),
    ]
