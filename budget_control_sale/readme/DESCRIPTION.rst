This module will create budget commitment for sale (to be used as alternate actual source in mis_builder)

When sales order is confirmed, sale.budget.move is created, and when
customer invoice is confirmed, reversed purchase.budget.move is created.

A new tab "Budget Commitment" is created on purchase order for budget user to keep track of the committed budget.

Please note that, sales commitment means reduced in expenses as opposite to purchase commitment
