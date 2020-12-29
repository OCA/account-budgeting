# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetActivity(models.Model):
    _inherit = "budget.activity"

    activity_group_id = fields.Many2one(
        comodel_name="budget.activity.group",
        index=True,
    )
