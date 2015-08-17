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
        'budget_line_ids': fields.one2many(
            'budget.line',
            'opportunity_id',
            u'Budget Line'),
        'budget_item_id': fields.many2one(
            'budget.item',
            u'Budget Item'),
        'analytic_account_id': fields.many2one(
            'account.analytic.account',
            u'Analytic Account'),
        'months': fields.integer(
            u'Duration in months'),
        'currency_id': fields.many2one(
            'res.currency',
            u'Revenue Currency'),
    }

    def write(self, cr, uid, ids, vals, context=None):
        """Get the budget item from the stage.

        The clickable progressbar does not run on_change, apparently.
        """
        if 'stage_id' in vals:
            stage_obj = self.pool['crm.case.stage']
            stage = stage_obj.browse(cr, uid, vals['stage_id'], context)

            vals['budget_item_id'] = stage.budget_item_id.id or False
            team = self.browse(cr, uid, ids, context=context)[0].section_id
            vals['analytic_account_id'] = (team
                                           and team.analytic_account_id
                                           and team.analytic_account_id.id
                                           or False)

        return super(Lead, self).write(cr, uid, ids, vals, context)

    def _get_default_analytic_account(self, cr, uid, context=None):
        user_obj = self.pool['res.users']
        team = user_obj.browse(cr, uid, uid, context).default_section_id
        return (
            team
            and team.analytic_account_id
            and team.analytic_account_id.id
            or False)

    _defaults = {
        'analytic_account_id': _get_default_analytic_account,
        'currency_id': lambda self, cr, uid, c:
            self.pool.get('res.users').browse(cr, uid,
                                              uid,
                                              c).company_id.currency_id.id,
    }
