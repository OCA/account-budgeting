# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


class SaleBudgetMove(models.Model):
    _inherit = 'sale.budget.move'
