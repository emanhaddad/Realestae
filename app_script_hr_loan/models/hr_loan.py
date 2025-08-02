# -*- coding: utf-8 -*-
##############################################################################
#
#    App-script Business Solutions
#
##############################################################################

from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil import relativedelta
import math
import logging
logger= logging.getLogger(__name__)


class LoansType(models.Model):
    _name = "hr.loan.type"
    _description = "Loans Types"

    name = fields.Char(string='Loan Name', required=True, translate=True)
    code = fields.Char(string='Loan code')
    active = fields.Boolean(default=True)
    start_date = fields.Date('Start Date', default=fields.Date.context_today,required=True)
    end_date = fields.Date('End Date')
    loan_type = fields.Selection([
        ('fixed','Fixed Amount'),
        ('salary','Based on Salary')
        ], required=True, default='fixed', string='Loan Type')
    loan_amount = fields.Float(string="Loan Amount", required=True)
    max_loan_amount = fields.Float(string="Max Loan Amount")
    factor = fields.Float(string="Factor", default=1 )
    installment = fields.Integer(string="No Of Installments",required=True, default=1)
    loan_account_id = fields.Many2one('account.account', domain=[('deprecated', '=', False)], string="Loan Account")
    loan_journal_id = fields.Many2one('account.journal','Journal')
    times_stop_loan =fields.Integer(string="Times of Stop Loan")
    period_stop_loan = fields.Integer(string="Period of Stop Loan")
    loan_limit = fields.Selection([
       ('one','Once'),
       ('limit','limit'),
       ('unlimit','Unlimit')], default='one', string='Limit', required=True)
    limit = fields.Integer(string="Loan Limit")
    salary_rule_ids = fields.Many2many('hr.salary.rule', string='Salary Rules')
    company_id = fields.Many2one('res.company', 'Company', readonly=True,
         default=lambda self: self.env.user.company_id)
    structure_type_ids = fields.Many2many('hr.payroll.structure.type', 'hr_loan_type_rel_struct_type_ids' ,string='Salary Structure Type')
    emp_tag_ids = fields.Many2many('hr.employee.category', string='Employee Tags')
    interference = fields.Boolean(string='Allow Interference')
    year_employment =fields.Integer(string="Years of Employment",default=1)
    validation = fields.Boolean(string="Apply Double Validation ")
    note = fields.Text(string='Description')
    decimal_calculate = fields.Selection([
       ('with','With decimal part'),
       ('without','Without decimal part')], default='with', string='decimal calculating', required=True)
    loan_purpose = fields.Text('Loan Purpose', required=True)
    request_by_employee = fields.Boolean(string="Request By Employee", default=True)
    violation = fields.Boolean(string="Allow violation Years of Employment")
    need_evaluate_performance = fields.Boolean(string="Need evaluate Performance")
    evaluate_degree = fields.Char('Degree of evaluation required')
    month_no=fields.Integer(string="Allow violation Years of Employment")


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread']
    _description = "Loans Requests"
    _order = "date desc, id desc"

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char(string="Loan Name", default="/", readonly=True)
    date = fields.Date(string="Date", default=fields.Date.today(), )
    restructure = fields.Text(tracking=True)
    payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today(),tracking=True)
    loan_id = fields.Many2one('hr.loan.type', string='Loan Type', required=True, readonly=True,
        states={'draft': [('readonly', False)]},tracking=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True,
        states={'draft': [('readonly', False)]}, default=_default_employee)
    department_id = fields.Many2one('hr.department', related="employee_id.department_id",store=True,
        string="Department")

    installment = fields.Integer(string="No Of Installments", required=True, default=1,tracking=True)
    requested_amount = fields.Float(string="Requested Amount", required=True,tracking=True)
    loan_amount = fields.Float(string="Loan Amount", required=True)
    salary_amount = fields.Float(string="Salary Amount", )
    installment_amount = fields.Float(string="Installment Amount",store=True,tracking=True)
    remain_amount = fields.Float(string="Remain Amount", compute='_compute_loan_amount', store=True)
    total_paid_amount = fields.Float(string="Total Paid Amount", compute='_compute_loan_amount', store=True,)
    loan_arc_ids = fields.One2many('hr.loan.archive','loan_id',string='Installments', index=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True,
         default=lambda self: self.env.user.company_id)
    move_id = fields.Many2one('account.move',string='Move', readonly=True)
    validation = fields.Boolean(related="loan_id.validation",string="Double Validation",readonly=False)
    note = fields.Text(string='Notes')
    reject_reason = fields.Text(string='Reject Reason')
    state = fields.Selection([('draft','Draft'),
        ('rejected','Rejected'),
        ('requested','Requested'),
        ('approved2','Second Approved'),
        ('approved','Approved'),
        ('transfered','Transfered'),
        ('paid','Paid'),
        ('done','Done')
        ], string="State", default='draft', tracking=True, copy=False, )
    loan_purpose = fields.Text('Loan Purpose', related="loan_id.loan_purpose")
    employee_counts = fields.Integer(string="Employee Counts")
    contract_id = fields.Many2one('hr.contract' , string="Contract",compute="set_contract" , store=True)
    max_ins_num = fields.Integer(string="Max No Of Installments", related="loan_id.installment")
    max_loan_amount = fields.Integer(string="Max Loan Amount", compute="_compute_max",store=True)
    check_update = fields.Boolean(
        string='Field Label',compute='_compute_loan_amount',
    )
    active = fields.Boolean(default=True)

    direct_payment_ids = fields.Many2many('account.move',string='Direct Payments ',
    help='here we register the amounts out of scheduled installment like reducing the loan number', )

    
    def restructuring_loan(self):
        action = self.env.ref('app_script_hr_loan.action_restructure_loan').read()[0]
        action.update({
            'context': {'default_loan_id': self.id,'default_remain_amount': self.remain_amount,
            'default_installment': self.env['hr.loan.archive'].search_count([
                ('loan_id','=',self.id),('employee_id','=',self.employee_id.id),
                ('loan_id.name','=',self.name),('state','=','paid')]
                )}
            })
        return action

    def _compute_max(self):
        for rec in self :
            if rec.loan_id.loan_type == 'fixed':
                rec.max_loan_amount = rec.loan_id.loan_amount
            if rec.loan_id.loan_type == 'salary':
                loan_amount = 0.0
                if rec.employee_id:
                    contract_id = rec.env['hr.contract'].search([
                        ('employee_id','=',rec.employee_id.id),
                    ],limit=1)
                    if contract_id:
                        for rule in rec.loan_id.salary_rule_ids:
                            loan_amount +=  rule.compute_allowed_deduct_amount(contract_id)
                            loan_amount *= rec.loan_id.factor
                        if loan_amount > rec.loan_id.max_loan_amount:
                            loan_amount = rec.loan_id.max_loan_amount

                        rec.max_loan_amount = loan_amount
            else:
                rec.max_loan_amount = 0.0


    @api.onchange('loan_id')
    def chec_domain(self):
        domain = []
        if self.loan_id.structure_type_ids:
            domain = [('contract_id.structure_type_id','in',self.loan_id.structure_type_ids.ids)]
        lst_contract = self.env['hr.employee'].search(domain)
        return {'domain': {'employee_id':[('id', 'in', lst_contract.ids)]}}

    
    @api.constrains('installment','installment_amount','loan_arc_ids',)
    def _check_installment(self):
        contract = self.employee_id.contract_id
        if contract:
            percentage = self.company_id.max_employee
            max_loan = (contract.wage * percentage) / 100
            emp_loans = self.env['hr.loan'].search([('id','!=',self.id),('employee_id', '=', self.employee_id.id),('state','!=','rejected')]).filtered(lambda loan:datetime.strptime(str(loan.date), "%Y-%m-%d").month == fields.Date.from_string(fields.Date.today()).month)

            amount_per_month = sum(emp_loans.mapped('installment_amount'))
            if percentage > 0 :
                if amount_per_month > max_loan:
                    raise ValidationError (_("This employee has exceeded the allowance percentage loans for this month"))

                if amount_per_month + self.installment_amount > max_loan:
                    raise ValidationError(_('The residual loan balance for this employee is %s' ) % (str(max_loan - amount_per_month)))
    
    def unlink(self):
        for loan in self:
            if loan.state not in ('draft'):
                raise UserError(_('You cannot delete a Record which is not in draft state.'))
            loan.loan_arc_ids.unlink()
        return super(HrLoan, self).unlink()

    

    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            self.invalidate_cache(['remain_amount','total_paid_amount'], [loan.id])
            for line in loan.loan_arc_ids:
                if line.state == 'done':
                    total_paid += line.amount
            remain_amount = loan.loan_amount - total_paid
            loan.write({'remain_amount':remain_amount,
                        'total_paid_amount':total_paid,
                        'check_update':True,
                            })
            self.invalidate_cache(['remain_amount','total_paid_amount'], [loan.id])

    @api.model
    def create(self, vals):
        vals['employee_counts'] = self._loan_count(vals['employee_id'])
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan.seq') or '/'
        return super(HrLoan, self).create(vals)

    
    def _loan_count(self,employee_id):
        return self.env['hr.loan'].search_count([('employee_id', '=', employee_id)]) + 1


    @api.onchange('installment')
    def onchange_installment(self):
        if not self.loan_id:
            return
        if self.installment > self.loan_id.installment:
            raise ValidationError(_('The number of installment is more than maximum number of installments.'))
        self.installment_amount = self.requested_amount /  self.installment

    @api.onchange('requested_amount',)
    def onchange_requested_amount(self):
        if not self.loan_id:
            return
        if self.requested_amount <= self.loan_id.loan_amount and self.loan_id.loan_type == 'fixed':
            self.installment_amount = self.requested_amount /  self.installment
            self.loan_amount = self.requested_amount
        if self.loan_id.loan_type == 'salary' and self.requested_amount <= self.salary_amount:
            self.installment_amount = self.requested_amount /  self.installment
            self.loan_amount = self.requested_amount
      
    @api.constrains('requested_amount','installment')
    def _check_requested_amount(self):
        for rec in self:
            if rec.loan_id and rec.requested_amount :
                if rec.loan_id.loan_type =='fixed':
                    if rec.requested_amount > rec.loan_id.loan_amount:
                        raise UserError(_("Requeste amount must be less than or equal loan amount"))
                if rec.loan_id.loan_type == 'salary':
                    if rec.requested_amount > rec.max_loan_amount:
                        raise UserError(_("Requeste amount must be less than or equal loan amount"))
            if rec.installment > rec.loan_id.installment :
                raise ValidationError(_('The number of installment is more than maximum number of installments.'))

    @api.constrains('loan_id','payment_date',"contract_id")
    def _check_loan_type_id_condtion(self):
        for rec in self:
            if rec.loan_id :
                if not rec.loan_id.interference:
                    loans = self.env['hr.loan'].search([('id','!=',self.id),('employee_id', '=', self.employee_id.id),('state','not in',['rejected','done'])])
                    interferences_loans = loans.filtered(lambda loan:loan.loan_id.id  == self.loan_id.id)
                    if interferences_loans :
                        interferences_loans_namse = interferences_loans.mapped('name')
                        raise ValidationError(_("Sorry you can't teake this type of loans until finsh this loans %s ") % (interferences_loans_namse) )
            if rec.loan_id.month_no > 0:
                loan_ids = rec.search([
                ('employee_id','=',rec.employee_id.id),
                ('loan_id','=',rec.loan_id.id),
                ('state','not in',['rejected']),('id','!=',rec.id)],order="date desc",limit=1)
                if loan_ids:
                    for line in loan_ids:
                        old_date=datetime.strptime(str(rec.payment_date), '%Y-%m-%d')-datetime.strptime(str(line.payment_date), '%Y-%m-%d')
                        next_request= (old_date).days  / 30
                        if next_request < rec.loan_id.month_no :
                            months = round(rec.loan_id.month_no -next_request ,2)
                            raise ValidationError(_("Sorry you can't teake this type of loans until you compleate  %s  month") % (str( months )))
    
    @api.depends('employee_id')
    def set_contract(self):
        contract_id = self.env['hr.contract'].search([
            ('employee_id','=',self.employee_id.id),
            ('state','=','open')
        ],limit=1)
        if contract_id:
            self.contract_id = contract_id.id
            structure_domain = ['|',('structure_type_ids','in',(contract_id.structure_type_id.id)),('structure_type_ids','=',False)]
            tag_domain = ['|',('emp_tag_ids','in',contract_id.employee_id.category_ids.ids),('emp_tag_ids','=',False)]
            domain = structure_domain + tag_domain
            avalibel_loan_type = self.env['hr.loan.type'].search(domain)
        else:
            self.contract_id = False

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        contract_id = self.env['hr.contract'].search([
            ('employee_id','=',self.employee_id.id),
            ('state','=','open')
        ],limit=1)
        if contract_id:
            structure_domain = ['|',('structure_type_ids','in',contract_id.structure_type_id.id),('structure_type_ids','=',False)]
            
            domain = structure_domain 
            avalibel_loan_type = self.env['hr.loan.type'].search(domain)
            return {'domain':{'loan_id':[('id' ,'in',avalibel_loan_type.ids)]}}

    @api.onchange('loan_id','employee_id')
    def onchange_loan_id(self):
        if not self.loan_id:
            return
        loan_amount = 0.0
        if self.loan_id.loan_type == 'fixed':
            loan_amount = self.loan_id.loan_amount
        else:
            if self.employee_id:
                contract_id = self.env['hr.contract'].search([
                    ('employee_id','=',self.employee_id.id),
                ],limit=1)
                if contract_id:
                    #to open as it and remove after comment line
                    '''for rule in self.loan_id.salary_rule_ids:
                        print ('............... my rule is : ',rule)
                        loan_amount +=  rule.compute_allowed_deduct_amount(contract_id)
                        loan_amount *= self.loan_id.factor
                    if loan_amount > self.loan_id.max_loan_amount:
                        loan_amount = self.loan_id.max_loan_amount
                    '''
                    loan_amount = self.loan_id.max_loan_amount

        self.max_ins_num = self.loan_id.installment
        self.max_loan_amount = loan_amount
        self.loan_amount = loan_amount
        self.requested_amount = loan_amount
        self.installment = self.loan_id.installment
        self.salary_amount = loan_amount
        if self.loan_id.installment > 0:
            self.installment_amount = loan_amount /  self.loan_id.installment
    
    def action_request(self):
        for loan in self:
            if loan.loan_amount <= 0.0:
                raise UserError(_("Loan Amount must be grater than 0"))
            if loan.satisfy_condition():
                loan.compute_installment()
                self.write({'state':'requested'})
            
            if self.loan_id.month_no > 0:
                loan_ids = self.search([
                ('employee_id','=',self.employee_id.id),
                ('loan_id','=',self.loan_id.id),
                ('state','in',['rejected'])])

                if loan_ids:
                    for rec in loan_ids:
                        old_date=datetime.strptime(str(rec.date), '%Y-%m-%d')-datetime.strptime(str(self.date), '%Y-%m-%d')

                        next_request= abs((old_date).days)/30
                        if next_request < self.loan_id.month_no :
                            msg =  _("Not allowed to request this type of loan")
                            self.write({'state': 'rejected','reject_reason': msg})
                            break
        return True

    def _check_security_action_approve(self):
        for rec in self :
            manger_user_id = rec.sudo().employee_id.get_employee_manager_user_id()
            manger_of_manger_user_id = rec.sudo().employee_id.parent_id.get_employee_manager_user_id()

            if not ((rec.env.uid == manger_user_id or rec.env.uid == manger_of_manger_user_id  or manger_user_id == False) or rec.env.user.has_group('app_script_hr_loan.group_loan_configration')):
                raise UserError(_('Only an HR Officer or Manager can approve loan requests.'))


    def _check_security_action_validate(self):
        for rec in self :
            manger_user_id = rec.sudo().employee_id.parent_id.get_employee_manager_user_id()
            if  not ((manger_user_id == rec.env.uid or manger_user_id ==  False) or rec.env.user.has_group('app_script_hr_loan.group_loan_configration')) :
                raise UserError(_('Only an HR Manager can apply the second approval on leave requests.'))

    
    def action_approve(self):
        self._check_security_action_approve()
        for loan in self:
            if loan.validation:
                return loan.write({'state': 'approved2'})
            else:
                loan.action_double_approve()

    
    def action_double_approve(self):

        if self.state == 'approved2':
            self._check_security_action_validate()
        else :
            self._check_security_action_approve()
        self.write({'state': 'approved'})

    
    def action_draft(self):
        self.write({'state': 'draft'})

    
    def action_refuse(self):
        msg  = _("Loan rejected")
        self.write({'state': 'rejected','reject_reason': msg})

    def action_done(self):
        for rec in self:
            if rec.remain_amount == 0 :
                rec.write({'state': 'done'})
            else:
                raise UserError(_("Sorry,, You must pay all installments "))

    
    def satisfy_condition(self):
        self.ensure_one()
        # CHECK: Loan Limit is Once:
        if not self._check_loan_limit():
            return False

        # CHECK: Interference:
        if not self._check_interference():
            return False

        # CHECK: Employment years
        if not self._check_year_employment():
            return False

        return True

    
    def _check_loan_limit(self):
        if self.loan_id.loan_limit == 'one':
            loan_ids = self.search([
                ('employee_id','=',self.employee_id.id),
                ('loan_id','=',self.loan_id.id),
                ('state','not in',['draft','rejected'])])
            if len(loan_ids) >= 1:
                msg  = _("Loan Limit is Once and Already Taken")
                self.write({'state': 'rejected','reject_reason': msg})
                return False

        if self.loan_id.loan_limit == 'limit':
            loan_ids = self.search([
                ('employee_id','=',self.employee_id.id),
                ('loan_id','=',self.loan_id.id),
                ('state','not in',['draft','rejected'])])
            if len(loan_ids) >= self.loan_id.limit:
                msg  = _('Loan Limit is %s and Already Taken') %(self.loan_id.limit)
                self.write({'state': 'rejected','reject_reason': msg})
        return True

    
    def _check_interference(self):
        if (self.loan_id.loan_limit == 'unlimit' or self.loan_id.loan_limit == 'unlimit') and  not self.loan_id.interference:
            loan_ids = self.search([
                ('employee_id','=',self.employee_id.id),
                ('loan_id','=',self.loan_id.id),
                ('state','not in',['draft','rejected','done'])])
            if len(loan_ids) >= 1:
                msg  =  _("Interference Between same Loan Not Allowed")
                self.write({'state': 'rejected','reject_reason': msg})
                for line in self.loan_arc_ids:
                    line.state = 'reject'
                return False
        return True

    
    def _check_year_employment(self):
        if not self.loan_id.violation:
            cont_date = fields.Date.from_string(self.contract_id.date_start)
            loan_date = fields.Date.from_string(self.date)
            days = (loan_date - cont_date).days
            if self.loan_id.year_employment * 365  > days:
                msg =  _("Employment years for Employee Not Fit employment Years for The Loan")
                self.write({'state': 'rejected','reject_reason': msg})
                return False

        return True
    
    def _check_request_month(self):
        if self.loan_id.month_no > 0:
            loan_ids = self.search([
                ('employee_id','=',self.employee_id.id),
                ('loan_id','=',self.loan_id.id),
                ('state','=','approved')])

            if len(loan_ids) > 1:
                for rec in loan_ids:
                    next_request= datetime.strptime(str(self.date), '%Y-%m-%d').months - datetime.strptime(str(rec.date), '%Y-%m-%d').months
                    if next_request < self.loan_id.month_no:
                        msg =  _("Not allowed to request this type of loan")
                        self.write({'state': 'rejected','reject_reason': msg})
        return True
    
    def action_transfer(self):
        for loan in self:
            if not loan.loan_arc_ids:
                raise UserError(_("Please Compute installment"))
            else:
                if loan.installment != len([x.id for x in loan.loan_arc_ids if x.state not in ['suspend']]):
                    raise ValidationError(_('The number of installment must equal installments. \n Plase recompute installments'))
                line_amount = sum(x.amount for x in loan.loan_arc_ids if x.state not in ['suspend'])
                line_amount = round(line_amount ,2)

                if loan.loan_amount != line_amount:
                  raise ValidationError(_('The Summation of installments amount must equal loan amount.'))
            if not loan.loan_id.loan_account_id:
                raise UserError(_("Please specify Debit account in Selected Loan Type"))
            if not loan.loan_id.loan_journal_id:
                raise UserError(_("Please specify journal in Selected Loan Type"))

            if not loan.loan_id.loan_journal_id.payment_credit_account_id.id:
                raise UserError(_("Please specify journal payment credit account "))

            move_id = self.env['account.move'].create({
                'move_type': 'entry',
                'invoice_date': loan.payment_date,
                'journal_id':loan.loan_id.loan_journal_id.id,
                'partner_id':loan.employee_id.address_home_id.id,
                'line_ids': [
                    (0, None, {
                        'name': loan.name or '',
                        'debit': loan.loan_amount  or 0.0,
                        'credit':  0.0,
                        'quantity': 1.0,
                        'date_maturity': loan.payment_date,
                        'currency_id': self.company_id.currency_id.id,
                        'account_id': loan.loan_id.loan_account_id.id,
                        'partner_id': self.employee_id.address_home_id.id,
                        'exclude_from_invoice_tab': True,
                    }),
                    (0, None, {
                        'name': loan.name or '',
                        'debit': 0.0,
                        'credit':  loan.loan_amount  or 0.0,
                        'quantity': 1.0,
                        'date_maturity': loan.payment_date,
                        'currency_id': self.company_id.currency_id.id,
                        'account_id': loan.loan_id.loan_journal_id.payment_credit_account_id.id,
                        'partner_id': self.employee_id.address_home_id.id,
                        'exclude_from_invoice_tab': True,
                    })

                    ]
            })
            move_id.post()
            self.write({'move_id': move_id.id})
            loan.loan_arc_ids.write({'state': 'paid'})
            self.write({'state': 'paid', 'move_id': move_id.id})

    
    def compute_installment(self):
        for loan in self:
            loan.loan_arc_ids.unlink()
            num=1
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.installment_amount
            if loan.loan_id.decimal_calculate == 'without':
                if not amount.is_integer():
                    num=2
                    frac, whole = math.modf(amount)
                    decimal_amount = frac * loan.installment
                    decimal_amount +=whole
                    amount=whole
                    self.env['hr.loan.archive'].create({
                        'date': date_start,
                        'year': date_start.year,
                        'month': date_start.month,
                        'amount': decimal_amount,
                        'employee_id': loan.employee_id.id,
                        'loan_type_id': loan.loan_id.id,
                        'loan_id': loan.id
                    })
                    date_start = date_start + relativedelta.relativedelta(months=+1)
            if amount != 0:
                for i in range(num, loan.installment + 1):
                    self.env['hr.loan.archive'].create({
                        'date': date_start,
                        'year': date_start.year,
                        'month': date_start.month,
                        'amount': amount,
                        'employee_id': loan.employee_id.id,
                        'loan_type_id': loan.loan_id.id,
                        'loan_id': loan.id})
                    date_start = date_start + relativedelta.relativedelta(months=+1)
        return True

    
    def action_payment(self):
        for loan in self:
            loan.loan_arc_ids.write({'state': 'paid'})
        self.write({'state': 'paid'})
        return True


