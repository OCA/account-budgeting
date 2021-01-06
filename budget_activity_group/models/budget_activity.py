# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class BudgetActivity(models.Model):
    _inherit = "budget.activity"

    activity_group_id = fields.Many2one(
        comodel_name="budget.activity.group",
        index=True,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        compute="_compute_account_id",
        store=True,
        readonly=False,
        required=False,
    )

    @api.depends("activity_group_id")
    def _compute_account_id(self):
        for rec in self:
            rec.account_id = (
                not rec.account_id
                and rec.activity_group_id.account_id
                or rec.account_id
            )
