# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MisBudgetItemAbstract(models.AbstractModel):
    _inherit = "mis.budget.item.abstract"

    def _prepare_overlap_domain(self):
        domain = super()._prepare_overlap_domain()
        # search domain impossible when create revision
        if self._context.get("create_revision", False):
            domain.append(("budget_control_id", "=", False))
        return domain
