# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SourceFundMonitorReport(models.Model):
    _name = "source.fund.monitor.report"
    _description = "Source Fund Monitoring Report"
    _auto = False
    _order = "fund_name desc"

    fund_name = fields.Char()
    date_range_id = fields.Many2one(comodel_name="date.range")
    date_from = fields.Date()
    date_to = fields.Date()
    budget_control_id = fields.Many2one(comodel_name="budget.control")
    amount = fields.Float()
    spent = fields.Float()
    fund_group_name = fields.Char(string="Fund Group")

    @property
    def _table_query(self):
        return "%s" % (self._get_sql())

    def _select_source_fund(self):
        return """
            select sf_line.id, sf_line.date_range_id, sf_line.date_from,
            sf_line.date_to, sf_line.budget_control_id, sf_line.amount,
            sf_line.spent, sf.name as fund_name, sf_group.name as fund_group_name
        """

    def _from_source_fund(self):
        return """
            from budget_source_fund_line sf_line
            join budget_source_fund sf on sf_line.fund_id = sf.id
            left join budget_source_fund_group sf_group
            on sf.fund_group_id = sf_group.id
        """

    def _where_source_fund(self):
        return """
            where sf.active is true
        """

    def _get_sql(self):
        return "{} {} {}".format(
            self._select_source_fund(),
            self._from_source_fund(),
            self._where_source_fund(),
        )
