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
from datetime import date, datetime
import calendar

from openerp.osv import fields, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class budget_budget(orm.Model):

    """ Budget Model. The module's main object.  """
    _name = "budget.budget"
    _description = "Budget"
    _order = 'name ASC'

    def _get_active_version(self, cr, uid, ids, field_name, arg, context=None):
        version_obj = self.pool['budget.version']
        result = {}

        for budget_id in ids:
            active_ids = version_obj.search(cr, uid, [
                ('budget_id', '=', budget_id),
                ('is_active', '=', True),
            ], context=context)

            result[budget_id] = active_ids and active_ids[0] or False

        return result

    _columns = {
        'code': fields.char('Code'),
        'name': fields.char('Name', required=True),
        'active': fields.boolean('Active'),
        'start_date': fields.date('Start Date', required=True),
        'end_date': fields.date('End Date', required=True),
        'budget_item_id': fields.many2one('budget.item',
                                          'Budget Structure',
                                          required=True,
                                          ondelete='restrict'),
        'budget_version_ids': fields.one2many('budget.version',
                                              'budget_id',
                                              'Budget Versions',
                                              readonly=True),
        'active_version_id': fields.function(
            _get_active_version,
            string='Active Version',
            type='many2one',
            relation='budget.version',
        ),
        'note': fields.text('Notes'),
        'create_date': fields.datetime('Creation Date', readonly=True)
    }

    _defaults = {
        'active': True,
    }

    def _check_start_end_dates(self, cr, uid, ids, context=None):
        """ check the start date is before the end date """
        lines = self.browse(cr, uid, ids)
        for l in lines:
            if l.end_date < l.start_date:
                return False
        return True

    _constraints = [
        (_check_start_end_dates,
         'Date Error: The end date is defined before the start date',
         ['start_date', 'end_date']),
    ]

    def name_search(self, cr, uid, name, args=None,
                    operator='ilike', context=None, limit=100):
        """ Extend search to look in name and code """
        if args is None:
            args = []
        ids = self.search(cr, uid,
                          ['|',
                           ('name', operator, name),
                           ('code', operator, name)] + args,
                          limit=limit,
                          context=context)
        return self.name_get(cr, uid, ids, context=context)

    def _get_periods(self, cr, uid, ids, context=None):
        """ return the list of budget's periods ordered by date_start"""
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        period_obj = self.pool.get('account.period')
        result = []
        for budget in self.browse(cr, uid, ids, context=context):
            period_ids = period_obj.search(
                cr, uid,
                [('date_stop', '>', budget.start_date),
                 ('date_start', '<', budget.end_date)],
                order="date_start ASC",
                context=context)
            result += period_obj.browse(cr, uid, period_ids, context=context)
        return result

    def on_change_start_date(self, cr, uid, ids, start_date_str, context=None):
        start_date = datetime.strptime(start_date_str, DATE_FORMAT)

        last_day_of_month = calendar.monthrange(start_date.year,
                                                start_date.month)[1]

        end_date = datetime(
            year=start_date.year,
            month=start_date.month,
            day=last_day_of_month)

        end_date_str = date.strftime(end_date, DATE_FORMAT)

        return {'value': {'end_date': end_date_str}}
