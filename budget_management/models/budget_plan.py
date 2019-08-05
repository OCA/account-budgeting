# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class BudgetPlan(models.Model):
    _name = 'budget.plan'
    _description = 'Budget plan ease filling the MIS Budget form'

    name = fields.Char(
        required=True,
    )
    budget_id = fields.Many2one(
        comodel_name='mis.budget',
        string='MIS Budget',
        required=True,
        ondelete='restrict',
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        related='budget_id.date_range_id',
    )
    date_from = fields.Date(
        related='budget_id.date_from',
    )
    date_to = fields.Date(
        related='budget_id.date_to',
    )
    active = fields.Boolean(
        default=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        required=True,
        ondelete='restrict',
    )
    item_ids = fields.One2many(
        comodel_name='mis.budget.item',
        inverse_name='budget_plan_id',
        string='Budget Items',
    )
    plan_date_range_type_id = fields.Many2one(
        comodel_name='date.range.type',
        string='Plan Date Range',
        required=True,
    )

    @api.model
    def create(self, vals):
        plan = super().create(vals)
        plan.prepare_budget_plan_matrix()
        return plan

    @api.multi
    def prepare_budget_plan_matrix(self):
        KpiExpression = self.env['mis.report.kpi.expression']
        for plan in self:
            plan.item_ids.unlink()
            if not plan.plan_date_range_type_id:
                raise UserError(_('Please select range'))
            date_ranges = plan.plan_date_range_type_id.date_range_ids
            # TODO: date ranges only within budget date range
            kpi_expressions = KpiExpression.search([
                ('kpi_id.report_id', '=', plan.budget_id.report_id.id),
                ('kpi_id.budgetable', '=', True)])
            items = []
            for date_range in date_ranges:
                for kpi_expression in kpi_expressions:
                    vals = {'budget_id': plan.budget_id.id,
                            'kpi_expression_id': kpi_expression.id,
                            'date_range_id': date_range.id,
                            'date_from': date_range.date_start,
                            'date_to': date_range.date_end,
                            'analytic_account_id': plan.analytic_account_id.id,
                            }
                    items += [(0, 0, vals)]
            plan.write({'item_ids': items})
