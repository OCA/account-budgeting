# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Arnaud Wüst, Leonardo Pistone
#    Copyright 2009-2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, api


class BudgetVersion(models.Model):
    _inherit = "budget.version"

    @api.multi
    def make_active(self):
        super(BudgetVersion, self).make_active()
        for this_version in self:
            this_version.company_id.sudo().write(
                {'budget_version_id': this_version.id})
