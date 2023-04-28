# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Budget Control",
    "version": "16.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-budgeting",
    "depends": [
        "account",
        "l10n_generic_coa",
        "date_range",
        "web_widget_x2many_2d_matrix",
    ],
    "data": [
        "data/sequence_data.xml",
        "security/budget_control_security_groups.xml",
        "security/budget_control_rules.xml",
        "security/ir.model.access.csv",
        "wizards/generate_budget_control_view.xml",
        "wizards/analytic_budget_info_view.xml",
        "wizards/analytic_budget_edit_view.xml",
        "wizards/confirm_state_budget_view.xml",
        "wizards/budget_commit_forward_info_view.xml",
        "wizards/budget_balance_forward_info_view.xml",
        "views/account_budget_move.xml",
        "views/budget_menuitem.xml",
        "views/budget_kpi_view.xml",
        "views/budget_template_view.xml",
        "views/res_config_settings_views.xml",
        "views/budget_period_view.xml",
        "views/budget_constraint_view.xml",
        "views/budget_control_view.xml",
        "views/analytic_account_views.xml",
        "views/account_move_views.xml",
        "views/account_journal_view.xml",
        "views/budget_balance_forward_view.xml",
        "views/budget_commit_forward_view.xml",
        "views/budget_transfer_view.xml",
        "views/budget_transfer_item_view.xml",
        "views/budget_move_adjustment_view.xml",
        "report/budget_monitor_report_view.xml",
        "report/budget_move_views.xml",
    ],
    "demo": ["demo/budget_template_demo.xml"],
    "assets": {
        "web.assets_backend": [
            "budget_control/static/src/xml/budget_popover.xml",
        ],
    },
    "installable": True,
    "maintainers": ["kittiu"],
    "post_init_hook": "update_data_hooks",
    "uninstall_hook": "uninstall_hook",
    "development_status": "Alpha",
}
