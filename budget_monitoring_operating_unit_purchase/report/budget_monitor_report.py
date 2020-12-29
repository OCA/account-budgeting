# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BudgetMonitorReport(models.Model):
    _inherit = "budget.monitor.report"

    def _select_po_commit(self):
        select_po_query = super()._select_po_commit()
        select_po_query = ",".join([select_po_query, "b.operating_unit_id"])
        return select_po_query
