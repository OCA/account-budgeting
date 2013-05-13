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
from datetime import datetime
from operator import attrgetter
from openerp.osv import fields, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.addons import decimal_precision as dp


class budget_line(orm.Model):
    """ Budget line.

    A budget version line NOT linked to an analytic account """

    _name = "budget.line"
    _description = "Budget Lines"

    _order = 'name ASC'

    def _get_budget_currency_amount(self, cr, uid, ids, name, arg, context=None):
        """ return the line's amount xchanged in the budget's currency """
        res = {}
        currency_obj = self.pool.get('res.currency')
        # We get all values from DB
        for line in self.browse(cr, uid, ids, context=context):
            budget_currency_id = line.budget_version_id.currency_id.id
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
            anl_currency_id = anl_account.currency_id.id
            amount = currency_obj.compute(cr, uid,
                                          line_currency_id,
                                          anl_currency_id,
                                          line.amount,
                                          context=context)

            # real amount is the total of analytic lines
            # within the periods, we'll read it in the
            # analytic account's currency, as for the
            # the budget line so we can compare them
            anl_line_ids = anl_lines_obj.search(
                cr, uid,
                [('account_id', '=', anl_account.id),
                 ('date', '>=', line.period_id.date_start),
                 ('date', '<=', line.to_period_id.date_stop)],
                context=context)
            anl_lines = anl_lines_obj.read(
                cr, uid, anl_line_ids, ['aa_amount_currency'], context=context)
            real = sum([l['aa_amount_currency'] for l in anl_lines])
            res[line.id] = {
                'analytic_amount': amount,
                'analytic_real_amount': real,
                'analytic_diff_amount': amount - real,
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

    _columns = {
        'period_id': fields.many2one('account.period',
                                     string='Start Period',
                                     required=True),
        'to_period_id': fields.many2one('account.period',
                                        string='End Period',
                                        required=True),
        'analytic_account_id': fields.many2one('account.analytic.account',
                                               string='Analytic Account'),
        'budget_item_id': fields.many2one('budget.item',
                                          'Budget Item',
                                          required=True,
                                          ondelete='restrict'),
        'name': fields.char('Description'),
        'amount': fields.float('Amount', required=True),
        'currency_id': fields.many2one('res.currency',
                                       'Currency',
                                       required=True),
        'budget_amount': fields.function(
            _get_budget_currency_amount,
            type='float',
            precision=dp.get_precision('Account'),
            string="In Budget's Currency"),
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
        ),
        'analytic_real_amount': fields.function(
            _get_analytic_amount,
            type='float',
            precision=dp.get_precision('Account'),
            multi='analytic',
            string="Analytic Real Amount",
        ),
        'analytic_diff_amount': fields.function(
            _get_analytic_amount,
            type='float',
            precision=dp.get_precision('Account'),
            multi='analytic',
            string="Analytic Real Amount",
        ),
    }

    _defaults = {
        'currency_id': lambda self, cr, uid, context: self._get_budget_version_currency(cr, uid, context)
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

    def _check_period_budget(self, cr, uid, ids, context=None):
        """ check if the line's period overlay the budget's period """
        def period_valid(period, budget):
            return (period.date_start > budget.start_date
                    and period.date_stop > budget.start_date
                    and period.date_start < budget.end_date
                    and period.date_stop < budget.end_date)
        lines = self.browse(cr, uid, ids, context=context)
        return all(period_valid(line.period_id, line.budget_version_id.budget_id)
                   and period_valid(line.to_period_id, line.budget_version_id.budget_id)
                   for line in lines)

    def _check_periods(self, cr, uid, ids, context=None):
        def periods_valid(period, to_period):
            return (period.date_start <= to_period.date_start
                    and period.date_stop <= to_period.date_stop)
        lines = self.browse(cr, uid, ids, context=context)
        return all(periods_valid(line.period_id, line.to_period_id)
                   for line in lines)

    def _check_start_end_dates(self, cr, uid, ids):
        """ check the start date is before the end date """
        lines = self.browse(cr, uid, ids)
        for l in lines:
            if l.end_date < l.start_date:
                return False
        return True

    _constraints = [
        (_check_period_budget,
         "The line's period must overlap the budget's start or end dates",
         ['period_id', 'to_period_id']),
        (_check_periods,
         "The end period must begin after the start period.",
         ['period_id', 'to_period_id']),
        (_check_item_in_budget_tree,
         "The line's bugdet item must belong to the budget structure "
         "defined in the budget",
         ['budget_item_id'])
    ]

    def init(self, cr):
        sql = ("UPDATE budget_line SET to_period_id = period_id "
               "WHERE to_period_id ISNULL")
        cr.execute(sql)

    def on_change_period_id(self, cr, uid, ids, period_id, to_period_id, context=None):
        if not to_period_id:
            return {'value': {'to_period_id': period_id}}
        else:
            return {}

    def _filter_by_period(self, cr, uid, lines, period_ids, context=None):
        """ return a list of lines amoungs those given in parameter that
        are linked to one of the given periods """
        if not period_ids:
            return []
        return [line for line in lines
                if line.period_id.id in period_ids]

    def _filter_by_date(self, cr, uid, lines, date_start=None,
                       date_end=None, context=None):
        """return a list of lines among those given in parameter
           that stand between date_start and date_end """
        return [line for line in lines
                if (date_start is None or line.period_id.date_start >= date_start)
                   and (date_end is None or line.period_id.date_stop <= date_end)]

    def _filter_by_missing_analytic_account(self, cr, uid, lines, context=None):
        """return a list of lines among those given in parameter that are ot
        linked to a analytic account """
        return [line for line in lines if not line.analytic_account_id]

    def _filter_by_items(self, cr, uid, lines, items_ids, context=None):
        """return a list of lines among those given in parameter
        that are linked to one of the given items """
        budget_items_obj = self.pool.get('budget.item')
        all_items = budget_items_obj.get_sub_item_ids(cr, uid,
                                                      items_ids,
                                                      context=context)
        return [line for line in lines
                if line.budget_item_id.id in all_items]

    def _filter_by_analytic_account(self, cr, uid, lines,
                                   analytic_accounts_ids, context=None):
        """return a list of lines among those given in parameter
        that is linked to analytic_accounts.
        param analytic_accounts_ids should be a list of accounts'ids. """
        result = []
        aa_obj = self.pool.get('account.analytic.account')
        tree_account_ids = aa_obj.search(
            cr, uid,
            [('id', 'child_of', analytic_accounts_ids)],
            context=context)
        return [line for line in lines
                if line.analytic_account_id in tree_account_ids]

    def get_analytic_account_ids(self, cr, uid, lines, context=None):
        """ from a bunch of lines, return all analytic accounts
        ids linked by those lines. """
        return list(set(line.analytic_account_id.id for line in lines
                        if lines.analytic_account_id))

    def _get_versions(self, cr, uid, lines, context=None):
        """  from a bunch of lines, return all budgets'
        versions those lines belong to """
        return list(set(line.budget_version_id for line in lines
                        if lines.budget_version_id))

    def _get_periods(self, cr, uid, ids, context=None):
        """return periods informations used by this budget lines.
        (the periods are selected in the budget lines)"""
        lines = self.browse(cr, uid, ids, context=context)
        periods = set(line.period_id for line in lines)
        return sorted(periods, key=attrgetter('date_start'))

    def search(self, cr, uid, args, offset=0, limit=None,
               order=None, context=None, count=False):
        """search through lines that belongs to accessible versions """
        if context is None:
            context = {}
        line_ids = super(budget_line, self).search(
            cr, uid, args, offset, limit, order, context, count)
        if not line_ids:
            return line_ids

        # get versions the uid can see, from versions, get periods then
        # filter lines by those periods
        version_obj = self.pool.get('budget.version')
        versions_ids = version_obj.search(cr, uid, [], context=context)
        versions = version_obj.browse(cr, uid, versions_ids, context=context)

        get_periods = version_obj._get_periods
        periods = []
        for version in versions:
            periods += get_periods(cr, uid, version, context=context)
        lines = self.browse(cr, uid, line_ids, context=context)
        lines = self._filter_by_period(cr, uid, lines,
                                       [p.id for p in periods], context=context)
        return [l.id for l in lines]
