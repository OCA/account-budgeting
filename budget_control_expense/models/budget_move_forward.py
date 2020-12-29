# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetMoveForward(models.Model):
    _inherit = "budget.move.forward"

    forward_expense_ids = fields.One2many(
        comodel_name="budget.move.forward.line",
        inverse_name="forward_id",
        string="Expenses",
        domain=[("res_model", "=", "hr.expense")],
    )

    def _get_domain_search(self, model):
        """ Filter Purchase used analytic account"""
        domain_search = super()._get_domain_search(model)
        if model == "hr.expense":
            domain_search.extend(
                [("analytic_account_id", "!=", False), ("state", "!=", "cancel")]
            )
        return domain_search


class BudgetMoveForwardLine(models.Model):
    _inherit = "budget.move.forward.line"

    res_model = fields.Selection(
        selection_add=[("hr.expense", "Expense")],
        ondelete={"hr.expense": "cascade"},
    )
    document_id = fields.Reference(
        selection_add=[("hr.expense", "Expense")],
        ondelete={"hr.expense": "cascade"},
    )
