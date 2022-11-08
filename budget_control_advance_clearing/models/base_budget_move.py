# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BudgetDoclineMixin(models.AbstractModel):
    _inherit = "budget.docline.mixin"

    def _update_budget_commitment(self, budget_vals, reverse=False):
        self.ensure_one()
        budget_vals = super()._update_budget_commitment(budget_vals, reverse)
        # change analytic account when carry forward (clearing and return)
        if (
            self[self._budget_analytic_field]
            and self._budget_model() == "advance.budget.move"
            and self.fwd_analytic_account_id
            and (budget_vals.get("clearing_id") or budget_vals.get("move_line_id"))
        ):
            budget_vals["analytic_account_id"] = self.fwd_analytic_account_id.id
        return budget_vals

    def _get_domain_fwd_line(self, docline):
        """Change res_model in forward advance to hr.expense.advance"""
        if self._budget_model() == "advance.budget.move":
            return [
                ("res_model", "=", "hr.expense.advance"),
                ("res_id", "=", docline.id),
                ("forward_id.state", "in", ["review", "done"]),
            ]
        return super()._get_domain_fwd_line(docline)
