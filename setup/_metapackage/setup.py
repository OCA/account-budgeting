import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-account-budgeting",
    description="Meta package for oca-account-budgeting Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-account_budget_oca',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
