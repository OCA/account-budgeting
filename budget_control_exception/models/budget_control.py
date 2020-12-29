# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class BudgetControl(models.Model):
    _name = "budget.control"
    _inherit = ["budget.control", "base.exception"]

    @api.model
    def test_all_draft_orders(self):
        order_set = self.search([("state", "=", "draft")])
        order_set.detect_exceptions()
        return True

    @api.model
    def _reverse_field(self):
        return "budget_control_ids"

    def detect_exceptions(self):
        all_exceptions = super().detect_exceptions()
        lines = self.mapped("item_ids")
        all_exceptions += lines.detect_exceptions()
        return all_exceptions

    @api.constrains("ignore_exception", "item_ids", "state")
    def budget_control_check_exception(self):
        budgets = self.filtered(lambda s: s.state == "done")
        if budgets:
            budgets._check_exception()

    @api.onchange("item_ids")
    def onchange_ignore_exception(self):
        if self.state == "done":
            self.ignore_exception = False

    def action_done(self):
        if self.detect_exceptions() and not self.ignore_exception:
            return self._popup_exceptions()
        return super().action_done()

    def action_draft(self):
        res = super().action_draft()
        for order in self:
            order.exception_ids = False
            order.main_exception_id = False
            order.ignore_exception = False
        return res

    @api.model
    def _get_popup_action(self):
        action = self.env.ref(
            "budget_control_exception.action_budget_control_exception_confirm"
        )
        return action
