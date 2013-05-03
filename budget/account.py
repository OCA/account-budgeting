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
from osv import fields, osv
from copy import copy


class account_account(osv.osv):
    """add new methods to the base account_account object """

    _inherit = "account.account"

    
    def get_children_map(self, cr, uid, company_id, context=None, sql_filter=""):
        if context is None: context = {}
        children_ids =  {}
        account_obj = self.pool.get('account.account')
        domain = [('company_id','=',company_id)]
        # Get all the accounts in the company
        acc_ids =  account_obj.search(cr, uid, domain, context=context)

        # For each account, get the child accounts
        for acc in acc_ids:
            child_ids = account_obj.search(cr, uid, [('parent_id','child_of',acc)], context=context)
            children_ids[acc] = [child_id for child_id in child_ids if child_id != acc]

        return children_ids
        
    
    def get_children_flat_list(self, cr, uid, ids, company_id, context=None):
        """return a flat list of all accounts'ids above the 
        ones given in the account structure (included the one given in params)"""
        if context is None: context = {}
        result= [] 
        
        children_map = self.get_children_map(cr, uid, company_id, context)
        
        #init the children array
        children = ids
        
        #while there is children, go deep in the structure
        while len(children) > 0:
            result += children
            
            #go deeper in the structure
            parents = copy(children)
            children = []
            for p in parents:
                if p in children_map:
                    children += children_map[p]
                
        #it may looks stupid tu do a search on ids to get ids... 
        #But it's not! It allows to apply access rules and rights on the accounts to not return protected results
        return self.search(cr, uid, [('id', 'in', result)], context=context)
    
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=80):
        """raise the limit of the search if there is a limit define in the context"""
        if context is None: context = {}
        current_limit = limit
        #if context : just in case context is None
        if context and 'limit' in context:
            current_limit = context['limit']
        return super(account_account, self).name_search(cr, user, name, args, operator, context, current_limit)    
    
    
account_account()        
        
        
    
class account_period(osv.osv):
    """ add new methods to the account_period base object """
    
    _name = 'account.period'
    _inherit = 'account.period'
    
    
    def search(self, cr, user, args, offset=0, limit=None, order=None, \
        context=None, count=False):
        """ special search. If we search a period from the budget version
         form (in the budget lines)  then the choice is reduce 
         to periods that overlap the budget dates"""
        if context is None: context = {}
        result = [] 
           
        parent_result = super(account_period, self).search(cr, user, args, offset, limit, order, context, count)

        #special search limited to a version
        if context.get('version_id'):
            
            #get version's periods
            version_obj = self.pool.get('c2c_budget.version')
            version = version_obj.browse(
                                            cr, 
                                            user, 
                                            context['version_id'], 
                                            context=context
                                        )

            allowed_periods = version_obj.get_periods(
                                                        cr, 
                                                        user, 
                                                        version, 
                                                        context
                                                    )
            allowed_periods_ids = [p.id for p in allowed_periods]
                                  
            #match version's period with parent search result  
            periods = self.browse(
                                    cr, 
                                    user, 
                                    parent_result, 
                                    context
                                )
            for p in periods:
                if p.id in allowed_periods_ids:
                    result.append(p.id)
                    
        #normal search
        else: 
            result = parent_result
                
        return result
    
    
account_period()

