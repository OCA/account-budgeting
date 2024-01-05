# Copyright 2020 Ecosoft - (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class BudgetAnalyticEdit(models.TransientModel):
    _name = "analytic.budget.edit"
    _description = "Edit Analytic Budget"

    initial_available = fields.Float(required=True)
    reason = fields.Text(required=True)

    def action_edit(self):
        active_id = self.env.context.get("active_id")
        analytic = self.env["account.analytic.account"].browse(active_id)
        if analytic.initial_available == self.initial_available:
            return
        analytic.write({"initial_available": self.initial_available})
        analytic.message_post(
            body=_("Edited initial value. Reason: {}").format(self.reason)
        )
        return
