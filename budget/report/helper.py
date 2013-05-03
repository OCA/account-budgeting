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
from c2c_reporting_tools.core.table_elements import *


class ItemCell(TextCellData):
    """ special cell for budget structure items. It's a text cell that handle a special style called "bold" """
    
    def __init__(self, item):
        """constructor"""
        super(ItemCell, self).__init__(item.name)
        
        if item.style == 'bold':
            self.font = "Helvetica-Bold"
            self.background_color = "#EEEEEE"


class PercentCell(NumCellData):
    """ special cell for % values. Basically, a NumCell with % next to the number """
    
    def get_raw_content(self, column_data, row_values, col_values):
        """ return the content of the cell without the surrounding Paragraph tags"""
        
        if self.value == 'error':
            return "-" 
        
        num = super(PercentCell, self).get_raw_content(column_data, row_values, col_values)
        return str(num)+" %"

        
class BudgetNumCell(NumCellData):
    """ special cell for budget values.  basically, a NumCell that display "Error!" in case the value is "error". """
    
    def _get_instant_value(self, column_data, row_values, col_values):
        """ return the numerical value of the cell or 0 in case the value is 'error' """
        
        if self.value == 'error':
            return 0
        return self.value
    
    def get_raw_content(self, column_data, row_values, col_values):
        """ return the formated value or 'Error!' in case the value is 'error' """
        if self.value == 'error':
            return "Formula Error!" 
        return super(BudgetNumCell, self).get_raw_content(column_data, row_values, col_values)
