# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetMonitorReport(models.Model):
    _inherit = "budget.monitor.report"

    res_id = fields.Reference(
        selection_add=[("purchase.request.line", "Purchase Request Line")],
    )
    amount_type = fields.Selection(
        selection_add=[("2_pr_commit", "PR Commit")],
    )

    def _select_pr_commit(self):
        return """
            select 2000000000 + a.id as id,
            'purchase.request.line,' || a.purchase_request_line_id as res_id,
            null::char as kpi_name,
            a.analytic_account_id,
            a.date as date,
            '2_pr_commit' as amount_type,
            a.credit-a.debit as amount,
            a.account_id,
            b.name as reference
       """

    def _from_pr_commit(self):
        return """
            from purchase_request_budget_move a
            left outer join purchase_request b on a.purchase_request_id = b.id
        """

    def _get_sql(self):
        return super()._get_sql() + "union ({} {})".format(
            self._select_pr_commit(),
            self._from_pr_commit(),
        )
