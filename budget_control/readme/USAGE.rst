Before start using this module, following access right must be set.
  - Budget User for Budget Control Sheet, Budget Report
  - Budget Manager for Budget Period

Followings are sample steps to start with,

1. Create new Budget Period

    - Choose KPI template
    - Identify date range, i.e., 1 fiscal year
    - Plan Date Range, i.e., Quarter, the slot to fill allocation in budget control will split by quarter
    - Budget Control - On Account = True

   Note: Upon creation, the MIS Budget (mis.budget) will be created automatically.
   The following steps will create mis.budget.item for it.

2. Create Budget Control Sheet

   To create budget control sheet, you can either create manually one by one or by using the helper,
   Action > Create Budget Control Sheet

    - Choose Analytic budget_control_purchase_tag_dimension
    - Check All Analytic Account, this will list all analytic account in selected groups
    - Uncheck Initial Budget By Commitment, this is used only on following year to
      init budget allocation if they were committed amount carried over.
    - Click "Create Budget Control Sheet", and then view the newly created control sheets.

3. Allocate amount in Budget Control Sheets

   Each analytic account will have its own sheet. Form Budget Period, click on the
   icon "Budget Control Sheets" or by Menu > Budgeting > Budget Control Sheet, to open them.

    - Based on "Plan Date Range" period, Plan table will show all KPI split by Plan Date Range
    - Allocate budget amount as appropriate.
    - Click Control button, state will change to Controlled.

   Note: Make sure the Plan Date Rang period already has date ranges that covers entire budget period.
   Once ready, you can click on "Reset Plan" anytime.

4. Budget Reports

   After some document transaction (i.e., invoice for actuals), you can view report anytime.

    - On both Budget Period and Budget Control sheet, click on Preview/Run/Export for MIS Report
    - Menu Budgeting > Budget Monitoring, to show budget report in standard Odoo BI view.

5. Budget Checking

   As we have checked Budget Control - On Account = True in first step, checking will occur
   every time an invoice is validated. You can test by validate invoice with big amount to exceed.
