# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class BudgetControl(models.Model):
    _inherit = "budget.control"

    transfer_item_ids = fields.Many2many(
        comodel_name="budget.transfer.item",
        string="Transfers",
        compute="_compute_transfer_item_ids",
    )
    transferred_amount = fields.Monetary(
        string="Transferred Amount",
        compute="_compute_transferred_amount",
    )

    @api.depends("allocated_amount", "transferred_amount")
    def _compute_allocated_released_amount(self):
        super()._compute_allocated_released_amount()
        for rec in self:
            rec.released_amount = rec.allocated_amount + rec.transferred_amount

    def _get_domain_transfer_item_ids(self):
        self.ensure_one()
        return [
            ("state", "=", "transfer"),
            "|",
            ("source_budget_control_id", "=", self.id),
            ("target_budget_control_id", "=", self.id),
        ]

    def _compute_transfer_item_ids(self):
        TransferItem = self.env["budget.transfer.item"]
        for rec in self:
            items = TransferItem.search(rec._get_domain_transfer_item_ids())
            rec.transfer_item_ids = items

    @api.depends("transfer_item_ids")
    def _compute_transferred_amount(self):
        for rec in self:
            total_amount = 0.0
            for item in rec.transfer_item_ids:
                if item.source_budget_control_id.id == rec.id:
                    total_amount -= item.amount
                if item.target_budget_control_id.id == rec.id:
                    total_amount += item.amount
            rec.transferred_amount = total_amount

    def action_open_budget_transfer_item(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update({"create": False, "edit": False})
        items = self.transfer_item_ids
        list_view = self.env.ref(
            "budget_control_transfer.view_budget_transfer_item_tree"
        ).id
        form_view = self.env.ref(
            "budget_control_transfer.view_budget_transfer_item_form"
        ).id
        return {
            "name": _("Budget Transfer Items"),
            "type": "ir.actions.act_window",
            "res_model": "budget.transfer.item",
            "views": [[list_view, "list"], [form_view, "form"]],
            "view_mode": "list",
            "context": ctx,
            "domain": [("id", "in", items and items.ids or [])],
        }
