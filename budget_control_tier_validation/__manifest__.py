# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Budget Control Tier Validation',
    'summary': 'Extends the functionality of Budget Control to '
               'support a tier validation process.',
    'version': '12.0.1.0.0',
    'category': 'Accounting',
    'website': 'https://github.com/OCA/account-budgeting',
    'author': 'Ecosoft, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'depends': [
        'budget_control',
        'base_tier_validation',
    ],
    'data': [
        'views/budget_control_view.xml',
    ],
    'installable': True,
    'maintainers': ['kittiu'],
    'development_status': 'Alpha',
}
