# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    budget_include_tax = fields.Boolean(
        string="Budget Included Tax",
        help="If checked, all budget moves amount will include tax",
    )
    budget_kpi_template_id = fields.Many2one(
        comodel_name="mis.report",
        string="Budget KPI Template",
    )
