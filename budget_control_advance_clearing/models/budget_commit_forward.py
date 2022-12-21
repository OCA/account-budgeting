# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetCommitForward(models.Model):
    _inherit = "budget.commit.forward"

    advance = fields.Boolean(
        default=True,
        help="If checked, click review budget commitment will pull advance commitment",
    )
    forward_advance_ids = fields.One2many(
        comodel_name="budget.commit.forward.line",
        inverse_name="forward_id",
        string="Fwd Advances",
        domain=[("res_model", "=", "hr.expense.advance")],
    )

    def _get_budget_docline_model(self):
        res = super()._get_budget_docline_model()
        if self.advance:
            res.append("hr.expense.advance")
        return res

    def _get_document_number(self, doc):
        if doc._name == "hr.expense.advance":
            return f"{doc.sheet_id._name},{doc.sheet_id.id}"
        return super()._get_document_number(doc)

    def _get_commit_docline(self, res_model):
        if res_model not in ["hr.expense.advance", "hr.expense"]:
            return super()._get_commit_docline(res_model)
        domain = self._get_base_domain()
        domain.extend(
            [
                ("analytic_account_id", "!=", False),
                ("state", "!=", "cancel"),
            ]
        )
        # Special case, model = hr.expense with advance
        if res_model == "hr.expense.advance":
            domain.extend(
                [
                    ("advance", "=", True),
                    ("sheet_id.clearing_residual", ">", 0.0),
                ]
            )
        else:
            domain.extend(
                [
                    ("advance", "=", False),  # Additional criteria
                ]
            )
        return self.env["hr.expense"].search(domain)


class BudgetCommitForwardLine(models.Model):
    _inherit = "budget.commit.forward.line"

    res_model = fields.Selection(
        selection_add=[("hr.expense.advance", "Advance")],
        ondelete={"hr.expense.advance": "cascade"},
    )
