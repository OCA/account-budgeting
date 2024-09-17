#  Copyright 2022 Simone Rubino - TAKOBI
#  License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields
from odoo.models import TransientModel


class ReportBudgetLinesHeader (TransientModel):
    _name = 'account_budget_oca.budget_lines_report.header'
    _description = "Budget Report Header"

    date = fields.Date()
    line_ids = fields.One2many(
        comodel_name='account_budget_oca.budget_lines_report',
        inverse_name='report_header_id',
    )

    def _prepare_report_lines(self):
        self.ensure_one()
        budget_lines = self.env['crossovered.budget.lines'].search([])
        budget_lines_values = budget_lines \
            .with_context(
                budget_date=self.date,
            ) \
            .read(
                fields=[
                    'id',
                    'crossovered_budget_id',
                    'analytic_account_id',
                    'general_budget_id',
                    'date_from',
                    'date_to',
                    'planned_amount',
                    'practical_amount',
                    'theoretical_amount',
                    'percentage',
                    'practical_on_planned_percentage',
                    'company_id',
                ],
                load=None,
            )
        report_id = self.id
        for budget_line_values in budget_lines_values:
            line_id = budget_line_values.pop('id')
            budget_line_values.update({
                'crossovered_budget_line_id': line_id,
                'report_header_id': report_id
            })
        return budget_lines_values

    def compute_report_data(self):
        self.ensure_one()
        report_lines_values = self._prepare_report_lines()
        report_lines = self.env['account_budget_oca.budget_lines_report'] \
            .create(report_lines_values)
        return report_lines

    def show_result(self):
        lines = self.mapped('line_ids')
        lines_action = self.env['ir.actions.act_window'] \
            .for_xml_id('account_budget_oca', 'budget_lines_report_action')
        lines_action['domain'] = [
            ('id', 'in', lines.ids),
        ]
        return lines_action


class ReportBudgetLines (TransientModel):
    _name = 'account_budget_oca.budget_lines_report'
    _description = "Budget Report Lines"

    report_header_id = fields.Many2one(
        comodel_name='account_budget_oca.budget_lines_report.header',
        string="Report Header",
        readonly=True,
    )
    crossovered_budget_line_id = fields.Many2one(
        comodel_name='crossovered.budget.lines',
        string="Budget Line",
        readonly=True,
    )
    crossovered_budget_id = fields.Many2one(
        comodel_name='crossovered.budget',
        string="Budget",
        readonly=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        readonly=True,
    )
    general_budget_id = fields.Many2one(
        comodel_name='account.budget.post',
        string='Budgetary Position',
        readonly=True,
    )
    date_from = fields.Date(
        string='Start Date',
        readonly=True,
    )
    date_to = fields.Date(
        string='End Date',
        readonly=True,
    )
    planned_amount = fields.Float(
        readonly=True,
    )
    practical_amount = fields.Float(
        readonly=True,
    )
    theoretical_amount = fields.Float(
        readonly=True,
    )
    percentage = fields.Float(
        string='Achievement',
        readonly=True,
    )
    practical_on_planned_percentage = fields.Float(
        string='Practical/Planned',
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        readonly=True,
    )
