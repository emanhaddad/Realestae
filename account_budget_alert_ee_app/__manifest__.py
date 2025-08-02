# -*- coding: utf-8 -*-

{
    'name' : 'Account Budget Limit Alert-Validation Warning',
    'author': "Edge Technologies",
    'version' : '18.0',
    'live_test_url':'https://youtu.be/Q-46v4WzE0M',
    "images":["static/description/main_screenshot.png"],
    'summary' : 'Accounting Budget Limit Alert Budget limit Warning against Purchase budget limit alerts against Bill budget exceed alerts budget limit alert accounting budget validation against purchase budget integration budget warning limit exceed warning on budget',
    'description' : """
            Allow Accounting Budget Limit Alert/Warning on confirm Purchase Order and validate Vendor Bill
    """,
    "license" : "OPL-1",
    'depends' : ['base','purchase','account','stock','account_budget'],
    'data': [
            'views/budget_view.xml',
            ],
    'qweb' : [],
    'demo': [],
    'installable' : True,
    'auto_install' : False,
    'price': 58,
    'category' : 'Accounting',
    'currency': "EUR",
}
