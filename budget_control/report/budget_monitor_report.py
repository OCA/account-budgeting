# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetMonitorReport(models.Model):
    _name = "budget.monitor.report"
    _description = "Budget Monitoring Report"
    _auto = False
    _order = "date desc"
    _rec_name = "reference"

    res_id = fields.Reference(
        selection=[
            ("mis.budget.item", "Budget Item"),
            ("account.move.line", "Account Move Line"),
        ],
        string="Resource ID",
    )
    reference = fields.Char()
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
    )
    date = fields.Date()
    amount = fields.Float()
    amount_type = fields.Selection(
        selection=[("1_budget", "Budget"), ("8_actual", "Actual")],
        string="Type",
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
    )
    kpi_name = fields.Char()

    @property
    def _table_query(self):
        return "%s" % (self._get_sql())

    def _select_budget(self):
        return """
            select 1000000000 + mbi.id as id,
            'mis.budget.item,' || mbi.id as res_id,
            mrk.description as kpi_name,
            mbi.analytic_account_id,
            mbi.date_from as date,  -- approx date
            '1_budget' as amount_type,
            mbi.amount as amount,
            null::integer as account_id,
            bc.name as reference
        """

    def _from_budget(self):
        return """
            from mis_budget_item mbi
            left outer join budget_control bc on mbi.budget_control_id = bc.id
            join mis_report_kpi_expression mrke on mbi.kpi_expression_id = mrke.id
            join mis_report_kpi mrk on mrke.kpi_id = mrk.id
        """

    def _where_budget(self):
        return """
            where mbi.active = true and mbi.state = 'done'
        """

    def _select_actual(self):
        return """
            select 8000000000 + aml.id as id,
            'account.move.line,' || aml.id as res_id,
            null::char as kpi_name,
            aml.analytic_account_id,
            aml.date as date,
            '8_actual' as amount_type,
            aml.credit-aml.debit as amount,
            aml.account_id,
            am.name as reference
       """

    def _from_actual(self):
        return """
            from account_move_line aml
            left outer join account_move am on aml.move_id = am.id
        """

    def _where_actual(self):
        return """
            where am.state = 'posted'
        """

    def _get_sql(self):
        return "({} {} {}) union ({} {} {})".format(
            self._select_budget(),
            self._from_budget(),
            self._where_budget(),
            self._select_actual(),
            self._from_actual(),
            self._where_actual(),
        )
