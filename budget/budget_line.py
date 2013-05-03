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
# XXX remove c2c_helper
from c2c_reporting_tools.c2c_helper import *


class c2c_budget_line(orm.Model):
    """ Budget line.

    A budget version line NOT linked to an analytic account """

    def filter_by_period(self, cr, uid, lines, period_ids, context=None):
        """ return a list of lines amoungs those given in parameter that
        are linked to one of the given periods """
        if not period_ids:
            return []
        return [line for line in lines
                if line.period_id.id in period_ids]

    def filter_by_date(self, cr, uid, lines, date_start=None,
                       date_end=None, context=None):
        """return a list of lines among those given in parameter
           that stand between date_start and date_end """
        return [line for line in lines
                if (date_start is None or line.period_id.date_start >= date_start)
                   and (date_end is None or line.period_id.date_stop <= date_end)]

    def filter_by_missing_analytic_account(self, cr, uid, lines, context=None):
        """return a list of lines among those given in parameter that are ot
        linked to a analytic account """
        return [line for line in lines if not line.analytic_account_id]

    def filter_by_items(self, cr, uid, lines, items_ids, context=None):
        """return a list of lines among those given in parameter
        that are linked to one of the given items """
        budget_items_obj = self.pool.get('c2c_budget.item')
        all_items = budget_items_obj.get_sub_items(cr, items_ids)
        return [line for line in lines
                if line.budget_item_id.id in all_items]

    def filter_by_analytic_account(self, cr, uid, lines,
                                   analytic_accounts_ids, context=None):
        """return a list of lines among those given in parameter
        that is linked to analytic_accounts.
        param analytic_accounts_ids should be a list of accounts'ids. """
        if context is None:
            context = {}
        result = []
        aa_obj = self.pool.get('account.analytic.account')
        all_accounts = aa_obj.get_children_flat_list(cr, uid,
                                                     analytic_accounts_ids)
        return [line for line in lines
                if line.analytic_account_id in all_accounts]

    def get_analytic_accounts(self, cr, uid, lines,
                              company_id, context=None):
        """ from a bunch of lines, return all analytic accounts
        ids linked by those lines. """
        return list(set(line.analytic_account_id.id for line in lines
                        if lines.analytic_account_id))

    # XXX returns browse instances, should be private to XML/RPC
    def get_versions(self, cr, uid, lines, context={}):
        """  from a bunch of lines, return all budgets'
        versions those lines belong to """
        return list(set(line.budget_version_id for line in lines
                        if lines.budget_version_id))

    # XXX returns browse instances, should be private to XML/RPC
    def get_periods(self, cr, uid, ids, context=None):
        """return periods informations used by this budget lines.
        (the periods are selected in the budget lines)"""
        lines = self.browse(cr, uid, ids, context=context)
        periods = set(line.period_id for line in lines)
        return sorted(periods, key=attrgetter('date_start'))

    def _get_budget_currency_amount(self, cr, uid, ids, name, arg, context=None):
        """ return the line's amount xchanged in the budget's currency """
        res = {}
        # We get all values from DB
        objs = self.browse(cr, uid, ids, context=context)
        for obj in objs:
            budget_currency_id = obj.budget_version_id.currency_id.id
            res[obj.id] = c2c_helper.exchange_currency(cr,
                                                       obj.amount,
                                                       obj.currency_id.id,
                                                       budget_currency_id)
        return res

    def _get_budget_version_currency(self, cr, uid, context=None):
        """ return the default currency for this line of account.
        The default currency is the currency set for the budget
        version if it exists """
        if context is None:
            context = {}
        # if the budget currency is already set
        if context.get('currency_id'):
            return context['currency_id']
        return False

    _name = "c2c_budget.line"
    _description = "Budget Lines"

    _order = 'name ASC'

    _columns = {
        'period_id': fields.many2one('account.period',
                                     string='Period',
                                     required=True),
        'analytic_account_id': fields.many2one('account.analytic.account',
                                               string='Analytic Account'),
        'budget_item_id': fields.many2one('c2c_budget.item',
                                          'Budget Item',
                                          required=True),
        'name': fields.char('Description'),
        'amount': fields.float('Amount', required=True),
        'currency_id': fields.many2one('res.currency',
                                       'Currency',
                                       required=True),
        'amount_in_budget_currency': fields.function(
            _get_budget_currency_amount,
            type='float',
            string="In Budget's Currency"),
        'budget_version_id': fields.many2one('c2c_budget.version',
                                             'Budget Version',
                                             required=True),
    }

    _defaults = {
        'currency_id': lambda self, cr, uid, context: self._get_budget_version_currency(cr, uid, context)
    }

    def _check_item_in_budget_tree(self, cr, uid, ids, context=None):
        """ check if the line's budget item is in the budget's structure """
        lines = self.browse(cr, uid, ids, context=context)
        budget_item_obj = self.pool.get('c2c_budget.item')
        for line in lines:
            item_id = line.budget_version_id.budget_id.budget_item_id.id
            # get list of budget items for this budget
            flat_items_ids = budget_item_obj.get_sub_items(cr, [item_id])
            if line.budget_item_id.id not in flat_items_ids:
                return False
        return True

    def _check_period(self, cr, uid, ids, context=None):
        """ check if the line's period overlay the budget's period """
        lines = self.browse(cr, uid, ids, context=context)
        return all(line.period_id.date_start > line.budget_version_id.budget_id.start_date
                   and line.period_id.date_stop > line.budget_version_id.budget_id.start_date
                   and line.period_id.date_start < line.budget_version_id.budget_id.end_date
                   and line.period_id.date_stop < line.budget_version_id.budget_id.end_date
                   for line in lines)

    def search(self, cr, uid, args, offset=0, limit=None,
               order=None, context=None, count=False):
        """search through lines that belongs to accessible versions """
        if context is None:
            context = {}
        line_ids = super(c2c_budget_line, self).search(
            cr, uid, args, offset, limit, order, context, count)
        if not line_ids:
            return line_ids

        # get versions the uid can see, from versions, get periods then
        # filter lines by those periods
        version_obj = self.pool.get('c2c_budget.version')
        versions_ids = version_obj.search(cr, uid, [], context=context)
        versions = version_obj.browse(cr, uid, versions_ids, context=context)

        get_period = version_obj.get_periods
        periods = [get_period(cr, uid, version, context=context)
                   for version in versions]
        lines = self.browse(cr, uid, line_ids, context=context)
        lines = self.filter_by_period(cr, uid, lines, [p.id for p in periods], context)
        return [l.id for l in lines]

    _constraints = [
        (_check_period,
         "The line's period must overlap the budget's start or end dates",
         ['period_id']),
        (_check_item_in_budget_tree,
         "The line's bugdet item must belong to the budget structure "
         "defined in the budget",
         ['budget_item_id'])
    ]
