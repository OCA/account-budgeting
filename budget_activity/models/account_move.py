# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    activity_id = fields.Many2one(
        comodel_name='budget.activity',
        string='Activity',
        index=True,
    )

    def _prepare_analytic_line(self):
        res = super()._prepare_analytic_line()
        res[0]['activity_id'] = self.activity_id.id
        return res
