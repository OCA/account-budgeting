# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetCommitForward(models.Model):
    _inherit = "budget.commit.forward"

    advance = fields.Boolean(
        string="Advance",
        default=True,
        help="If checked, click review budget commitment will pull advance commitment",
    )
    forward_advance_ids = fields.One2many(
        comodel_name="budget.commit.forward.line",
        inverse_name="forward_id",
        string="Advance",
        domain=[("res_model", "=", "hr.expense.advance")],
    )

    def _get_budget_docline_model(self):
        res = super()._get_budget_docline_model()
        if self.advance:
            res.append("hr.expense.advance")
        return res

    def _get_document_number(self, doc):
        if doc._name == "hr.expense.advance":
            return "{},{}".format(doc.sheet_id._name, doc.sheet_id.id)
        return super()._get_document_number(doc)

    def _get_commit_docline(self, res_model):
        # Special case, model = hr.expense with advance
        if res_model == "hr.expense.advance":
            model = "hr.expense"
            domain = self._get_base_domain()
            domain.extend(
                [
                    ("advance", "=", True),
                    ("analytic_account_id", "!=", False),
                    ("state", "!=", "cancel"),
                ]
            )
            return self.env[model].search(domain)
        if res_model == "hr.expense":
            domain = self._get_base_domain()
            domain.extend(
                [
                    ("advance", "=", False),  # Additional criteria
                    ("analytic_account_id", "!=", False),
                    ("state", "!=", "cancel"),
                ]
            )
            return self.env[res_model].search(domain)
        return super()._get_commit_docline(res_model)


class BudgetCommitForwardLine(models.Model):
    _inherit = "budget.commit.forward.line"

    res_model = fields.Selection(
        selection_add=[("hr.expense.advance", "Advance")],
        ondelete={"hr.expense.advance": "cascade"},
    )
