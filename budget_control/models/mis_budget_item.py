# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class MisBudgetItem(models.Model):
    _inherit = "mis.budget.item"

    budget_control_id = fields.Many2one(
        comodel_name="budget.control",
        ondelete="cascade",
        index=True,
    )
    active = fields.Boolean(
        compute="_compute_active",
        readonly=True,
        store=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Controlled"), ("cancel", "Cancelled")],
        string="Status",
        compute="_compute_budget_control_state",
        store=True,
        index=True,
    )

    def _compute_name(self):
        """ Overwrite name using KPI only """
        for rec in self:
            rec.name = rec.kpi_expression_id.kpi_id.display_name

    @api.depends("budget_control_id.state")
    def _compute_budget_control_state(self):
        for rec in self:
            rec.state = rec.budget_control_id.state

    @api.depends("budget_control_id.active")
    def _compute_active(self):
        for rec in self:
            rec.active = rec.budget_control_id and rec.budget_control_id.active or True
