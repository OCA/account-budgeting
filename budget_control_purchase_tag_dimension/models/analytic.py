# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class AccountAnalyticDimension(models.Model):
    _inherit = 'account.analytic.dimension'

    @api.model
    def create(self, values):
        self._create_x_field(values, 'purchase.budget.move')
        return super().create(values)


class PurchaseBudgetMove(models.Model):
    _name = 'purchase.budget.move'
    _inherit = ['analytic.dimension.line', 'purchase.budget.move']
    _analytic_tag_field_name = 'analytic_tag_ids'
