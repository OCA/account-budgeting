# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetControlStateConfirmation(models.TransientModel):
    _name = "budget.state.confirmation"
    _description = "Confirmation State"

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submit", "Submitted"),
            ("done", "Controlled"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        required=True,
    )

    def confirm(self):
        self.ensure_one()
        active_ids = self._context.get("active_ids")
        budget_control = self.env["budget.control"].browse(active_ids)
        if self.state == "draft":
            return budget_control.action_draft()
        elif self.state == "done":
            return budget_control.action_done()
        elif self.state == "submit":
            return budget_control.action_submit()
        elif self.state == "cancel":
            return budget_control.action_cancel()
