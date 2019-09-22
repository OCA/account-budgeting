# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BudgetControl(models.Model):
    _name = 'budget.control'
    _inherit = ['budget.control', 'tier.validation']
    _state_from = ['draft']
    _state_to = ['done']
