# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetSourceFund(models.Model):
    _name = "budget.source.fund"
    _inherit = ["mail.thread"]
    _description = "Source of Fund"
    _order = "name"

    name = fields.Char(required=True, string="Source of Fund")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company", default=lambda self: self.env.company, readonly=True
    )
    fund_group_id = fields.Many2one(
        comodel_name="budget.source.fund.group",
        string="Fund Group",
        tracking=True,
    )
    fund_line_ids = fields.One2many(
        comodel_name="budget.source.fund.line",
        inverse_name="fund_id",
        string="Fund Line",
        readonly=True,
    )

    _sql_constraints = [("unique_name", "UNIQUE(name)", "Group must be unique")]


class BudgetSourceFundLine(models.Model):
    _name = "budget.source.fund.line"
    _description = "Source of Fund Line"

    fund_id = fields.Many2one(comodel_name="budget.source.fund", readonly=True)
    active = fields.Boolean(related="fund_id.active")
    date_range_id = fields.Many2one(
        comodel_name="date.range",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_from = fields.Date(
        required=True,
        string="From",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_to = fields.Date(
        required=True,
        string="To",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    budget_control_id = fields.Many2one(
        comodel_name="budget.control", copy=False, readonly=True
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="fund_id.company_id.currency_id",
        string="Company Currency",
        readonly=True,
        help="Utility field to fund amount currency",
    )
    amount = fields.Monetary(
        default=0.0,
        currency_field="company_currency_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    spent = fields.Monetary(default=0.0, currency_field="company_currency_id")
    state = fields.Selection(related="budget_control_id.state")
