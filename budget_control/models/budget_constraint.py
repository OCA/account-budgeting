# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetConstraint(models.Model):
    _name = "budget.constraint"
    _inherit = "mail.thread"
    _description = "Constraint Budget by server action"
    _order = "sequence"

    sequence = fields.Integer(default=1, required=True)
    name = fields.Char(required=True)
    description = fields.Text()
    server_action_id = fields.Many2one(
        comodel_name="ir.actions.server",
        string="Server Action",
        domain=[
            ("usage", "=", "ir_actions_server"),
            ("model_id.model", "=", "budget.constraint"),
        ],
        help="Server action triggered as soon as this step is check_budget",
    )
    active = fields.Boolean(default=True)
