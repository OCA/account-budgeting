# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Leonardo Pistone
#    Copyright 2014 Camptocamp SA
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

from openerp.osv import orm, fields


class Lead(orm.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    _columns = {
        'budget_line_id': fields.many2one(
            'budget.line',
            u'Budget Line'),
        'budget_item_id': fields.many2one(
            'budget.item',
            u'Budget Item'),
        'analytic_account_id': fields.many2one(
            'account.analytic.account',
            u'Analytic Account',
            required=True),
    }

    def _get_default_analytic_account(self, cr, uid, context=None):
        team_id = self._get_default_section_id(cr, uid, context)
        if team_id:
            team_obj = self.pool['crm.case.section']
            team = team_obj.browse(cr, uid, team_id, context)
            return (
                team.analytic_account_id
                and team.analytic_account_id.id
                or False)
        else:
            return False

    _default = {
        'analytic_account_id': _get_default_analytic_account,
    }
