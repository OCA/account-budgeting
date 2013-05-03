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
import time
import pooler


class c2c_budget_wizard_abstraction(osv.osv):
    """ This object define parts of wizards forms 
    and process that can be override. 
    It is used to replace analytic_account by 
    projects for some of ours customers """
    
    _name = "c2c_budget.wizard_abstraction"
    _description = "Wizard Abstraction"
    _columns = {}
    _defaults = {}
    
    
    def budget_vs_real_get_form(self, cr, uid, data, context=None):
        """ return a piece of form used in the budget_vs_real wizard """

        return """<separator string="Select Analytic Accounts 
        (leave empty to get all accounts in use)" 
        colspan="4"/>    
        <field name="split_by_aa" />
        <newline/> 
        <field name="analytic_accounts" 
            colspan="4" nolabel="1" width="600" height="200"/>
        <newline/> 
        """
               
               
    def budget_vs_real_get_fields(self, cr, uid, data, context=None):
        """ return some fields of form used in the budget_vs_real wizard """
 
        fields = {}
        fields['analytic_accounts'] = {
                                        'string':'Analytic Accounts', 
                                        'type':'many2many', 
                                        'relation':'account.analytic.account'
                                      }        
        fields['split_by_aa'] = {
                                    'string':'Split by Analytic Accounts', 
                                    'type':'boolean'
                                }        
        return fields


    def budget_by_period_get_form(self, cr, uid, data, context=None):
        """ return a piece of form used in the budget_by_period wizard """

        return """<separator string="Select Analytic Accounts 
        (leave empty to get all accounts in use)" colspan="4"/>    
        <field name="split_by_aa" />
        <newline/> 
        <field name="analytic_accounts" 
            colspan="4" nolabel="1" width="600" height="200"/>
        <newline/> 
        """
               
               
    def budget_by_period_get_fields(self, cr, uid, data, context=None):
        """ return some fields of form used in the budget_by_period wizard """
 
        fields = {}
        fields['analytic_accounts'] = {
                                        'string':'Analytic Accounts', 
                                        'type':'many2many', 
                                        'relation':'account.analytic.account'
                                    }        
        fields['split_by_aa'] = {
                                    'string':'Split by Analytic Accounts', 
                                    'type':'boolean'
                                }        
        return fields
    
    
    def advanced_search_get_form(self, cr, uid, data, context=None):
        """ return a piece of form used in the advanced_search """
        
        return """<separator string="Choose Analytic Accounts 
              (leave empty to not filter)" colspan="2"/>
              <separator string="Choose versions (leave empty to not filter)" colspan="2"/>
              <field name="analytic_accounts" nolabel="1" colspan="2" width="400"/>
              <field name="versions" nolabel="1" colspan="2" width="400" height="150"/>
              <field name="empty_aa_too" colspan="2"/>"""
        
        
    def advanced_search_get_fields(self, cr, uid, data, context=None):
        """ return some fields of form used in the advanced_search wizard """
        
        fields = {}
        fields['analytic_accounts'] = {
                                        'string':'Analytic Accounts', 
                                        'type':'many2many', 
                                        'relation':'account.analytic.account'
                                    }
        fields['empty_aa_too'] = {
                                    'string':'Include Lines Without Analytic Account', 
                                    'type':'boolean'
                                }
        fields['versions'] = {
                                'string':'Versions', 
                                'type':'many2many', 
                                'relation':'c2c_budget.version'
                            }
        return fields

    
c2c_budget_wizard_abstraction()
