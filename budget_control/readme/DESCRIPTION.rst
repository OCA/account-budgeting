This module is the main module from a set of budget control modules.
This module alone will allow you to work in full cycle of budget control process.
Other modules, each one are the small enhancement of this module, to fullfill
additional needs. Having said that, following will describe the full cycle of budget
control already provided by this module,

Budget Control Core Features:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Budget Commitment (base.budget.move)**

  Probably the most crucial part of budget_control.

  * Budget Balance = Budget Allocated - (Budget Actuals - Budget Commitments)

  Actual amount are from `account.move.line` from posted invoice. Commitments can be sales/purchase,
  expense, purchase request, etc. Document required to be budget commitment can extend base.budget.move.
  For example, the module budget_control_expense will create budget commitment `expense.budget.move`
  for approved expense.
  Note that, in this budget_control module, there is no extension for budget commitment yet.

* **Budget Template (budget.template)**

  A Budget Template in the budget control system serves as a framework for controlling the budget,
  allowing for the budget to be managed according to the pre-defined template.
  The budget template has a relationship with the accounting,
  and is used to control spending based on pre-configured accounts.

* **Budget Period (budget.period)**

  Budget Period is the first thing to do for new budget year, and is used to govern how budget will be
  controlled over the defined date range, i.e.,

  * Duration of budget year
  * Template to control (budget.template)
  * Document to do budget checking
  * Analytic account in controlled
  * Control Level

  Although not mandatory, an organization will most likely use fiscal year as budget period.
  In such case, there will be 1 budget period per fiscal year, and multiple budget control sheet (one per analytic).

* **Budget Control Sheet (budget.control)**

  Each analytic account can have one budget control sheet per budget period.
  The budget control is used to allocate budget amount in a simpler way.
  In the backend it simply create budget.control.line, nothing too fancy.
  Once we have budget allocations, the system is ready to perform budget check.

* **Budget Checking**

  By calling function -- check_budget(), system will check whether the confirmation
  of such document can result in negative budget balance. If so, it throw error message.
  In this module, budget check occur during posting of invoice and journal entry.
  To check budget also on more documents, do install budget_control_xxx relevant to that document.

* **Budget Constraint**

  To make the function -- check_budget() more flexible,
  additional rules or limitations can be added to the budget checking process.
  The system will perform the regular budget check and will also check the additional conditions specified
  in the added rules. An example of using budget constraints can be seen from the budget_allocation module.

* **Budget Reports**

  Currently there are 2 types of report.

  1. Budget Monitoring: combine all budget related transactions, and show them in Standard Odoo BI view.
  2. Actual Budget Moves: combine all actual commit transactions, and show them in Standard Odoo BI view.

* **Budget Commitment Move Forward**

  In case budget commitment is being used. Sometime user has committed budget withing this year
  but not ready to use it and want to move the commitment amount to next year budget.
  Budget Commitment Forward can be use to change the budget move's date to the designated year.

* **Budget Transfer**

  This module allow transferring allocated budget from one budget control sheet to other


Extended Modules:
~~~~~~~~~~~~~~~~~

Following are brief explanation of what the extended module will do.

**Budget Move extension**

These modules extend base.budget.move for other document budget commitment.

* budget_control_expense
* budget_control_purchase
* budget_control_purchase_request
* budget_control_sale

**Budget Allocation**

This module is the main module for manage allocation (source of fund, analytic tag and analytic account)
until set budget control. and allow create Master Data source of fund, analytic tag dimension.
Users can view source of fund monitoring report

* budget_allocation

**Tier Validation**

Extend base_tier_validation for budget control sheet

* budget_control_tier_validation

**Analytic Tag Dimension Enhancements**

When 1 dimension (analytic account) is not enough,
we can use dimension to create persistent dimension columns

- analytic_tag_dimension
- analytic_tag_dimension_enhanced

Following modules ensure that, analytic_tag_dimension will work with all new
budget control objects. These are important for reporting purposes.

* budget_allocation
* budget_allocation_expense
* budget_allocation_purchase
