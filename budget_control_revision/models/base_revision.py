# Copyright 2020 Ecosoft Co., Ltd. (<http://ecosoft.co.th>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class BaseRevision(models.AbstractModel):
    _inherit = "base.revision"

    def _copy_item_ids(self, new_revision):
        for item in new_revision.item_ids:
            old_item = self.item_ids.filtered(
                lambda l: l.date_from == item.date_from
                and l.date_to == item.date_to
                and l.analytic_account_id == item.analytic_account_id
                and l.kpi_expression_id == item.kpi_expression_id
            )
            item.update({"amount": old_item.amount})

    def copy_revision_with_context(self):
        ctx = self._context.copy()
        ctx.update({"create_revision": True})
        new_revision = super(
            BaseRevision, self.with_context(ctx)
        ).copy_revision_with_context()
        self._copy_item_ids(new_revision)
        self.item_ids.write({"active": False})
        return new_revision
