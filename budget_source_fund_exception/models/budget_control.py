# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class BudgetControl(models.Model):
    _inherit = "budget.control"

    def _get_amount_plan(self):
        amount_plan = sum(self.item_ids.mapped("amount"))
        return amount_plan

    def _get_amount_fund(self):
        amount_fund = sum(self.fund_line_ids.mapped("amount"))
        return amount_fund
