# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetActivity(models.Model):
    _name = "budget.activity"
    _description = "Activity"

    name = fields.Char(
        required=True,
    )
    active = fields.Boolean(default=True)
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account",
        domain=[("deprecated", "=", False)],
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    code = fields.Char(related="account_id.code")
