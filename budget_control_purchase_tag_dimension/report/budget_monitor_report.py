# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class BudgetMonitorReport(models.Model):
    _inherit = 'budget.monitor.report'

    # Purchase Budget
    def _select_po_commit(self):
        res = super()._select_po_commit()
        return self._add_x_dimensions(res)
