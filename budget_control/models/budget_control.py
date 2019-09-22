# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class BudgetControl(models.Model):
    _name = 'budget.control'
    _description = 'Budget Control'
    _inherit = ['mail.thread']

    name = fields.Char(
        required=True,
    )
    assignee_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned To',
        domain=lambda self: [('groups_id', 'in', [self.env.ref(
            "budget_control.group_budget_control_user").id])],
        track_visibility='onchange',
        states={'done': [('readonly', True)]},
        copy=False,
    )
    budget_id = fields.Many2one(
        comodel_name='mis.budget',
        string='MIS Budget',
        required=True,
        ondelete='restrict',
        domain=lambda self: self._get_mis_budget_domain(),
        help="List of mis.budget created by and linked to budget.management",
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
        inverse_name='budget_control_id',
        string='Budget Items',
        copy=False,
    )
    plan_date_range_type_id = fields.Many2one(
        comodel_name='date.range.type',
        string='Plan Date Range',
        required=True,
    )
    state = fields.Selection(
        [('draft', 'Draft'),
         ('done', 'Controlled'), ],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        default='draft',
        track_visibility='always',
        track_sequence=1,
    )
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Name must be unique!'),
        ('budget_control_uniq', 'UNIQUE(budget_id, analytic_account_id)',
         'Duplicated analytic account for the same budget!')
    ]

    @api.model
    def _get_mis_budget_domain(self):
        all_budget_mgnts = self.env['budget.management'].search([])
        return [('id', 'in', all_budget_mgnts.mapped('mis_budget_id').ids)]

    @api.model
    def create(self, vals):
        plan = super().create(vals)
        plan.prepare_budget_control_matrix()
        return plan

    @api.multi
    def write(self, vals):
        # if any field in header changes, reset the plan matrix
        res = super().write(vals)
        fixed_fields = ['budget_id',
                        'plan_date_range_type_id',
                        'analytic_account_id']
        change_fields = list(vals.keys())
        if list(set(fixed_fields) & set(change_fields)):
            self.prepare_budget_control_matrix()
        return res

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def prepare_budget_control_matrix(self):
        KpiExpression = self.env['mis.report.kpi.expression']
        DateRange = self.env['date.range']
        for plan in self:
            plan.item_ids.unlink()
            if not plan.plan_date_range_type_id:
                raise UserError(_('Please select range'))
            date_ranges = DateRange.search([
                ('type_id', '=', plan.plan_date_range_type_id.id),
                ('date_start', '>=', plan.date_from),
                ('date_end', '<=', plan.date_to)])
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

    @api.multi
    def _report_instance(self):
        self.ensure_one()
        budget_mgnt = self.env['budget.management'].search([
            ('mis_budget_id', '=', self.budget_id.id)])
        ctx = {'mis_report_filters': {}}
        if self.analytic_account_id:
            ctx['mis_report_filters']['analytic_account_id'] = {
                'value': self.analytic_account_id.id,
            }
        return budget_mgnt.report_instance_id.with_context(ctx)

    @api.multi
    def preview(self):
        return self._report_instance().preview()

    @api.multi
    def print_pdf(self):
        return self._report_instance().print_pdf()

    @api.multi
    def export_xls(self):
        return self._report_instance().export_xls()
