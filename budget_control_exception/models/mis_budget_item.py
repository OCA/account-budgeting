# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class MisBudgetItem(models.Model):
    _name = "mis.budget.item"
    _inherit = ["mis.budget.item", "base.exception.method"]

    ignore_exception = fields.Boolean(
        related="budget_control_id.ignore_exception",
        store=True,
        string="Ignore Exceptions",
    )

    def _get_main_records(self):
        return self.mapped("budget_control_id")

    @api.model
    def _reverse_field(self):
        return "budget_control_ids"

    def _detect_exceptions(self, rule):
        records = super()._detect_exceptions(rule)
        return records.mapped("budget_control_id")