class LoanArchive(models.Model):
    _name = "hr.loan.archive"
    _description = "Loan Archive"

    date = fields.Date(string="Payment Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    amount = fields.Float(string="Amount", required=True)
    month = fields.Integer('Month', required=True)
    year = fields.Integer('Year', required=True)
    loan_type_id = fields.Many2one('hr.loan.type', string="Loan Type")
    loan_id = fields.Many2one('hr.loan', string="Loan")
    payment_type = fields.Selection([
       ('salary','Salary') ,
       ('direct_payment','Direct Payment')
       ], string='Payment Type', required=True, default='salary')
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.", ondelete='set null')
    state = fields.Selection([
        ('draft','Draft'),
        ('suspend','Suspend'),
        ('reject','Rejected'),
        ('paid','To Deduct'),
        ('done','Done')
        ], string='Status', readonly=True, copy=False, default='draft')
    company_id = fields.Many2one('res.company', 'Company', related="loan_id.company_id")

    
    def name_get(self):
        res = []
        for rec in self:
            name = "%s - %s (%s / %s)" % (rec.employee_id.name, rec.loan_id.name,rec.month,rec.year)
            res += [(rec.id, name)]
        return res

    
    def action_new_arah(self):
        for arch in self:
            loan_archive = self.search([('loan_id','=',arch.loan_id.id)],order='date desc', limit=1)
            date_start = datetime.strptime(str(loan_archive.date), '%Y-%m-%d')
            date_start = date_start + relativedelta.relativedelta(months=+1)
            self.create({
                'date': date_start,
                'year': date_start.year,
                'month': date_start.month,
                'amount': arch.amount,
                'employee_id': arch.employee_id.id,
                'loan_type_id': arch.loan_type_id.id,
                'loan_id': arch.loan_id.id,
                'state':'paid'})
        return True

    
    def action_suspend(self):
        self.action_new_arah()
        self.write({'state': 'suspend'})

    
    def action_paid(self):
        self.write({'state': 'paid', 'payslip_id': False})
        for arc in self:
           if arc.loan_id.state=='done' and arc.loan_id.remain_amount > 0.0:
               arc.loan_id.write({'state': 'paid'})
        return True

    
    def action_done(self):
        self.write({'state': 'done'})
        for arc in self:
            if arc.loan_id.remain_amount <= 0 and arc.loan_id.state =='paid':
                arc.loan_id.write({'state': 'done'})
        return True

    
class LoanSuspend(models.Model):
    _name = "hr.loan.suspend"
    _inherit = ['mail.thread']
    _description = "Suspended Loans"
    _order = "id desc"

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name =  fields.Char("Name", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True,
        states={'draft': [('readonly', False)]}, default=_default_employee)
    loan_id = fields.Many2one("hr.loan",'Loan', required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    arc_ids = fields.Many2many('hr.loan.archive', string='Installments')
    note = fields.Text("Notes")
    state = fields.Selection([
        ('draft','Draft'),
        ('requested','Requested'),
        ('approved','Approved'),
        ('rejected','Rejected')
        ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')
    times_stop_loan =fields.Integer(string="Times of Stop Loan" ,related="loan_id.loan_id.times_stop_loan" )
    period_stop_loan = fields.Integer(string="Period of Stop Loan" ,related="loan_id.loan_id.period_stop_loan")
    company_id = fields.Many2one('res.company', 'Company', related="loan_id.company_id")
    date = fields.Date(string="Date")

    @api.model
    def create(self, vals):
        if not vals.get('name', False):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan.suspend') or '/'
        return super(LoanSuspend, self).create(vals)

    @api.onchange('start_date','end_date')
    def _onchange_dates(self):
        for rec in self:
            lines =[]
            for line in rec.arc_ids:
                if line.date >= rec.start_date and line.date <= rec.end_date:
                    lines.append(line.id)
            rec.arc_ids = [(6, 0,[x for x in lines])]

    
    def action_reject(self):
        self.write({'state':'rejected'})

    
    def action_draft(self):
        self.write({'state':'draft'})

    
    def action_approve(self):
        self.arc_ids.action_suspend()
        self.write({'state': 'approved','date':fields.Date.today()})

    
    def action_request(self):

        if  not self.arc_ids:
            raise UserError(_('Please specify installment'))
        times_of_stop = self.search([
            ('loan_id','=',self.loan_id.id),('state','in',['requested','approved'])])
        if  len(times_of_stop) >= self.loan_id.loan_id.times_stop_loan:
            raise ValidationError(_('You cannot suspend a loan max  suspend times is  %s.') % (self.loan_id.loan_id.times_stop_loan,))
        if  len(self.arc_ids) > self.loan_id.loan_id.period_stop_loan:
            raise ValidationError(_('Suspend Duration is bigger than allowed duration  %s.') % (self.loan_id.loan_id.period_stop_loan,))

        return self.write({'state':'requested'})


class HrLoanEmployee(models.Model):
    _inherit = "hr.employee"

    
    def _compute_employee_loans(self):
        self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])

    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')
    
    def get_avalibel_loan_type(self,contract_id):
        contract_id = self.env['hr.contract'].search([
            ('id','=',contract_id),
        ],limit=1)

        if contract_id:
            structure_domain = ['|',('structure_type_ids','in',contract_id.structure_type_id.id),('structure_type_ids','=',False)]
            domain = structure_domain 
            avalibel_loan_type = self.env['hr.loan.type'].search(domain)
            avalibel_loan_type = avalibel_loan_type.mapped(lambda r: {"id": r.id,
                "installment": r.installment,
                "loan_amount": r.loan_amount,
                "loan_purpose": r.loan_purpose,
                "loan_type": r.name,
                })

            return avalibel_loan_type
        return []

    def get_employee_manager_user_id(self):
        #this function is used for get employee manager
        for rec in self:
            manager_user_id = False
            manager_user_id = rec.sudo().parent_id.user_id.id
            if not manager_user_id:
                manager_user_id = rec.sudo().department_id.manager_id.user_id.id
            return manager_user_id


