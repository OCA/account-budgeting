import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-account-budgeting",
    description="Meta package for oca-account-budgeting Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-account_budget_template',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 11.0',
    ]
)
