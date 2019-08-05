# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _


class BudgetManagement(models.Model):
    _name = 'budget.management'
    _inherits = {'mis.report.instance': 'report_instance_id'}
    _description = 'For each fiscal year, manage how budget is controlled'

    report_instance_id = fields.Many2one(
        comodel_name='mis.report.instance',
        readonly=False,
        ondelete='restrict',
        help="Automatically created report instance for this budget mgnt",
    )
    source_mis_budget_id = fields.Many2one(
        comodel_name='mis.budget',
        string='MIS Budget',
        readonly=True,
        ondelete='restrict',
        help="Automatically created mis budget",
    )
    bm_date_from = fields.Date(
        string='From',
        required=True,
    )
    bm_date_to = fields.Date(
        string='To',
        required=True,
    )
    control_budget = fields.Boolean(
        default=False,
        help="Block user from confirming document, if budget become negative",
    )
    account_control = fields.Boolean(
        string='Control on Account Documents',
        default=False,
        help="Control budget on journal document(s), i.e., vendor bill",
    )
    purchase_control = fields.Boolean(
        string='Control on Purchase Order',
        default=False,
        help="Control budget on purchase order confirmation",
    )
    purchase_request_control = fields.Boolean(
        string='Control on Purchase Request',
        default=False,
        help="Control budget on purchase request confirmation",
    )
    expense_control = fields.Boolean(
        string='Control on Expense',
        default=False,
        help="Control budget on expense confirmation",
    )

    @api.model
    def create(self, vals):
        # Auto create mis.budget, and link it to same kpi and date range
        mis_budget = self.env['mis.budget'].create({
            'name': _('%s - Budget Plan') % vals['name'],
            'report_id': vals['report_id'],
            'date_from': vals['bm_date_from'],
            'date_to': vals['bm_date_to'],
        })
        vals.update({'comparison_mode': True,
                     'target_move': 'posted',
                     'source_mis_budget_id': mis_budget.id})
        budget_mgnt = super().create(vals)
        budget_mgnt._recompute_report_instance_periods()
        return budget_mgnt

    @api.multi
    def write(self, vals):
        vals.update({'comparison_mode': True, 'target_move': 'posted'})
        res = super().write(vals)
        self._recompute_report_instance_periods()
        return res

    @api.multi
    def unlink(self):
        report_instances = self.mapped('report_instance_id')
        mis_budgets = self.mapped('source_mis_budget_id')
        res = super().unlink()
        report_instances.mapped('period_ids.source_sumcol_ids').unlink()
        report_instances.mapped('period_ids').unlink()
        report_instances.unlink()
        mis_budgets.unlink()
        return res

    @api.multi
    def _recompute_report_instance_periods(self):
        for budget_mgnt in self:
            budget_mgnt.report_instance_id.period_ids.\
                mapped('source_sumcol_ids').unlink()
            budget_mgnt.report_instance_id.period_ids.unlink()
            budget_mgnt._create_report_instance_period()

    @api.multi
    def _create_report_instance_period(self):
        self.ensure_one()
        Period = self.env['mis.report.instance.period']
        report_instance_id = self.report_instance_id.id
        budget = Period.create({
            'name': 'Budgeted',
            'report_instance_id': report_instance_id,
            'sequence': 10,
            'source': 'mis_budget',
            'source_mis_budget_id': self.source_mis_budget_id.id,
            'mode': 'fix',
            'manual_date_from': self.bm_date_from,
            'manual_date_to': self.bm_date_to,
        })
        actual = Period.create({
            'name': 'Actuals',
            'report_instance_id': report_instance_id,
            'sequence': 20,
            'source': 'actuals',
            'mode': 'fix',
            'manual_date_from': self.bm_date_from,
            'manual_date_to': self.bm_date_to,
        })
        Period.create({
            'name': 'Available',
            'report_instance_id': report_instance_id,
            'sequence': 30,
            'source': 'sumcol',
            'source_sumcol_ids': [
                (0, 0, {'sign': '+', 'period_to_sum_id': budget.id}),
                (0, 0, {'sign': '-', 'period_to_sum_id': actual.id}),
            ],
            'mode': 'none',
        })
