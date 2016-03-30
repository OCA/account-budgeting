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
from operator import itemgetter
from itertools import imap
from openerp.osv import fields, orm
from openerp.addons import decimal_precision as dp


class budget_line(orm.Model):

    """ Budget line.

    A budget version line NOT linked to an analytic account """

    _name = "budget.line"
    _description = "Budget Lines"

    _order = 'name ASC'

    def _get_alloc_rel(self, cr, uid, ids, context=None):
        item_obj = self.pool['budget.item']
        line_obj = self.pool['budget.line']
        item_ids = item_obj.search(cr, uid, [('allocation_id', 'in', ids)],
                                   context=context)
        if item_ids:
            line_ids = line_obj.search(cr, uid,
                                       [('budget_item_id', 'in', item_ids)],
                                       context=context)
            return line_ids
        return []

    _store_tuple = (lambda self, cr, uid, ids, c=None: ids,
                    ['budget_item_id'], 10)
    _alloc_store_tuple = (_get_alloc_rel, [], 20)

    def _get_budget_currency_amount(self, cr, uid, ids, name, arg,
                                    context=None):
        """ return the line's amount xchanged in the budget's currency """
        res = {}
        currency_obj = self.pool.get('res.currency')
        # We get all values from DB
        for line in self.browse(cr, uid, ids, context=context):
            budget_currency_id = line.budget_currency_id.id
            res[line.id] = currency_obj.compute(cr, uid,
                                                line.currency_id.id,
                                                budget_currency_id,
                                                line.amount,
                                                context=context)
        return res

    def _get_analytic_amount(self, cr, uid, ids, field_names=None,
                             arg=False, context=None):
        """ Compute the amounts in the analytic account's currency"""
        res = {}
        if field_names is None:
            field_names = []
        currency_obj = self.pool.get('res.currency')
        anl_lines_obj = self.pool.get('account.analytic.line')

        for line in self.browse(cr, uid, ids, context=context):
            anl_account = line.analytic_account_id
            if not anl_account:
                res[line.id] = dict.fromkeys(field_names, 0.0)
                continue

            line_currency_id = line.currency_id.id
            anl_currency_id = line.analytic_currency_id.id
            amount = currency_obj.compute(cr, uid,
                                          line_currency_id,
                                          anl_currency_id,
                                          line.amount,
                                          context=context)
            fnl_account_ids = [acc.id for acc
                               in line.budget_item_id.all_account_ids]

            # real amount is the total of analytic lines
            # within the time frame, we'll read it in the
            # analytic account's currency, as for the
            # the budget line so we can compare them
            domain = [('account_id', 'child_of', anl_account.id),
                      ('general_account_id', 'in', fnl_account_ids)]
            if line.date_start:
                domain.append(('date', '>=', line.date_start))
            if line.date_stop:
                domain.append(('date', '<=', line.date_stop))
            anl_line_ids = anl_lines_obj.search(cr, uid, domain,
                                                context=context)
            anl_lines = anl_lines_obj.read(
                cr, uid, anl_line_ids, ['aa_amount_currency'], context=context)
            real = sum([l['aa_amount_currency'] for l in anl_lines])
            res[line.id] = {
                'analytic_amount': amount,
                'analytic_real_amount': real,
                'analytic_diff_amount': real - amount,
            }
        return res

    def _get_budget_version_currency(self, cr, uid, context=None):
        """ return the default currency for this line of account.
        The default currency is the currency set for the budget
        version if it exists """
        if context is None:
            context = {}
        # if the budget currency is already set
        return context.get('currency_id', False)

    def _fetch_budget_line_from_aal(self, cr, uid, ids, context=None):
        """
        return the list of budget line to which belong the
        analytic.account.line `ids´
        """
        account_ids = []
        budget_line_obj = self.pool.get('budget.line')
        for aal in self.browse(cr, uid, ids, context=context):
            if aal.account_id and aal.account_id.id not in account_ids:
                account_ids.append(aal.account_id.id)

        line_ids = budget_line_obj.search(cr,
                                          uid,
                                          [('analytic_account_id',
                                            'in',
                                            account_ids)],
                                          context=context)
        return line_ids

    _columns = {
        'date_start': fields.date('Start Date'),
        'date_stop': fields.date('End Date'),
        'analytic_account_id': fields.many2one(
            'account.analytic.account',
            string='Analytic Account',
            domain="[('state', '=', 'open'), ('type', '!=', 'view')]"),
        'budget_item_id': fields.many2one('budget.item',
                                          'Budget Item',
                                          required=True,
                                          ondelete='restrict'),
        'allocation': fields.related(
            'budget_item_id',
            'allocation_id',
            'name',
            type='char',
            string='Budget Item Allocation',
            select=True,
            readonly=True,
            store={
                'budget.line': _store_tuple,
                'budget.allocation.type': _alloc_store_tuple}),
        'name': fields.char('Description'),
        'amount': fields.float('Amount', required=True),
        'currency_id': fields.many2one('res.currency',
                                       'Currency',
                                       required=True),
        'budget_amount': fields.function(
            _get_budget_currency_amount,
            type='float',
            precision=dp.get_precision('Account'),
            string="In Budget's Currency",
            store=True),
        'budget_currency_id': fields.related('budget_version_id',
                                             'currency_id',
                                             type='many2one',
                                             relation='res.currency',
                                             string='Budget Currency',
                                             readonly=True),
        'budget_version_id': fields.many2one('budget.version',
                                             'Budget Version',
                                             required=True,
                                             ondelete='cascade'),
        'analytic_amount': fields.function(
            _get_analytic_amount,
            type='float',
            precision=dp.get_precision('Account'),
            multi='analytic',
            string="In Analytic Amount's Currency",
            store={
                'budget.line': (lambda self, cr, uid, ids, c: ids,
                                ['amount',
                                 'date_start',
                                 'date_stop',
                                 'analytic_account_id',
                                 'currency_id'], 10),
                'account.analytic.line': (_fetch_budget_line_from_aal,
                                          ['amount',
                                           'unit_amount',
                                           'date'], 10),
            }
        ),
        'analytic_real_amount': fields.function(
            _get_analytic_amount,
            type='float',
            precision=dp.get_precision('Account'),
            multi='analytic',
            string="Analytic Real Amount",
            store={
                'budget.line': (lambda self, cr, uid, ids, c: ids,
                                ['amount',
                                 'date_start',
                                 'date_stop',
                                 'analytic_account_id',
                                 'currency_id'], 10),
                'account.analytic.line': (_fetch_budget_line_from_aal,
                                          ['amount',
                                           'unit_amount',
                                           'date'], 10),
            }
        ),
        'analytic_diff_amount': fields.function(
            _get_analytic_amount,
            type='float',
            precision=dp.get_precision('Account'),
            multi='analytic',
            string="Analytic Difference Amount",
            store={
                'budget.line': (lambda self, cr, uid, ids, c: ids,
                                ['amount',
                                 'date_start',
                                 'date_stop',
                                 'analytic_account_id',
                                 'currency_id'], 10),
                'account.analytic.line': (_fetch_budget_line_from_aal,
                                          ['amount',
                                           'unit_amount',
                                           'date'], 10),
            }
        ),
        'analytic_currency_id': fields.related('analytic_account_id',
                                               'currency_id',
                                               type='many2one',
                                               relation='res.currency',
                                               string='Analytic Currency',
                                               readonly=True)
    }

    _defaults = {
        'currency_id': lambda self, cr, uid, context:
        self._get_budget_version_currency(cr, uid, context)
    }

    def _check_item_in_budget_tree(self, cr, uid, ids, context=None):
        """ check if the line's budget item is in the budget's structure """
        lines = self.browse(cr, uid, ids, context=context)
        budget_item_obj = self.pool.get('budget.item')
        for line in lines:
            item_id = line.budget_version_id.budget_id.budget_item_id.id
            # get list of budget items for this budget
            flat_items_ids = budget_item_obj.get_sub_item_ids(cr, uid,
                                                              [item_id],
                                                              context=context)
            if line.budget_item_id.id not in flat_items_ids:
                return False
        return True

    def _check_dates_budget(self, cr, uid, ids, context=None):
        """ check if the line dates are within the budget's dates """
        def date_valid(date, budget):
            if not date:
                return True
            return (date >= budget.start_date and
                    date <= budget.end_date)
        lines = self.browse(cr, uid, ids, context=context)
        return all(date_valid(line.date_start,
                              line.budget_version_id.budget_id) and
                   date_valid(line.date_stop,
                              line.budget_version_id.budget_id)
                   for line in lines)

    def _check_dates(self, cr, uid, ids, context=None):
        def dates_valid(start, stop):
            if not start or not stop:
                return True
            return start <= stop
        lines = self.browse(cr, uid, ids, context=context)
        return all(dates_valid(line.date_start, line.date_stop)
                   for line in lines)

    _constraints = [
        (_check_dates_budget,
         "The line's dates must be within the budget's start and end dates",
         ['date_start', 'date_stop']),
        (_check_dates,
         "The end date must be after the start date.",
         ['date_start', 'date_stop']),
        (_check_item_in_budget_tree,
         "The line's bugdet item must belong to the budget structure "
         "defined in the budget",
         ['budget_item_id'])
    ]

    def init(self, cr):
        def migrate_period(period_column, date_column):
            sql = ("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'budget_line' "
                   "AND column_name = %s")
            cr.execute(sql, (period_column, ))
            if not cr.fetchall():
                return

            sql = ("UPDATE budget_line "
                   "SET {1} = (SELECT {1} FROM account_period "
                   "           WHERE account_period.id = budget_line.{0}) "
                   ", {0} = NULL "
                   "WHERE {1} IS NULL "
                   "AND {0} IS NOT NULL"
                   ).format(period_column, date_column)
            cr.execute(sql)

        migrate_period('period_id', 'date_start')
        migrate_period('to_period_id', 'date_stop')

    def onchange_analytic_account_id(self, cr, uid, ids, analytic_account_id,
                                     context=None):
        values = {}
        if analytic_account_id:
            aa_obj = self.pool.get('account.analytic.account')
            account = aa_obj.browse(cr, uid, analytic_account_id,
                                    context=context)
            values['currency_id'] = account.currency_id.id
        return {'value': values}

    def _sum_columns(self, cr, uid, res, orderby, context=None):
        """ Compute sum of columns showed by the group by

        :param res: standard group by result
        :param orderby: order by string sent by webclient
        :returns: updated dict with missing sums of int and float

        """
        # We want to sum float and int only
        cols_to_sum = self._get_applicable_cols()
        r_ids = self.search(cr, uid, res['__domain'], context=context)
        lines = self.read(cr, uid, r_ids, cols_to_sum, context=context)
        if lines:
            # Summing list of dict For details:
            # http://stackoverflow.com/questions/974678/
            # faster implementation as mine even if less readable
            tmp_res = dict((key, sum(imap(itemgetter(key), lines)))
                           for key in cols_to_sum)
            res.update(tmp_res)
        return res

    def _get_applicable_cols(self):
        """ Get function columns of numeric types """
        col_to_return = []
        for col, val in self._columns.iteritems():
            if (isinstance(val, fields.function) and
                    val._type in ('float', 'integer')):
                col_to_return.append(col)
        return col_to_return

    def read_group(self, cr, uid, domain, fields, groupby, offset=0,
                   limit=None, context=None, orderby=False, lazy=True):
        """ Override in order to see useful values in group by allocation.

        Compute all numerical values.

        """
        res = super(budget_line, self).read_group(
            cr, uid, domain, fields, groupby,
            offset, limit, context, orderby, lazy
        )

        for result in res:
            self._sum_columns(cr, uid, result, orderby, context=context)
        # order_by looks like
        # 'col1 DESC, col2 DESC, col3 DESC'
        #  Naive implementation we decide of the order using the first DESC ASC
        if orderby:
            order = [x.split(' ') for x in orderby.split(',')]
            reverse = False
            if order and len(order[0]) > 1:
                reverse = (order[0][1] == 'DESC')
            getter = [x[0] for x in order if x[0]]
            if getter:
                res = sorted(res, key=itemgetter(*getter), reverse=reverse)
        return res
