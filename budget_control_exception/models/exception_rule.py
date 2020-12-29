# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ExceptionRule(models.Model):
    _inherit = "exception.rule"

    budget_control_ids = fields.Many2many(
        comodel_name="budget.control", string="Budget Control"
    )
    model = fields.Selection(
        selection_add=[
            ("budget.control", "Budget Control"),
            ("mis.budget.item", "Budget Plan"),
        ],
        ondelete={
            "budget.control": "cascade",
            "mis.budget.item": "cascade",
        },
    )
