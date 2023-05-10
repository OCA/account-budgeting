# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BudgetDoclineMixin(models.AbstractModel):
    _inherit = "budget.docline.mixin"

    def _get_domain_fwd_line(self, docline):
        """Change res_model in forward advance to hr.expense.advance"""
        if self._budget_model() == "advance.budget.move":
            return [
                ("res_model", "=", "hr.expense.advance"),
                ("res_id", "=", docline.id),
                ("forward_id.state", "=", "done"),
            ]
        return super()._get_domain_fwd_line(docline)
