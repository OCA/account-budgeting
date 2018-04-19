import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-account-budgeting",
    description="Meta package for oca-account-budgeting Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-budget',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
