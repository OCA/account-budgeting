# Copyright 2015-2019 ACSONE SA/NV (<http://acsone.eu>)
# Copyright 2021 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    not_affect_budget = fields.Boolean(
        string="Not Affect Budget",
        help="Default value for journal entry",
    )
