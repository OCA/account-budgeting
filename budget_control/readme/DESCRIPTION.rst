This module is the main module from a set of budget control modules.
This module alone will allow you to work in full cycle of budget control process.
Other modules, each one are the small enhancement of this module, to fullfill
additional needs. Having said that, following will describe the full cycle of budget
control already provided by this module,

**Notes:**

Mis Buidler (mis_builder_budget) is used as the core engine to calculate the budgeting
figure. The budget_control modules are aimed to ease the use of budgeting in organization.

In order to understand how this module works, you should first understand
budgeting concept of mis_builder_budget.


Budget Control Core Features:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Budget Commitment (base.budget.move)**

  Probably the most crucial part of budget_control.

  * Budget Balance = Budget Allocated - (Budget Actuals - Budget Commitments)

  Actual amount are from `account.move.line` from posted invoice. Commitments can be sales/purchase,
  expense, purchase request, etc. Document required to be budget commitment can extend base.budget.move.
  For example, the module budget_control_expense will create budget commitment `expense.budget.move`
  for approved expense. These budget commitments will be used as alternate data source on mis_builder_budget.
  Note that, in this budget_control module, there is no extension for budget commitment yet.

* **Budget Period (budget.period)**

  Budget Period is the first thing to do for new budget year, and is used to govern how budget will be
  controlled over the defined date range, i.e.,

  * Duration of budget year
  * KPI to control (mis.report.instance)
  * Document to do budget checking
  * Analytic account in controlled
  * Control Level

  Although not mandatory, an organization will most likely use fiscal year as budget period.
  In such case, there will be 1 budget period per fiscal year, and multiple budget control sheet (one per analytic).

* **Budget Control Sheet (budget.control)**

  Each analytic account can have one budget control sheet per budget period.
  The budget control is used to allocate budget amount in a simpler way.
  In the backend it simply create mis.budget.item, nothing too fancy.
  Once we have budget allocations, the system is ready to perform budget check.

* **Budget Checking**

  By calling function -- check_budget(), system will check whether the confirmation
  of such document can result in negative budget balance. If so, it throw error message.
  In this module, budget check occur during posting of invoice and journal entry.
  To check budget also on more documents, do install budget_control_xxx relevant to that document.

* **Budget Reports**

  Currently there are 2 types of report.

  1. MIS Builder Reports: inherited from MIS Builder, to shows overall budget condition, overall or by each analytic.
  2. Budget Monitor Report: combine all budget related transactions, and show them in Standard Odoo BI view.

* **Budget Commitment Move Forward**

  In case budget commitment is being used. Sometime user has committed budget withing this year
  but not ready to use it and want to move the commitment amount to next year budget.
  Budget Move Forward can be use to change the budget move's date to the designated year.

Extended Modules:
~~~~~~~~~~~~~~~~~

Following are brief explanation of what the extended module will do.

**Budget Transfer**

This module allow transferring allocated budget from one budget control sheet to other

* budget_control_transfer

**Budget Move extension**

These modules extend base.budget.move for other document budget commitment.

* budget_control_expense
* budget_control_purchase
* budget_control_purchase_request
* budget_control_sale

**Budget Source of Fund**

This module allow create Master Data source of fund.
there is relation between source of fund and budget control sheet
for allocated source of fund from one budget control sheet to many source of fund.
Users can view source of fund monitoring report

* budget_source_fund

**Tier Validation**

Extend base_tier_validation for budget control sheet

* budget_control_tier_validation

**Analytic Tag Dimension Enhancements**

When 1 dimension (analytic account) is not enough,
we can use dimension to create persistent dimension columns

- analytic_tag_dimension
- account_tag_dimension_enhanced

Following modules ensure that, analytic_tag_dimension will work with all new
budget control objects. These are important for reporting purposes.

* budget_control_tag_dimension
* budget_control_expense_tag_dimension
* budget_control_purchase_tag_dimension
