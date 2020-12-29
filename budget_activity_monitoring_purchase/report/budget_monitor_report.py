# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BudgetMonitorReport(models.Model):
    _inherit = "budget.monitor.report"

    # Purchase
    def _select_po_commit(self):
        select_po_query = super()._select_po_commit()
        select_po_query = ",".join([select_po_query, "ba.name as activity_name"])
        return select_po_query

    def _from_po_commit(self):
        from_po_query = super()._from_po_commit()
        from_po_query = "\n".join(
            [
                from_po_query,
                "left outer join budget_activity ba on a.activity_id = ba.id",
            ]
        )
        return from_po_query
