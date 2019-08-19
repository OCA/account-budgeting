# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class BudgetManagement(models.Model):
    _inherit = 'budget.management'

    sale = fields.Boolean(
        string='On Sales',
        default=False,
        help="Control budget on sales order confirmation",
    )

    @api.multi
    def _create_budget_move_periods(self):
        periods = super()._create_budget_move_periods()
        if self.sale:
            Period = self.env['mis.report.instance.period']
            model = self.env.ref('budget_management_sale.'
                                 'model_sale_budget_move')
            sale = Period.create({
                'name': 'Sales Committed',
                'report_instance_id': self.report_instance_id.id,
                'sequence': 11,
                'source': 'actuals_alt',
                'source_aml_model_id': model.id,
                'mode': 'fix',
                'manual_date_from': self.bm_date_from,
                'manual_date_to': self.bm_date_to,
            })
            periods.update({sale: '-'})
        return periods
