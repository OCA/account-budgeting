# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class MisBudgetItem(models.Model):
    _inherit = "mis.budget.item"

    def name_get(self):
        return [
            (record.id, "{}: {}".format(record.name, record.date_range_id.name))
            for record in self
        ]

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        domain = args or []
        domain += [
            "|",
            "|",
            ("kpi_expression_id.kpi_id.description", operator, name),
            ("kpi_expression_id.kpi_id.name", operator, name),
            ("date_range_id.name", operator, name),
        ]
        return self.search(domain, limit=limit).name_get()
