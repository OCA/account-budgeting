# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class BudgetMonitorReport(models.Model):
    _inherit = "budget.monitor.report"

    def _get_consumed_sources(self):
        return super()._get_consumed_sources() + [
            {
                "model": ("hr.expense", "Expense"),
                "type": ("5_ex_commit", "EX Commit"),
                "budget_move": ("expense_budget_move", "expense_id"),
                "source_doc": ("hr_expense_sheet", "sheet_id"),
            }
        ]

    def _where_expense(self):
        return ""

    def _get_sql(self):
        select_ex_query = self._select_statement("5_ex_commit")
        key_select_list = sorted(select_ex_query.keys())
        select_ex = ", ".join(select_ex_query[x] for x in key_select_list)
        return super()._get_sql() + "union (select {} {} {})".format(
            select_ex,
            self._from_statement("5_ex_commit"),
            self._where_expense(),
        )
