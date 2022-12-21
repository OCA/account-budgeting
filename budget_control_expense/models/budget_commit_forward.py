# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetCommitForward(models.Model):
    _inherit = "budget.commit.forward"

    expense = fields.Boolean(
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
            return f"{doc.sheet_id._name},{doc.sheet_id.id}"
        return super()._get_document_number(doc)

    def _get_commit_docline(self, res_model):
        if res_model == "hr.expense":
            domain = self._get_base_domain()
            domain.extend(
                [
                    ("analytic_account_id", "!=", False),
                    ("state", "!=", "cancel"),
                ]
            )
            return self.env[res_model].search(domain)
        return super()._get_commit_docline(res_model)


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
    document_number = fields.Reference(
        selection_add=[("hr.expense.sheet", "Expense Sheet")],
        ondelete={"hr.expense.sheet": "cascade"},
    )
