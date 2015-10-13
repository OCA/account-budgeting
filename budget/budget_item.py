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
from openerp.osv import fields, orm


class allocation_type(orm.Model):

    """Allocation type from budget line"""
    _name = "budget.allocation.type"

    _columns = {
        'name': fields.char('Name', required=True),
    }


class budget_item(orm.Model):

    """ Budget Item

    This is a link between budgets and financial accounts. """
    _name = "budget.item"
    _description = "Budget items"
    _order = 'sequence ASC, name ASC'

    def _get_all_account_ids(self, cr, uid, ids, field_name,
                             arg, context=None):
        result = {}
        account_obj = self.pool.get('account.account')
        for item in self.browse(cr, uid, ids, context=context):
            result[item.id] = []
            if not item.account:
                continue
            account_ids = [account.id for account in item.account]
            account_ids = account_obj._get_children_and_consol(
                cr, uid, account_ids, context=context)
            result[item.id] = account_ids
        return result

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
        'allocation_id': fields.many2one('budget.allocation.type',
                                         'Budget Line Allocation Type'),

        'style': fields.selection([('normal', 'Normal'),
                                   ('bold', 'Bold'),
                                   ('invisible', 'Invisible')],
                                  string='Style',
                                  required=True),
        'all_account_ids': fields.function(
            _get_all_account_ids,
            type='many2many',
            relation='account.account',
            string='Accounts and Children Accounts'),
    }

    _defaults = {
        'active': True,
        'type': 'normal',
        'style': 'normal',
    }

    def _check_recursion(self, cr, uid, ids, context=None, parent=None):
        """ use in _constraints[]: return false
        if there is a recursion in the budget items structure """
        # use the parent check_recursion function defined in orm.py
        return super(budget_item, self)._check_recursion(
            cr, uid, ids, parent=parent or 'parent_id', context=context)

    _constraints = [
        (_check_recursion,
         'Error ! You can not create recursive budget items structure.',
         ['parent_id'])
    ]

    def get_sub_item_ids(self, cr, uid, item_ids, context=None):
        """ Returns list of ids of sub items (including the top level
        item id)"""
        tree = self.get_flat_tree(cr, uid, item_ids, context=context)
        return [item['id'] for item in tree]

    def get_sorted_list(self, cr, uid, root_id, context=None):
        """return a list of items sorted by sequence to be used in reports
           Data are returned in a list
           (value=dictionnary(keys='id','code',
           'name','level', sequence, type, style))
        """
        flat_tree = self.get_flat_tree(cr, uid, root_id, context=context)
        flat_tree = sorted(flat_tree, key=itemgetter('sequence'))
        item_ids = [item['id'] for item in flat_tree]
        return self.browse(cr, uid, item_ids, context=context)

    def get_flat_tree(self, cr, uid, root_ids, context=None):
        """ return informations about a buget items tree structure.

        Data are returned in a list of dicts with the items values.
        Data are sorted as in the pre-order walk
        algorithm in order to allow to display easily the tree in reports
        """
        def recurse_tree(node_ids, level=0):
            result = []
            items = self.read(cr, uid,
                              node_ids,
                              ['code', 'name', 'sequence',
                               'type', 'style', 'children_ids'],
                              context=context)
            all_children_ids = []
            for item in items:
                children_ids = item.pop('children_ids')
                if children_ids:
                    all_children_ids += children_ids
                item['level'] = level
            result += items
            if all_children_ids:
                result += recurse_tree(all_children_ids, level + 1)
            return result
        if not hasattr(root_ids, '__iter__'):
            root_ids = [root_ids]
        return recurse_tree(root_ids)

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
        domain = []
        if context.get('budget_id'):
            ctx = context.copy()
            ctx.pop('budget_id')  # avoid recursion for underhand searches
            budget_obj = self.pool.get('budget.budget')
            budget = budget_obj.browse(cr, uid,
                                       context['budget_id'],
                                       context=ctx)
            allowed_item_ids = self.get_sub_item_ids(
                cr, uid,
                [budget.budget_item_id.id],
                context=ctx)

            domain = [('id', 'in', allowed_item_ids)]
        return super(budget_item, self).search(
            cr, uid, args + domain, offset, limit, order, context, count)
