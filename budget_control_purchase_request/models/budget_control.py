# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetControl(models.Model):
    _inherit = "budget.control"

    amount_purchase_request = fields.Monetary(
        string="Purchase Request",
        compute="_compute_budget_info",
        help="Sum of purchase amount",
    )
