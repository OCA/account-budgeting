# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetSourceFundGroup(models.Model):
    _name = "budget.source.fund.group"
    _inherit = ["mail.thread"]
    _description = "Source of Fund Group"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [("unique_name", "UNIQUE(name)", "Group must be unique")]
