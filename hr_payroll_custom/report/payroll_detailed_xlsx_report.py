# -*- coding: utf-8 -*-
##############################################################################
#
#	NCTR, Nile Center for Technology Research
#	Copyright (C) 2021-2021 NCTR (<http://www.nctr.sd>).
#
##############################################################################
from odoo import models , _
import string


class DetailedXlsxReport(models.AbstractModel):
    _name = 'report.hr_payroll_custom.xlsx_payroll_detailed_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        format1 = workbook.add_format(
            {'font_size': 12, 'align': 'vcenter', 'bold': True, 'bg_color': '#d2ecfa', 'color': 'black',
             'bottom': True, })
        format2 = workbook.add_format(
            {'font_size': 12, 'align': 'vcenter', 'bold': True, 'bg_color': '#d2ecfa', 'color': 'black',
             'num_format': '#,##0.00'})
        format3 = workbook.add_format({'font_size': 11, 'align': 'vcenter', 'bold': False, 'num_format': '#,##0.00'})

        format4 = workbook.add_format({'font_size': 16, 'align': 'center', 'bold': True,'color':'#118aa6'})
        sheet = workbook.add_worksheet('Employees Sheet')
        cols = list(string.ascii_uppercase) + ['AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ', 'AK',
                                               'AL', 'AM', 'AN', 'AO', 'AP', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AV',
                                               'AW', 'AX', 'AY', 'AZ']
        rules = []
        rules_ids = []
        col_no = 3
        for line in lines.slip_ids :
            rule_ids = self.env['hr.payroll.structure'].browse(line.struct_id).get_all_rules()
            sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
            rule_ids = self.env['hr.salary.rule'].browse(sorted_rule_ids)
            for rule in rule_ids :
                if rule not in rules_ids :
                    rules_ids.append(rule)
            break
        
        for item in rules_ids :
            if item.code not in ['GROSS','NET'] : 

                col_title = ''
                row = [None, None, None, None, None,None]
                row[0] = col_no
                row[1] = item.code
                row[2] = item.name
                col_title = str(cols[col_no]) + ':' + str(cols[col_no])
                row[3] = col_title
                if len(item.name) < 8:
                    row[4] = 12
                else:
                    row[4] = len(item.name) + 2
                rules.append(row)
                col_no += 1


        # List report column headers:
        batch_period = str(lines.date_start.strftime('%B %d, %Y')) + '  To  ' + str(
            lines.date_end.strftime('%B %d, %Y'))
        company_name = lines.env.company.name
        # Company Name
        sheet.merge_range(0,2, 3,5, company_name+'\nPayslip Detailed Report'+'\n'+batch_period, format4)


        i = 1
        sheet.write(5, 0, _('Employee Name'), format1)
        sheet.write(5, 1, _('Department'), format1)
        sheet.write(5, 2, _('Structure'), format1)
        for rule in rules:
            sheet.write(5, rule[0], rule[2], format1)
        

        sheet.write(5, rule[0]+i,_('NET'), format1)
        net_col = str(cols[rule[0]+i]) + ':' + str(cols[rule[0]+i])

        # Report
        # Details:
        details_row = 6
        has_payslips = False
        
        for slip in lines.slip_ids:
            i = 1
            has_payslips = True
            sheet.write(details_row, 0, slip.employee_id.name, format3)
            sheet.write(details_row, 1, slip.employee_id.department_id.name, format3)
            sheet.write(details_row, 2, slip.struct_id.name, format3)

            for line in slip.line_ids:
                if line.code not in ['GROSS'] : 
                    for rule in rules:
                        if line.code == rule[1]:
                            if line.amount > 0:
                                sheet.write(details_row, rule[0], line.total, format3)
                            else:
                                sheet.write(details_row, rule[0], line.total, format3)
            
            sheet.write(details_row, rule[0]+i , slip.net_wage, format3)
            
            details_row += 1
            
        col_no +=1
        # Generate summission row at report end:
        sum_x = details_row
        if has_payslips == True:
            sheet.write(sum_x, 0, 'Total', format2)
            for i in range(3, col_no):
                sum_start = cols[i] + '3'
                sum_end = cols[i] + str(sum_x)
                sum_range = '{=SUM(' + str(sum_start) + ':' + sum_end + ')}'
                sheet.write_formula(sum_x, i, sum_range, format2)
                i += 1

        # set width and height of colmns & rows:
        sheet.set_column('A:A', 35)
        sheet.set_column('B:B', 35)
        for rule in rules:
            sheet.set_column(rule[3], rule[4])
        sheet.set_column('C:C', 35)
        sheet.set_column(net_col,15)

