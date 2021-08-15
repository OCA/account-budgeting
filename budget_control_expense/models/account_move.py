# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        """Uncommit budget for source expense document."""
        res = super().write(vals)
        if vals.get("state") in ("draft", "posted", "cancel"):
            self.mapped("line_ids").uncommit_expense_budget()
        return res

    def _post(self, soft=True):
        """
        In odoo auto post journal, when you post journal entry from expense
        but analytic on invoice is from expense.
        this function will not auto post,
        you can change analytic and manual post.
        """
        model = self._context.get("active_model", False)
        active_ids = self._context.get("active_ids", False)
        if model == "hr.expense":
            expense_ids = self.env[model].browse(active_ids)
            for exp in expense_ids:
                if not exp.auto_post:
                    return False
        return super()._post(soft)
