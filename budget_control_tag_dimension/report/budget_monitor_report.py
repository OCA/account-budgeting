# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class BudgetMonitorReport(models.Model):
    _inherit = 'budget.monitor.report'

    def _get_dimension_fields(self):
        return [x for x in self.fields_get().keys()
                if x.startswith("x_dimension_")]

    def _add_x_dimensions(self, res):
        add_fields = self._get_dimension_fields()
        add_fields = [", a.{0} as {0}".format(x) for x in add_fields]
        return res + "".join(add_fields)

    # Budget Control
    def _select_budget(self):
        res = super()._select_budget()
        res = self._add_x_dimensions(res)
        return res

    def _select_actual(self):
        res = super()._select_actual()
        return self._add_x_dimensions(res)
