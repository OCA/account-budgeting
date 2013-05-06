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
import copy
from operator import itemgetter
from openerp.osv import fields, orm, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from tools.safe_eval import safe_eval
from openerp.tools.translate import _


class budget_item(orm.Model):
    """ Budget Item

    This is a link between budgets and financial accounts. """
    _name = "budget.item"
    _description = "Budget items"
    _order = 'sequence ASC, name ASC'

    _columns = {
        'code': fields.char('Code', required=True),
        'name': fields.char('Name', required=True),
        'active': fields.boolean('Active'),
        'parent_id': fields.many2one('budget.item',
                                     string='Parent Item',
                                     ondelete='cascade'),
        'children_ids': fields.one2many('budget.item',
                                        'parent_id',
                                        string='Children Items'),
        'account': fields.many2many('account.account',
                                    string='Financial Account'),
        'note': fields.text('Notes'),
        'calculation': fields.text('Calculation'),
        'type': fields.selection([('view', 'View'),
                                  ('normal', 'Normal')],
                                 string='Type',
                                 required=True),
        'sequence': fields.integer('Sequence'),
        'style': fields.selection([('normal', 'Normal'),
                                   ('bold', 'Bold'),
                                   ('invisible', 'Invisible')],
                                  string='Style',
                                  required=True),
    }

    _defaults = {
        'active': True,
        'type': 'normal',
        'style': 'normal',
    }

    def get_real_values_from_analytic_accounts(self, cr, uid, item_id, periods,
                                               lines, company_id, currency_id,
                                               change_date, context=None):
        """return the sum of analytic move lines for this item (and all
        subitems)"""
        if context is None:
            context = {}

        # filter the budget lines to work on
        budget_line_obj = self.pool.get('budget.line')
        budget_lines = budget_line_obj.filter_by_items(cr, uid,
                                                       lines,
                                                       [item_id],
                                                       context=context)

        # get the list of Analytic accounts related to those lines
        aa_ids = budget_line_obj.get_analytic_accounts(cr, uid,
                                                       budget_lines,
                                                       company_id,
                                                       context=context)

        # get accounts (and subaccounts) related to the given item (and
        # subitems)
        general_accounts_ids = self.get_accounts(cr, uid,
                                                 [item_id], company_id,
                                                 context=context)

        # get dates limits
        start_date = None
        end_date = None
        for period in periods:
            if start_date is None or start_date > period.date_start:
                start_date = period.date_start
            if end_date is None or end_date < period.date_stop:
                end_date = period.date_stop

        #we have all informations to look for Analytic Accounts' lines
        aa_lines_obj = self.pool.get('account.analytic.line')
        aa_lines_ids = aa_lines_obj.search(
            cr,
            uid,
            [('date', '>=', start_date),
             ('date', '<=', end_date),
             ('general_account_id', 'in', general_accounts_ids),
             ('account_id', 'in', aa_ids)],
            context=context)
        aa_lines = aa_lines_obj.browse(cr, uid, aa_lines_ids, context=context)
        # now we have the lines, let's add them
        result = 0
        currency_obj = self.pool.get('res.currency')
        ctx = context.copy()
        ctx['date'] = change_date.strptime(DEFAULT_SERVER_DATE_FORMAT)
        for line in aa_lines:
            from_ccy_id = line.general_account_id.company_id.currency_id.id
            result += currency_obj.compute(cr, uid,
                                           from_ccy_id,
                                           currency_id,
                                           line.amount,
                                           context=ctx)
        return result

    def get_real_values(self, cr, uid, item, periods, company_id,
                        currency_id, change_date, context=None):
        """return the sum of the account move lines for this item """
        if context is None:
            context = {}
        result = 0.
        currency_obj = self.pool.get('res.currency')
        move_line_obj = self.pool.get('account.move.line')
        # get the list of accounts and subaccounts linked to this item
        accounts = self.get_accounts(cr, uid,  [item.id], company_id, context)
        # get all move_lines linked to this item
        move_line_ids = move_line_obj.search(
            cr, uid,
            [('period_id', 'in', [p.id for p in periods]),
             ('account_id', 'in', accounts)],
            context=context)
        move_lines = move_line_obj.browse(cr, uid, move_line_ids,
                                          context=context)
        # sum all lines
        for line in move_lines:
            line_currency_id = line.company_id.currency_id.id

            if line.debit != 0:
                amount = line.debit
                sign = -1
            else:
                amount = line.credit
                sign = 1

            ctx = context.copy()
            ctx['date'] = change_date.strptime(DEFAULT_SERVER_DATE_FORMAT)
            result += sign * currency_obj.compute(cr, uid,
                                                  line_currency_id,
                                                  currency_id,
                                                  amount,
                                                  context=ctx)
        return result

    def get_sub_items(self, cr, item_ids):
        """ return a flat list of ids of all items under
        items in the tree structure """
        parents_ids = item_ids

        items_ids = copy.copy(parents_ids)

        loop_counter = 0

        # for each "level" of parent
        while len(parents_ids) > 0:
            # get all the sub items of this level
            # XXX fix the sql injection
            query = """SELECT id
                       FROM budget_item
                       WHERE parent_id IN ( %s )
                       AND active """ % ','.join(map(str, parents_ids))
            cr.execute(query)
            children_ids = map(lambda x: x[0], cr.fetchall())
            items_ids += children_ids

            # continue with next level
            parents_ids = copy.copy(children_ids)

            # count the loops to avoid infinite loops
            loop_counter += 1
            if (loop_counter > 100):
                raise osv.except_osv(
                    _('Recursion Error'),
                    _("It seems the item structure is recursive.\n"
                      "Please check and correct it before to run this "
                      "action again"))
        return list(set(item_ids))

    def get_accounts(self, cr, uid,  item_ids, company_id, context=None):
        """return a list of accounts ids and their sub accounts
        linked to items (item_ids) and their subitems """
        if context is None:
            context = {}

        sub_items_ids = self.get_sub_items(cr, item_ids)
        sub_items = self.browse(cr, uid, sub_items_ids, context=context)
        # gather all account linked to all subitems
        ids = []
        for subitem in sub_items:
            ids += [a.id for a in subitem.account]

        #get the list of sub accounts of gathered accounts
        account_obj = self.pool.get('account.account')
        account_flat_list = account_obj.get_children_flat_list(cr, uid, ids,
                                                               company_id,
                                                               context=context)
        #here is the list of all accounts and subaccounts linked to
        #items and subitems
        return account_flat_list

    def compute_view_items(self, items, items_values):
        """ compute items (type "view") values that are based on calculations
            return the items_values param where computed values
            are added (or replaced)
            items is a list of items objects
            items_values is a dictionnary item_id => item_value
        """
        # prepare the dictionnary of values for formula remplacement.
        # put in it normal items' values and view items' values that do
        # not have formula
        value_dict = {}
        for item in items:
            if not(item.code and item.code.strip()):
                continue
            if not (item.type == 'normal'
                    or (item.type == 'view'
                        and item.calculation
                        and item.calculation.strip())):
                continue
            value_dict[item.code] = items_values[item.id]

        # TODO: check why this method is done so, weirdness sensors
        # actived

        # this loop allow to use view items' results in formulas.
        # count the number of errors that append. Loop until
        # the number remain constant (=error in formulas)
        # or reach 0 (=nothing more to compute)
        previous_error_counter = 0
        while True:
            error_counter = 0

            # look throught the items if there is formula to compute?
            for i in items:
                # if this item is a view, we must maybe
                # replace its value by a calculation (if not already done)
                if i.type != 'view':
                    continue
                if not (i.calculation and i.calculation.strip()):
                    continue
                if not i.code or i.code in value_dict:
                    continue
                formula_ok = True
                scope = {'result': 0}
                # replace keys by values in formula
                try:
                    formula = i.calculation % value_dict
                except Exception:
                    formula_ok = False
                    error_counter += 1
                # try to run the formula
                if formula_ok:
                    try:
                        safe_eval(formula, scope, mode='exec', nocopy=True)
                    except Exception:
                        formula_ok = False
                        error_counter += 1
                # retrieve formula result
                if formula_ok:
                    items_values[i.id] = value_dict[i.code] = scope['result']
                else:
                    items_values[i.id] = 'error'

            # the number of errors in this loop equal to the previous loop.
            # No chance to get better... let's exit the "while true" loop
            if error_counter == previous_error_counter:
                break
            else:
                previous_error_counter = error_counter

        return items_values

    def get_sorted_list(self, cr, uid, root_id, context=None):
        """return a list of items sorted by sequence to be used in reports
           Data are returned in a list
           (value=dictionnary(keys='id','code',
           'name','level', sequence, type, style))
        """
        flat_tree = sorted(self.get_flat_tree(cr, uid, root_id),
                           key=itemgetter('sequence'))
        item_ids = [item['id'] for item in flat_tree]
        return self.browse(cr, uid, item_ids, context=context)

    def get_flat_tree(self, cr, uid, root_id, level=0):
        """ return informations about a buget items tree strcuture.

        Data are returned in a list
        (value=dictionnary(keys='id','code','name','level', sequence, type, style))
        Data are sorted as in the pre-order walk
        algorithm in order to allow to display easily the tree in rapports

        example::

            root
            |_node 1
                |_sub node 1
            |_node 2
            |_ ...

        Do not specify the level param when you call this method,
        it is used for recursive calls
        """
        result = []
        # this method is recursive so for the first call,
        # we must init result with the root node
        if (level == 0):
            # XXX fix sql injectoin
            query = """SELECT id, code, name, sequence, type, style, %s as level
                       FROM budget_item
                       WHERE id = %s """ % (level, str(root_id))

            cr.execute(query)
            result.append(cr.dictfetchall()[0])
            level += 1

        #get children's data
        # XXX fix sql injectoin
        query = """SELECT id, code, name, sequence, type, style, %s as level
                   FROM budget_item
                   WHERE parent_id = %s
                   AND active
                   ORDER BY sequence """ % (level, str(root_id))
        cr.execute(query)
        query_result = cr.dictfetchall()

        for child in query_result:
            result.append(child)
            # recursive call to append the children right after the item
            result += self.get_flat_tree(cr, uid, child['id'], level + 1)

        #check to avoid inifite loop
        if (level > 100):
            raise osv.except_osv(_('Recursion Error'),
                                 _("It seems the budget items structure "
                                   "is recursive (or too deep). "
                                   "Please check and correct it "
                                   "before to run this action again"))

        return result

    def _check_recursion(self, cr, uid, ids, context=None, parent=None):
        """ use in _constraints[]: return false
        if there is a recursion in the budget items structure """
        #use the parent check_recursion function defined in orm.py
        return super(budget_item, self)._check_recursion(
            cr, uid, ids, parent=parent or 'parent_id', context=context)

    _constraints = [
        (_check_recursion,
         'Error ! You can not create recursive budget items structure.',
         ['parent_id'])
    ]

    def name_search(self, cr, uid, name, args=None,
                    operator='ilike', context=None, limit=100):
        """search not only for a matching names but also
        for a matching codes """
        if args is None:
            args = []
        ids = self.search(cr, uid,
                          ['|',
                           ('name', operator, name),
                           ('code', operator, name)] + args,
                          limit=limit,
                          context=context)
        return self.name_get(cr, uid, ids, context=context)

    def search(self, cr, uid, args, offset=0,
               limit=None, order=None, context=None, count=False):
        """ special search. If we search an item from the budget
        version form (in the budget lines)
        then the choice is reduce to periods
        that overlap the budget dates"""
        if context is None:
            context = {}
        result = []
        parent_result = super(budget_item, self).search(
            cr, uid, args, offset, limit, order, context, count)
        if context.get('budget_id'):
            budget_obj = self.pool.get('budget.budget')
            budget = budget_obj.browse(cr, uid,
                                       context['budget_id'],
                                       context=context)
            allowed_items = self.get_sub_items(cr, [budget.budget_item_id.id])
            result.extend([item for item in parent_result
                           if item in allowed_items])
        # normal search
        else:
            result = parent_result
        return result
