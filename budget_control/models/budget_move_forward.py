# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class BudgetMoveForward(models.Model):
    _name = 'budget.move.forward'
    _description = 'Budget Move Forward'
    _inherit = ['mail.thread']

    name = fields.Char(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    assignee_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned To',
        domain=lambda self: [('groups_id', 'in', [self.env.ref(
            "budget_control.group_budget_control_user").id])],
        track_visibility='onchange',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )
    to_budget_id = fields.Many2one(
        comodel_name='mis.budget',
        string='To Budget Period',
        required=True,
        ondelete='restrict',
        readonly=True,
        states={'draft': [('readonly', False)]},
        # TODO: add domain, and default
    )
    date_budget_move = fields.Date(
        related='to_budget_id.date_from',
        string='Move to date',
    )
    state = fields.Selection(
        [('draft', 'Draft'),
         ('done', 'Done'), ],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        default='draft',
        track_visibility='always',
        track_sequence=1,
    )
    forward_line_ids = fields.One2many(
        comodel_name='budget.move.forward.line',
        inverse_name='forward_id',
        string='Forward Lines',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Name must be unique!'),
    ]

    @api.multi
    def get_budget_move_forward(self):
        """Get budget move forward for each new commit document type."""
        Line = self.env['budget.move.forward.line']
        specific_model = self._context.get('res_model', False)
        for rec in self:
            models = Line._fields['res_model'].selection
            for model in list(dict(models).keys()):
                if specific_model and specific_model != model:
                    continue
                Line.search([('forward_id', '=', rec.id),
                             ('res_model', '=', model)]).unlink()
                docs = self.env[model].search([('amount_commit', '>', 0.0)])
                Line.create([{'forward_id': rec.id,
                              'res_model': model,
                              'res_id': doc.id,
                              'document_id': '%s,%s' % (model, doc.id),
                              'amount_commit': doc.amount_commit,
                              'date_commit': doc.date_commit,
                              } for doc in docs])

    @api.multi
    def action_budget_carry_forward(self):
        Line = self.env['budget.move.forward.line']
        for rec in self:
            models = Line._fields['res_model'].selection
            for model in list(dict(models).keys()):
                doclines = Line.search(
                    [('forward_id', '=', rec.id),
                     ('res_model', '=', model)]).mapped('document_id')
                if not doclines:
                    continue
                budget_moves = doclines.mapped('budget_move_ids')
                budget_moves.write({'date': rec.date_budget_move})
        self.write({'state': 'done'})


class BudgetMoveForwardLine(models.Model):
    _name = 'budget.move.forward.line'
    _description = 'Budget Move Forward Line'

    forward_id = fields.Many2one(
        comodel_name='budget.move.forward',
        index=True,
        readonly=True,
        required=True,
    )
    res_model = fields.Selection(
        selection=[],
        string='Res Model',
        required=True,
    )
    res_id = fields.Integer(
        string='Res ID',
        required=True,
    )
    document_id = fields.Reference(
        selection=[],
        string='Document',
        required=True,
    )
    date_commit = fields.Date(
        string='Date',
        required=True,
    )
    amount_commit = fields.Float(
        string='Commitment',
        required=True,
    )


class BudgetDoclineMixin(models.AbstractModel):
    _name = 'budget.docline.mixin'
    _description = 'Mixin used in each document line model that commit budget'

    amount_commit = fields.Float(
        compute='_compute_commit',
        store=True,
    )
    date_commit = fields.Date(
        compute='_compute_commit',
        store=True,
    )

    @api.depends('budget_move_ids', 'budget_move_ids.date')
    def _compute_commit(self):
        for rec in self:
            if not rec.budget_move_ids:
                continue
            debit = sum(rec.budget_move_ids.mapped('debit'))
            credit = sum(rec.budget_move_ids.mapped('credit'))
            rec.amount_commit = debit - credit
            rec.date_commit = min(rec.budget_move_ids.mapped('date'))
