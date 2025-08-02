# -*- coding: utf-8 -*-
# from odoo import http


# class HolidayReport(http.Controller):
#     @http.route('/holiday_report/holiday_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/holiday_report/holiday_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('holiday_report.listing', {
#             'root': '/holiday_report/holiday_report',
#             'objects': http.request.env['holiday_report.holiday_report'].search([]),
#         })

#     @http.route('/holiday_report/holiday_report/objects/<model("holiday_report.holiday_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('holiday_report.object', {
#             'object': obj
#         })
