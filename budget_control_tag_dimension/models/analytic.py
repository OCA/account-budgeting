# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class AccountAnalyticDimension(models.Model):
    _inherit = 'account.analytic.dimension'

    @api.model
    def _create_x_field(self, values, model_names):
        _models = self.env['ir.model'].search([
            ('model', '=', model_names),
        ])
        _models.write({
            'field_id': [(0, 0, {
                'name': 'x_dimension_{}'.format(values.get('code')),
                'field_description': values.get('name'),
                'ttype': 'many2one',
                'relation': 'account.analytic.tag',
            })],
        })

    @api.model
    def create(self, values):
        res = super().create(values)
        self._create_x_field(values, 'mis.budget.item')
        self._create_x_field(values, 'budget.monitor.report')
        return res


class MisBudgetItem(models.Model):
    _name = 'mis.budget.item'
    _inherit = ['analytic.dimension.line', 'mis.budget.item']
    _analytic_tag_field_name = 'analytic_tag_ids'
