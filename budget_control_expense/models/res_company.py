# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    auto_post_journal = fields.Boolean(
        string="Carry Forward - Expense Auto Post",
        help="If checked, After carry forward budget "
        "it still auto post journal when you click "
        "Post Journal Entries on Expense.",
    )
