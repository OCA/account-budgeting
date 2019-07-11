import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-account-budgeting",
    description="Meta package for oca-account-budgeting Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-account_budget_oca',
        'odoo12-addon-account_budget_template',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
