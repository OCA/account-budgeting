# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BudgetTemplate(models.Model):
    _name = "budget.template"
    _description = "Budget Template"

    name = fields.Char(required=True)
    line_ids = fields.One2many(
        comodel_name="budget.template.line",
        inverse_name="template_id",
    )


class BudgetTemplateLine(models.Model):
    _name = "budget.template.line"
    _description = "Budget Template Lines"

    template_id = fields.Many2one(
        comodel_name="budget.template",
        index=True,
        ondelete="cascade",
        readonly=True,
    )
    name = fields.Char(
        compute="_compute_name",
        store=True,
    )
    kpi_id = fields.Many2one(
        comodel_name="budget.kpi",
        string="KPI",
        required=True,
        ondelete="restrict",
        index=True,
    )
    account_ids = fields.Many2many(
        comodel_name="account.account",
        relation="budget_kpi_account_rel",
        column1="budget_kpi_id",
        column2="account_id",
        required=True,
    )

    @api.depends("kpi_id")
    def _compute_name(self):
        for rec in self:
            rec.name = rec.kpi_id.name
