# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Budget Control Full Cycle Demo',
    'version': '12.0.1.0.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'author': 'Ecosoft,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-budgeting',
    'depends': [
        'budget_control',
        'budget_control_expense',
        'budget_control_purchase',
        'budget_control_purchase_request',
        'budget_control_transfer',
    ],
    'data': [
        'data/date_range.xml',
        'data/mis_report.xml',
        'data/analytic_account.xml',
    ],
    'installable': True,
    'maintainers': ['kittiu'],
    'development_status': 'Alpha',
}
