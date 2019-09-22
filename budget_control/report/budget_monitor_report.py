# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import tools
from odoo import models, fields, api


class BudgetMonitorReport(models.Model):
    _name = 'budget.monitor.report'
    _description = 'Budget Monitoring Report'
    _auto = False
    _order = 'date desc'
    _rec_name = 'res_id'

    res_id = fields.Reference(
        selection=[('mis.budget.item', 'Budget Item'),
                   ('account.move.line', 'Account Move Line')],
        string='Resource ID',
    )
    reference = fields.Char()
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
    )
    date = fields.Date()
    amount = fields.Float()
    amount_type = fields.Selection(
        selection=[('1_budget', 'Budget'),
                   ('8_actual', 'Actual')],
        string='Type',
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
    )

    def _select_budget(self):
        return """
            select 1000000000 + a.id as id,
                'mis.budget.item,' || a.id as res_id,
                a.analytic_account_id,
                a.date_from as date,  -- approx date
                '1_budget' as amount_type,
                a.amount as amount,
                null::integer as account_id,
                b.name as reference
        """

    def _from_budget(self):
        return """
            from mis_budget_item a
            left outer join budget_control b on a.budget_control_id = b.id
            where a.active = true and a.state = 'done'
        """

    def _select_actual(self):
        return """
            select 8000000000 + a.id as id,
            'account.move.line,' || a.id as res_id,
            a.analytic_account_id,
            a.date as date,
            '8_actual' as amount_type,
            a.credit-a.debit as amount,
            a.account_id,
            b.name as reference
       """

    def _from_actual(self):
        return """
            from account_move_line a
            left outer join account_move b on a.move_id = b.id
        """

    def _get_sql(self):
        return ("(%s %s) union (%s %s)" % (self._select_budget(),
                                           self._from_budget(),
                                           self._select_actual(),
                                           self._from_actual()))

    @api.model_cr
    def init(self):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s as (%s)
        """ % (self._table, self._get_sql()))
