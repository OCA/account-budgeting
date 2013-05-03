# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Arnaud Wüst
#    Copyright 2009-2013 Camptocamp SA
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


class budget_budget(orm.Model):
    """ Budget Model. The module's main object.  """
    _name = "budget.budget"
    _description = "Budget"
    _order = 'name ASC'
    _columns = {
        'code': fields.char('Code'),
        'name': fields.char('Name', required=True),
        'active': fields.boolean('Active'),
        'start_date': fields.date('Start Date', required=True),
        'end_date': fields.date('End Date', required=True),
        'budget_item_id': fields.many2one('budget.item',
                                          'Budget Structure',
                                          required=True),
        'budget_version_ids': fields.one2many('budget.version',
                                              'budget_id',
                                              'Budget Versions',
                                              readonly=True),
        'note': fields.text('Notes'),
        'create_date': fields.datetime('Creation Date', readonly=True)
    }

    _defaults = {
        'active': True,
    }

    def name_search(self, cr, uid, name, args=None,
                    operator='ilike', context=None, limit=80):
        """search not only for a matching names but also for a matching
        codes """
        if context is None:
            context = {}
        if args is None:
            args = []

        ids = self.search(cr,
                          uid,
                          [('code',operator,name)] + args,
                          limit=limit,
                          context=context)
        ids += self.search(cr,
                           uid,
                           [('name',operator,name)]+ args,
                           limit=limit,
                           context=context)
        return self.name_get(cr, uid, ids, context=context)

    def _check_start_end_dates(self, cr, uid, ids):
        """ check the start date is before the end date """
        lines = self.browse(cr, uid, ids)
        for l in lines:
            if l.end_date < l.start_date:
                return False
        return True

    def _get_periods(self, cr, uid, ids, context=None):
        """ return the list of budget's periods ordered by date_start"""
        if isinstance(ids, (int, long)):
            ids = [ids]
        period_obj = self.pool.get('account.period')
        start_date = end_date = None
        result = []
        for budget in self.browse(cr, uid, ids, context=context):
            periods_ids = period_obj.search(
                cr, uid,
                [('date_stop', '>', budget.start_date),
                 ('date_start', '<', budget.end_date)],
                order="date_start ASC")
            browse = period_obj.browse
            result.append(browse(cr, uid, periods_ids, context=context))
        return result

    def _get_periods_union(self, cr, uid, ids, context=None):
        """ return the list of budget's periods ordered by date_start
            it returns a unique list that cover all given budgets ids
        """
        if context is None:
            context = {}
        period_obj = self.pool.get('account.period')
        if isinstance(ids, (int, long)):
            ids = [ids]
        # find the earliest start_date en latest end_date
        start_date = end_date = None
        for budget in self.browse(cr, uid, ids, context=context):
            if start_date is None or start_date > budget.start_date:
                start_date = budget.start_date
            if end_date is None or end_date < budget.end_date:
                end_date = budget.end_date

        period_ids = []
        if start_date is not None:
            periods_ids = period_obj.search(cr, uid,
                                            [('date_stop', '>', start_date),
                                             ('date_start', '<', end_date)],
                                            order="date_start ASC")
        return period_obj.browse(cr, uid, periods_ids, context=context)

    def unlink(self, cr, uid, ids, context=None):
        """delete all budget versions when deleting a budget """
        # XXX delete cascade is not working?
        if context is None:
            context = {}
        budget_version_obj = self.pool.get('budget.version')
        lines_ids = budget_version_obj.search(cr, uid,
                                              [('budget_id', 'in', ids)],
                                              context=context)
        budget_version_obj.unlink(cr, uid, lines_ids, context=context)
        return super(budget_budget, self).unlink(cr, uid, ids, context=context)

    _constraints = [
        (_check_start_end_dates,
         'Date Error: The end date is defined before the start date',
         ['start_date', 'end_date']),
    ]
