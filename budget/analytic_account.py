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
import pooler
from copy import copy


class analytic_account(osv.osv):
    """ add new methods to the base 
        analytic_account object """

    _inherit = "account.analytic.account"
    
    def get_children_map(self, cr, uid, context=None):
        """ return a dictionnary mapping the parent relation 
            between accounts and their children """
        if context is None: context = {}
        #build a dictionnary {parent_id -> [children_ids]}
        children_ids =  {}
        anal_ids = self.search(cr, uid, [], context)
        anal_accounts = self.browse(cr, uid, anal_ids, context)
        
        for anal_account in anal_accounts: 
            if anal_account.parent_id:
                if anal_account.parent_id.id not in children_ids:
                    children_ids[anal_account.parent_id.id] = []
                children_ids[anal_account.parent_id.id].append(anal_account.id)
            
        
        return children_ids
    
    
    def get_children_flat_list(self, cr, uid, ids, context=None):
        """return a flat list of all accounts'ids above the ones 
        given in the account structure (included the one given in params)"""
        if context is None: context = {}
        result= [] 
        
        children_map = self.get_children_map(cr, uid, context)
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
                
        return result
analytic_account()
