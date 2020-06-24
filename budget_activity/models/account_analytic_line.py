# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    activity_id = fields.Many2one(
        comodel_name='budget.activity',
        string='Activity',
        index=True,
    )
