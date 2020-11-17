# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Budget Control on Expense",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-budgeting",
    "depends": [
        "budget_control",
        "hr_expense",
        "analytic_tag_dimension",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/budget_period_view.xml",
        "views/hr_expense_view.xml",
        "views/budget_move_forward_view.xml",
    ],
    "installable": True,
    "maintainers": ["kittiu"],
    "development_status": "Beta",
}
