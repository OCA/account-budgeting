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
import time
from openerp.osv import fields, orm


class c2c_budget_version(orm.Model):
    """ Budget version.

    A budget version is a budget made at a given time for a given company.
    It also can have its own currency """

    _name = "c2c_budget.version"
    _description = "Budget versions"

    _order = 'name ASC'

    _columns = {
        'code': fields.char('Code'),
        'name': fields.char('Version Name',  required=True),
        'budget_id': fields.many2one('c2c_budget',
                                     string='Budget',
                                     required=True),
        'currency_id': fields.many2one('res.currency',
                                       string='Currency',
                                       required=True),
        'company_id': fields.many2one('res.company',
                                      string='Company',
                                      required=True),
        'user_id': fields.many2one('res.users', string='User In Charge'),
        'budget_line_ids': fields.one2many('c2c_budget.line',
                                           'budget_version_id',
                                           string='Budget Lines'),
        'note': fields.text('Notes'),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'ref_date': fields.date('Reference Date', required=True),
    }

    _defaults = {
        'ref_date': fields.date.context_today,
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(
                                                    cr, uid, 'account.account', context=c),
    }

    def get_period(self, cr, uid, version, date, context=None):
        """ return the period corresponding to the given date
        for the given version """
        period_obj = self.pool.get('account.period')
        period_ids = period_obj.search(cr, uid,
                                       [('date_start', '<=', date),
                                        ('date_stop', '>=', date)],
                                       context=context)
        periods_tmp = period_obj.browse(cr, uid, period_ids, context=context)
        if len(periods_tmp) > 0:
            return periods_tmp[0]
        return None

    def get_periods(self, cr, uid, version, context=None):
        """return periods informations used by this version.
        (the periods are those between start and end dates defined in
        budget)"""
        budget_obj = self.pool.get('c2c_budget')
        return budget_obj.get_periods(cr, uid, version.budget_id.id)

    def get_next_periods(self, cr, uid,  version, start_period,
                         periods_nbr, context=None):
        """ return a list of "periods_nbr" periods that follow the
        "start_period" for the given version """
        period_obj = self.pool.get('account.period')
        period_ids = period_obj.search(
            cr, uid,
            [('date_start', '>', start_period.date_start)],
            order="date_start ASC",
            limit=periods_nbr,
            context=context)
        return period_obj.browse(cr, uid, period_ids, context=context)

    def get_previous_period(self, cr, uid, version, period, context=None):
        """ return the period that preceed the one given in param.
            return None if there is no preceeding period defined """
        period_obj = self.pool.get('account.period')
        ids = period_obj.search(cr, uid,
                                [('date_stop', '<', period.date_start)],
                                order="date_start DESC",
                                context=context)
        periods = period_obj.browse(cr, uid, ids, context)
        if len(periods) > 0:
            return periods[0]
        return None

    def get_next_period(self, cr, uid, version, period, context=None):
        """ return the period that follow the one given in param.
            return None if there is no next period defined """
        nexts = self.get_next_periods(cr, uid, version, period, 1, context)
        if len(nexts) > 0:
            return nexts[0]
        return None

    def get_filtered_budget_values(self, cr, uid, version, lines,
                                   period_start=None, period_end=None,
                                   context=None):
        """
        for a given version compute items' values on lines between
        period_start and period_end included
        version is a budget_version object
        lines is a list of budget_lines objects to work on
        period_start is a c2c_budget.period object
        period_end is a c2c_budget.period object
        return a dict: item_id => value
        """
        if context is None:
            context = {}
        # find periods used by this version that stand between
        # period_start and period_end included.
        filtered_periods = []
        periods = self.get_periods(cr, uid, version, context=context)
        start = period_start.date_start if period_start is not None else None
        stop = period_start.date_stop if period_end is not None else None
        periods = [period for period in periods
                   if (start is None or period.date_start >= start)
                   and (stop is None or period.date_stop <= stop)]

        # get lines related to this periods
        budget_lines_obj = self.pool.get('c2c_budget.line')
        filtered_lines = budget_lines_obj.filter_by_period(
            cr, uid, lines, [p.id for p in periods], context=context)
        # compute budget values on those lines
        return self.get_budget_values(cr, uid, version,
                                      filtered_lines, context=context)

    def get_budget_values(self, cr, uid, version, lines, context=None):
        """ for a given version compute items' values on lines
            version is a budget_version object
            lines is a list of budget_lines objects to work on
            return a dict: item_id => value
        """
        if context is None:
            context = {}
        budget_item_obj = self.pool.get('c2c_budget.item')
        item_id = version.budget_id.budget_item_id.id
        items = budget_item_obj.get_sorted_list(cr, uid, item_id)
        items_results = dict.fromkeys((item.id for item in items), 0.)
        for item in items:
            sub_items_ids = budget_item_obj.get_sub_items(cr, [item.id])
            for line in lines:
                if line.budget_version_id.id != version.id:
                    continue
                if line.budget_item_id.id not in sub_items_ids:
                    continue
                items_results[item.id] += line.amount_in_budget_currency
        # complete results with calculated items
        return budget_item_obj.compute_view_items(items, items_results)

    def get_real_values_from_analytic_accounts(self, cr, uid,
                                               version, lines, context=None):
        """ return the values from the analytic accounts """
        if context is None:
            context = {}
        item_obj = self.pool.get('c2c_budget.item')
        item_id = version.budget_id.budget_item_id.id
        items = item_obj.get_sorted_list(cr, uid, item_id, context=context)
        items_results = dict.fromkeys((item.id for item in items), 0.)
        line_obj = self.pool.get('c2c_budget.line')
        periods = self.get_periods(cr, uid, version, context=context)
        for item in items:
            items_results[item.id] = item_obj.get_real_values_from_analytic_accounts(
                cr, uid,
                item.id,
                periods,
                lines,
                version.company_id.id,
                version.currency_id.id,
                version.ref_date,
                context=context)
        # complete results with calculated items
        return item_obj.compute_view_items(items, items_results)

    def get_real_values(self, cr, uid, version, lines, context=None):
        """ return the values from the general account """
        if context is None:
            context = {}
        item_obj = self.pool.get('c2c_budget.item')
        item_id = version.budget_id.budget_item_id.id
        items = item_obj.get_sorted_list(cr, uid, item_id, context=context)
        items_results = dict.fromkeys((item.id for item in items), 0.)
        line_obj = self.pool.get('c2c_budget.line')
        periods = self.get_periods(cr, uid, version, context=context)
        for item in items:
            items_results[item.id] = item_obj.get_real_values(
                cr, uid,
                item,
                periods,
                version.company_id.id,
                version.currency_id.id,
                version.ref_date,
                context=context)
        # complete results with calculated items
        return item_obj.compute_view_items(items, items_results)

    def get_percent_values(self, cr, uid, ref_datas, ref_id, context=None):
        """ build a dictionnary item_id => value that compare each values
            of ref_datas to one of them.
            ref_datas is a dictionnary as get_budget_values() returns
            ref_id is one of the keys of ref_datas.
        """
        result = {}
        ref_value = 1
        if ref_id in ref_datas:
            ref_value = ref_datas[ref_id]

        # % calculation is impossible on a 0 value or on texts (for
        # exemple: "error!")
        for id in ref_datas:
            try:
                result[id] = (ref_datas[id] / ref_value) * 100
            except:
                result[id] = 'error'

        return result

    def name_search(self, cr, uid, name, args=None, operator='ilike',
                    context=None, limit=80):
        """search not only for a matching names but also
        for a matching codes. Search also in budget names """

        if args is None:
            args = []
        ids = self.search(cr, uid,
                          [('name', operator, name)] + args,
                          limit=limit,
                          context=context)

        if len(ids) < limit:
            ids += self.search(cr, uid,
                               [('code', operator, name)] + args,
                               limit=limit,
                               context=context)
        ids = ids[:limit]
        return self.name_get(cr, uid, ids, context)

    def unlink(self, cr, uid, ids, context=None):
        """delete all budget lines when deleting a budget version """
        # XXX delete cascade?
        budget_lines_obj = self.pool.get('c2c_budget.line')
        lines_ids = budget_lines_obj.search(cr,
                                            uid,
                                            [('budget_version_id', 'in', ids)],
                                            context=context)
        budget_lines_obj.unlink(cr, uid, lines_ids, context)
        return super(c2c_budget_version, self).unlink(cr, uid, ids,
                                                      context=context)
