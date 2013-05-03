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


class c2c_budget_report_abstraction(osv.osv):
    """ This object define parts of reports that can be override. 
        It is used to replace analytic_account by projects for some 
        of ours customers """
    
    _name = "c2c_budget.report_abstraction"
    _description = "Report Abstraction"
    _columns = {}
    _defaults = {}
        
        
    def get_project_group_object(self, cr, uid, context=None):
        """ return the object use to group by projects in reports 
            this is an abstraction level use to allow this module 
            to be overridden in order to use project as analytic accounts
        """
        return self.pool.get('account.analytic.account');
        
        
    
c2c_budget_report_abstraction()
