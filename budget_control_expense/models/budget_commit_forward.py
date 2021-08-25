# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetCommitForward(models.Model):
    _inherit = "budget.commit.forward"

    expense = fields.Boolean(
        string="Expense",
        default=True,
        help="If checked, click review budget commitment will pull expense commitment",
    )
    forward_expense_ids = fields.One2many(
        comodel_name="budget.commit.forward.line",
        inverse_name="forward_id",
        string="Expenses",
        domain=[("res_model", "=", "hr.expense")],
    )

    def _get_budget_docline_model(self):
        res = super()._get_budget_docline_model()
        if self.expense:
            res.append("hr.expense")
        return res

    def _get_document_number(self, doc):
        if doc._name == "hr.expense":
            return ("{},{}".format(doc.sheet_id._name, doc.sheet_id.id),)
        return super()._get_document_number(doc)

    def _get_domain_search(self, model):
        domain_search = super()._get_domain_search(model)
        if model == "hr.expense":
            domain_search.extend(
                [
                    ("analytic_account_id", "!=", False),
                    ("state", "!=", "cancel"),
                ]
            )
        return domain_search


class BudgetCommitForwardLine(models.Model):
    _inherit = "budget.commit.forward.line"

    res_model = fields.Selection(
        selection_add=[("hr.expense", "Expense")],
        ondelete={"hr.expense": "cascade"},
    )
    document_id = fields.Reference(
        selection_add=[("hr.expense", "Expense")],
        ondelete={"hr.expense": "cascade"},
    )
