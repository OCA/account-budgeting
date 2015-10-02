# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Leonardo Pistone
#    Copyright 2014 Camptocamp SA
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
{"name": "Budget CRM",
 "version": "1.0",
 "author": "Camptocamp,Odoo Community Association (OCA)",
 "category": "Generic Modules/Accounting",
 "website": "http://camptocamp.com",
 "description": """
Budget CRM
==========

This module depends on the OCA module "budget", not on the Odoo core
account_budget module.

It provides a link in the drop down menu of the Opportunities to generate
automatically budget lines from them.

The information used to generate the budget lines is found as follows:

* The active Budget Version is the one selected in the Company
* The number of lines to generate comes from the Months field of the
  Opportunity
* The amount of every line is the expected revenue of the Opportunity, divided
  by the number of months
* The first line starts on the 1st of the month after the Expected Date of the
  Opportunity and ends on the last day of the month
* The other lines start end end in the following months
* The name comes from the name of the opportunity, with also the year and
  month.
* The Analytic Account comes from the Lead, where by default it comes from the
  Sales Team
* The Budget Item comes from the Lead, where by default it comes from the
  Stage.
* The Currency comes from the current Budget Version (in the Company)

The generated Budget Lines are linked to the Opportunity and can be seen in
the new Budget tab. They can coexist vith existing budget lines in the same
Version.

The next time the synchronization is run, the budget lines previously linked
to the Opportunity are deleted. Existing lines are not affected.
    """,
 "complexity": "normal",
 "depends": ["budget",
             "crm",
             ],
 "demo": [
     'demo/setup_team.yml',
     'demo/setup_user.yml',
 ],
 "data": [
     'view/lead.xml',
     'view/team.xml',
     'view/stage.xml',
     'view/budget_line.xml',
     'view/company.xml',
     'wizard/crm_to_budget.xml',
 ],
 "test": [
     'test/test_lead_defaults.yml',
     'test/test_crm_to_budget.yml',
     'test/test_update_crm_to_budget.yml',
 ],
 "installable": False,
 }
