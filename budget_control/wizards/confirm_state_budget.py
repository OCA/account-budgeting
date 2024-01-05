# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BudgetControlStateConfirmation(models.TransientModel):
    _name = "budget.state.confirmation"
    _description = "Confirmation State"

    def confirm(self):
        active_ids = self._context.get("active_ids")
        state = self._context.get("state")
        budget_control = self.env["budget.control"].browse(active_ids)
        if state == "done":
            return budget_control.action_done()
        elif state == "submit":
            return budget_control.action_submit()
        elif state == "cancel":
            return budget_control.action_cancel()
