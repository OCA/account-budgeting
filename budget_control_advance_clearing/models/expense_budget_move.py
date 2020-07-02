# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ExpenseBudgetMove(models.Model):
    _inherit = 'expense.budget.move'

    clear_advance = fields.Float(
        readonly=True,
        help="No further budget commitment as it is clearing from advance",
    )
