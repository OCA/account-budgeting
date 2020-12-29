# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class BudgetControlExceptionConfirm(models.TransientModel):
    _name = "budget.control.exception.confirm"
    _inherit = ["exception.rule.confirm"]
    _description = "Budget Control exception wizard"

    related_model_id = fields.Many2one("budget.control", "Budget Control")

    def action_confirm(self):
        self.ensure_one()
        if self.ignore:
            self.related_model_id.ignore_exception = True
        return super().action_confirm()
