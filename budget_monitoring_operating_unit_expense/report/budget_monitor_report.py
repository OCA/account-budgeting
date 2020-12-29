# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BudgetMonitorReport(models.Model):
    _inherit = "budget.monitor.report"

    def _select_ex_commit(self):
        select_ex_query = super()._select_ex_commit()
        select_ex_query = ",".join([select_ex_query, "b.operating_unit_id"])
        return select_ex_query
