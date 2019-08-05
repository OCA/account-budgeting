# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Budget Management',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Ecosoft,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-budgeting',
    'depends': [
        'mis_builder_budget',
        'web_widget_x2many_2d_matrix',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/budget_management_view.xml',
        'views/budget_plan_view.xml',
    ],
    'installable': True,
    'maintainers': ['kittiu'],
    'development_status': 'Beta',
}
