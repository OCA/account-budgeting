# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    activity_id = fields.Many2one(
        comodel_name="budget.activity",
        string="Activity",
        index=True,
    )

    def _get_computed_account(self):
        self.ensure_one()
        res = super()._get_computed_account()
        if self.activity_id:
            res = self.activity_id.account_id
        return res

    def _prepare_analytic_line(self):
        res = super()._prepare_analytic_line()
        res[0]["activity_id"] = self.activity_id.id
        return res

    @api.onchange("activity_id")
    def _onchange_activity_id(self):
        if self.activity_id:
            self.account_id = self.activity_id.account_id
