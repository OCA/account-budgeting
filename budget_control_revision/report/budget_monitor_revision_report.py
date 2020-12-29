# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetMonitorRevisionReport(models.Model):
    _name = "budget.monitor.revision.report"
    _description = "Budget Revision Monitoring Report"
    _auto = False
    _order = "date desc"
    _rec_name = "reference"

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
    revision_number = fields.Char()

    def _find_operating_unit(self):
        user_id = self.env["res.users"].browse(self._uid)
        if user_id.operating_unit_ids:
            ou = "in {}".format(tuple(user_id.operating_unit_ids.ids))
        else:
            ou = "= {}".format(user_id.default_operating_unit_id.id)
        return ou

    @property
    def _table_query(self):
        return "%s" % (self._get_sql())

    def _select_budget(self):
        return """
            select 1000000000 + mbi.id as id,
            mbi.analytic_account_id,
            mbi.date_from as date,  -- approx date
            '1_budget' as amount_type,
            mbi.amount as amount,
            bc.name as reference,
            'Version ' || bc.revision_number::char as revision_number
        """

    def _from_budget(self):
        return """
            from mis_budget_item mbi
            left outer join budget_control bc on mbi.budget_control_id = bc.id
        """

    def _where_budget(self):
        operating_unit = self._find_operating_unit()
        return """
            where mbi.state != 'draft' and bc.operating_unit_id {}
        """.format(
            operating_unit
        )

    def _get_sql(self):
        return "{} {} {}".format(
            self._select_budget(),
            self._from_budget(),
            self._where_budget(),
        )
