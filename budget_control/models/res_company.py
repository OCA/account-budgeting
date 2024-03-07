# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    budget_include_tax = fields.Boolean(
        string="Budget Included Tax",
        help="If checked, all budget moves amount will include tax",
    )
    budget_include_tax_method = fields.Selection(
        selection=[
            ("all", "All documents & taxes"),
            ("specific", "Specific document & taxes"),
        ],
        default="all",
    )
    budget_include_tax_account = fields.Many2many(
        comodel_name="account.tax",
        relation="company_budget_include_tax_account_rel",
        column1="company_id",
        column2="tax_id",
    )
    budget_include_tax_purchase = fields.Many2many(
        comodel_name="account.tax",
        relation="company_budget_include_tax_purchase_rel",
        column1="company_id",
        column2="tax_id",
    )
    budget_include_tax_expense = fields.Many2many(
        comodel_name="account.tax",
        relation="company_budget_include_tax_expense_rel",
        column1="company_id",
        column2="tax_id",
    )
    budget_template_id = fields.Many2one(
        comodel_name="budget.template",
        string="Budget Template",
    )
