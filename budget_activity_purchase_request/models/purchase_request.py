# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'


class PurchaseRequestBudgetMove(models.Model):
    _inherit = 'purchase.request.budget.move'
