# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class MisBudgetItem(models.Model):
    _inherit = "mis.budget.item"
    _order = "date_range_id, kpi_expression_id"

    budget_control_id = fields.Many2one(
        comodel_name="budget.control",
        ondelete="cascade",
        index=True,
        required=True,
    )
    kpi_id = fields.Many2one(
        comodel_name="mis.report.kpi",
        related="kpi_expression_id.kpi_id",
        store=True,
    )
    active = fields.Boolean(
        compute="_compute_active",
        readonly=True,
        store=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submit", "Submitted"),
            ("done", "Controlled"),
            ("cancel", "Cancelled"),
        ],
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
            rec.active = rec.budget_control_id.active if rec.budget_control_id else True

    def search_neutralize(self, dom):
        if len(dom) == 3 and dom[0] == "date":
            return (1, "=", 1)
        return dom

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        args = [
            isinstance(arg, tuple) and self.search_neutralize(arg) or arg
            for arg in args
        ]
        return super().search(args, offset, limit, order, count)
