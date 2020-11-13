# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Budget Control",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-budgeting",
    "depends": [
        "account",
        "mis_builder_budget",
        "web_widget_x2many_2d_matrix",
    ],
    "data": [
        "security/budget_control_security_groups.xml",
        "security/budget_control_rules.xml",
        "security/ir.model.access.csv",
        "views/budget_menuitem.xml",
        "views/budget_period_view.xml",
        "views/mis_budget_item.xml",
        "views/budget_control_view.xml",
        "views/account_move_views.xml",
        "views/budget_move_forward_view.xml",
        "wizard/generate_budget_control_view.xml",
        "report/budget_monitor_report_view.xml",
    ],
    "installable": True,
    "maintainers": ["kittiu"],
    "development_status": "Alpha",
}
