# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    not_affect_budget = fields.Boolean(
        help="If check, lines does not affect the budget"
    )

    def _move_type_budget(self):
        """For hooks, default check budget following
        - Vedor Bills
        - Customer Refund
        - Journal Entries
        """
        self.ensure_one()
        return ("in_invoice", "out_refund", "entry")

    def action_post(self):
        res = super().action_post()
        BudgetPeriod = self.env["budget.period"]
        move_check_budget = self.filtered(
            lambda l: not l.not_affect_budget
            and l.move_type in self._move_type_budget()
        )
        for doc in move_check_budget:
            BudgetPeriod.check_budget(doc.line_ids)
        return res
