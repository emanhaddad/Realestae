

{
    'name': 'Real estate Maintenance',
    'summary': """
        This module extends the Real estate module allowing the Real estate Maintenance.""",
    'version': '18.0',
    'author': 'App Script',
    'depends': [
    'real_estate',
    'account',
    'base',
    'rent_contract_account',
    'maintenance',
    'real_estate_expenses',
    'sign',

    ],
    'data': [
        #Security
            'security/real_estate_maintenance.xml',
            'security/ir.model.access.csv',
        #Views
            'wizard/realestate_booking_cancel.xml',
            'wizard/realestate_payment.xml',
            'data/mail_template.xml',
            'views/res_config_settings.xml',
            'views/real_estate.xml',
            'views/rea_estate_sale.xml',
            'views/real_estate_maintenance.xml',
            'views/real_estate_booking.xml',
            'views/real_estate_deliver.xml',
            'views/real_estate_delegate.xml',
            'views/real_estate_delegate_portal.xml',
            'views/real_estate_customer_status.xml',
            'views/real_estate_report_view.xml',
            'views/real_estate_unit_report_view.xml',
            'views/real_estate_evacuate.xml',
            'views/investor_clearance.xml',
            'views/profits_count.xml',
            'views/real_estate_sale_report_view.xml',
            'views/real_estate_sale_contract_report_view.xml',
            'reports/booking_report_template.xml',
            'reports/booking_report_views.xml',
            'reports/evacuate_report_template.xml',
            'reports/investor_clearance_report_template.xml',
            'reports/delegation_report_template.xml',
            'reports/maintenance_report_template.xml',
        #Data
            'data/real_estate_maintenance.xml',
    ],
}
