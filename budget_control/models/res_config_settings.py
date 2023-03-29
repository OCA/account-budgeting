# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Tax Included
    budget_include_tax = fields.Boolean(
        related="company_id.budget_include_tax", readonly=False
    )
    budget_include_tax_method = fields.Selection(
        related="company_id.budget_include_tax_method", readonly=False
    )
    budget_include_tax_account = fields.Many2many(
        related="company_id.budget_include_tax_account", readonly=False
    )
    budget_include_tax_purchase = fields.Many2many(
        related="company_id.budget_include_tax_purchase", readonly=False
    )
    budget_include_tax_expense = fields.Many2many(
        related="company_id.budget_include_tax_expense", readonly=False
    )
    # --
    budget_template_id = fields.Many2one(
        comodel_name="budget.template",
        related="company_id.budget_template_id",
        readonly=False,
    )
    group_required_analytic = fields.Boolean(
        string="Required Analytic Account",
        implied_group="budget_control.group_required_analytic",
    )
    group_budget_date_commit = fields.Boolean(
        string="Enable Date Commit",
        implied_group="budget_control.group_budget_date_commit",
    )
    # Modules
    budget_control_account = fields.Boolean(
        string="Account",
        default=True,
        readonly=True,
    )
    module_budget_control_purchase_request = fields.Boolean(string="Purchase Request")
    module_budget_control_purchase = fields.Boolean(string="Purchase")
    module_budget_control_expense = fields.Boolean(string="Expense")
    module_budget_control_advance_clearing = fields.Boolean(string="Advance/Clearing")
    module_budget_plan = fields.Boolean(string="Budget Plan")
