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
from openerp.osv import fields, orm


class BudgetVersion(orm.Model):

    """ Budget version.

    A budget version is a budget made at a given time for a given company.
    It also can have its own currency """

    _name = "budget.version"
    _description = "Budget versions"

    _order = 'name ASC'

    _columns = {
        'code': fields.char('Code'),
        'name': fields.char('Version Name', required=True),
        'budget_id': fields.many2one('budget.budget',
                                     string='Budget',
                                     required=True,
                                     ondelete='cascade'),
        'currency_id': fields.many2one('res.currency',
                                       string='Currency',
                                       required=True),
        'company_id': fields.many2one('res.company',
                                      string='Company',
                                      required=True),
        'user_id': fields.many2one('res.users', string='User In Charge'),
        'budget_line_ids': fields.one2many('budget.line',
                                           'budget_version_id',
                                           string='Budget Lines'),
        'note': fields.text('Notes'),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'ref_date': fields.date('Reference Date', required=True),
        'is_active': fields.boolean(
            'Active version',
            readonly=True,
            help='Each budget can have no more than one active version.')
    }

    _defaults = {
        'ref_date': fields.date.context_today,
        'company_id':
        lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(
            cr, uid, 'account.account', context=c),
    }

    def name_search(self, cr, uid, name, args=None, operator='ilike',
                    context=None, limit=100):
        """Extend search to name and code. """

        if args is None:
            args = []
        ids = self.search(cr, uid,
                          ['|',
                           ('name', operator, name),
                           ('code', operator, name)] + args,
                          limit=limit,
                          context=context)
        return self.name_get(cr, uid, ids, context=context)

    def _get_periods(self, cr, uid, version, context=None):
        """return periods informations used by this version.

        (the periods are those between start and end dates defined in
         budget)"""
        budget_obj = self.pool.get('budget.budget')
        return budget_obj._get_periods(cr, uid, version.budget_id.id,
                                       context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        self.write(cr, uid, id, {'is_active': False}, context)

        if default is None:
            default = {}

        default['budget_line_ids'] = []

        return super(BudgetVersion, self).copy(
            cr, uid, id, default, context)

    def make_active(self, cr, uid, ids, context=None):
        for this_version in self.browse(cr, uid, ids, context):
            this_version.write({'is_active': True})

            other_versions = self.search(cr, uid, [
                ('budget_id', '=', this_version.budget_id.id),
                ('id', '!=', this_version.id),
            ], context=context)
            self.write(cr, uid, other_versions, {'is_active': False}, context)
