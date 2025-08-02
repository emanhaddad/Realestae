# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Rental/Sign Bridge",
    "summary": """
            Bridge Sign functionalities with the Rental application
        """,
    "author": "Odoo S.A.",
    "website": "https://www.odoo.com",
    "category": "Sales/Sales",
    "version": "18.0",
    "depends": ["sign", "real_estate_maintenance"],
    "data": [
        "security/ir.model.access.csv",
        "security/rental_sign_security.xml",
        "wizard/contract_sign_views.xml",
        "data/mail_templates.xml",
        "views/res_config_settings_views.xml",
        "views/real_estate_contract.xml",
    ],
    "demo": [
        "data/demo.xml",
    ],
    "auto_install": False,
}
