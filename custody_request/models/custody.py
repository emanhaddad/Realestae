# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class CustodyRequest(models.Model):
    _inherit = "custody.request"

    custody_approval_route = fields.Selection(related='company_id.custody_approval_route',
                                               string="Use Approval Route", readonly=True)
    state = fields.Selection([('draft','Draft'),
                              ('sent','Sent'),
                              ('to approve','Under Approval'),
                            #   ('sale','Approved'),
                              ('done','Paid'),
                              ('cleared','Cleared'),
                              ('cancel','Rejected')],default='draft')
    team_custom_id = fields.Many2one('custody.request')
    custody_line_ids = fields.One2many('custody.request.lines', 'custody_request_id', 'Custody line', readonly=True,
                                    states={'done': [('readonly', False)]} )

    current_approver = fields.Many2one(
        comodel_name="'custody.request'", string="Approver",
        compute="_compute_approver", store=True, compute_sudo=True)

    next_approver = fields.Many2one(
        comodel_name="'custody.request'", string="Next Approver",
        compute="_compute_approver", store=True, compute_sudo=True)

    is_current_approver = fields.Boolean(
        string="Is Current Approver", compute="_compute_is_current_approver"
    )

    lock_amount_total = fields.Boolean(
        string="Lock Amount Total", compute="_compute_lock_amount_total"
    )

    amount_total = fields.Monetary(tracking=True)

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'amount_total' in init_values and self.amount_total != init_values.get('amount_total'):
            self._check_lock_amount_total()
        return super(CustodyRequest, self)._track_subtype(init_values)

    def approve(self):
        for order in self:
           #order.write({'state': 'sale'})
           return super(CustodyRequest, order).confirm_post()

    def confirm_dm(self):
        if self.amount > self.custody_category_id.max_amount:
            raise ValidationError(_("The requested amount (%s) is more than the maximum amount (%s) allowed in the custody category ")% (self.amount, self.custody_category_id.max_amount))
        for order in self:

            order.write({'state': 'to approve'})

            # order._add_supplier_to_product()
            if order.user_name.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.user_name.partner_id.id])
        return True

    # def generate_approval_route(self):
    #     """
    #     Generate approval route for order
    #     :return:
    #     """
    #     for order in self:
    #         if not order.team_custom_id:
    #             continue
    #         for team_approver in order.team_custom_id.approver_ids:

    #             custom_condition = order.compute_custom_condition(team_approver)
    #             if not custom_condition:
    #                 # Skip approver, if custom condition for the approver is set and the condition result is not True
    #                 continue

    #             min_amount = team_approver.company_currency_id._convert(
    #                 team_approver.min_amount,
    #                 order.currency_id,
    #                 order.company_id,
    #                 order.custody_date or fields.Date.today())
    #             if min_amount > order.amount_total:
    #                 # Skip approver if Minimum Amount is greater than Total Amount
    #                 continue
    #             max_amount = team_approver.company_currency_id._convert(
    #                 team_approver.max_amount,
    #                 order.currency_id,
    #                 order.company_id,
    #                 order.custody_date or fields.Date.today())
    #             if max_amount and max_amount < order.amount_total:
    #                 # Skip approver if Maximum Amount is set and less than Total Amount
    #                 continue

                # Add approver to the SO
                # raise ('jjjjjjjjjjj')
                # self.env['custody.order.approver'].create({
                #     'sequence': team_approver.sequence,
                #     'team_custom_id': team_approver.team_custom_id.id,
                #     'user_id': team_approver.user_id.id,
                #     'role': team_approver.role,
                #     'min_amount': team_approver.min_amount,
                #     'max_amount': team_approver.max_amount,
                #     'lock_amount_total': team_approver.lock_amount_total,
                #     'order_id': order.id,
                #     'team_approver_id': team_approver.id,
                # })

    def compute_custom_condition(self, team_approver):
        self.ensure_one()
        localdict = {'SO': self, 'USER': self.env.user}
        if not team_approver.custom_condition_code:
            return True
        try:
            safe_eval(team_approver.custom_condition_code, localdict, mode='exec', nocopy=True)
            return bool(localdict['result'])
        except Exception as e:
            raise UserError(_('Wrong condition code defined for %s. Error: %s') % (team_approver.display_name, e))

    def _compute_approver(self):
        print ("yyyyyyyyyyy")
        # for order in self:
        #     next_approvers = order.approver_ids.filtered(lambda a: a.state == "to approve")
        #     order.next_approver = next_approvers[0] if next_approvers else False

        #     current_approvers = order.approver_ids.filtered(lambda a: a.state == "pending")
        #     order.current_approver = current_approvers[0] if current_approvers else False

    @api.depends('current_approver')
    def _compute_is_current_approver(self):
        for order in self:
            order.is_current_approver = ((order.current_approver and order.current_approver.user_id == self.env.user)
                                         or self.env.is_superuser())

    # @api.depends('approver_ids.state', 'approver_ids.lock_amount_total')
    # def _compute_lock_amount_total(self):
    #     for order in self:
    #         order.lock_amount_total = len(order.approver_ids.filtered(lambda a: a.state == "approved" and a.lock_amount_total)) > 0

    def send_to_approve(self):
        for order in self:
            # if order.state != 'to approve' and not order.team_custom_id:
            #     continue

            main_error_msg = _("Unable to send approval request to next approver.")
            if order.current_approver:
                reason_msg = _("The order must be approved by %s") % order.current_approver.user_id.name
                raise UserError("%s %s" % (main_error_msg, reason_msg))

            if not order.next_approver:
                reason_msg = _("There are no approvers in the selected Custody team.")
                raise UserError("%s %s" % (main_error_msg, reason_msg))
            # use sudo as sale user cannot update sale.order.approver
            order.sudo().next_approver.state = 'pending'
            # Now next approver became as current
            current_approver_partner = order.current_approver.user_id.partner_id
            if current_approver_partner not in order.message_partner_ids:
                order.message_subscribe([current_approver_partner.id])
            order.with_user(order.user_id).message_post_with_view(
                'custody_request.request_to_approve_so',
                subject=_('Petty cash Approval: %s') % (order.name,),
                composition_mode='mass_mail',
                partner_ids=[(4, current_approver_partner.id)],
                auto_delete=True,
                auto_delete_message=True,
                parent_id=False,
                subtype_id=self.env.ref('mail.mt_note').id)

    # def _check_lock_amount_total(self):
    #     msg = _('Sorry, you are not allowed to change Amount Total of SO. ')
    #     for order in self:
    #         if order.state in ('draft', 'sent'):
    #             continue
    #         if order.lock_amount_total:
    #             reason = _('It is locked after received approval. ')
    #             raise UserError(msg + "\n\n" + reason)
    #         if order.team_custom_id.lock_amount_total:
    #             reason = _('It is locked after generated approval route. ')
    #             suggestion = _('To make changes, cancel and reset Custody to draft. ')
    #             raise UserError(msg + "\n\n" + reason + "\n\n" + suggestion)
            
class CustodyStatement(models.Model):
    _name = "custody.statement"
    _description = 'Custody Statements'

    name = fields.Char('Name', size=256, required=True, tracking=True)
    account_id = fields.Many2one('account.account','Account', tracking=True)
    journal_id = fields.Many2one('account.journal',string='Journal', tracking=True)




class CustodyLines(models.Model):
    """ To manage custody lines """
    _name = "custody.request.lines"
    _description = 'Custody Resuest Lines'

    name = fields.Char('Name', size=256, default='New')
    custody_request_id = fields.Many2one('custody.request', 'custody request', readonly=True, tracking=True)
    date = fields.Date('Date', required=True, tracking=True)
    cost = fields.Float('Cost', digits=(18, 2), required=True, tracking=True)
    statement_id = fields.Many2one('custody.statement', 'Statement', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department')
    #account_id = fields.Many2one('account.account','Account')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id, readonly=True)
    move_id = fields.Many2one('account.move','Move')

    @api.model
    def create(self, vals):
        code = 'custody.request.statement.code'
        if vals.get('name', 'New') == 'New':
            message = 'CS' + self.env['ir.sequence'].next_by_code(code)
            vals['name'] = message
            # self.message_post(subject='Create CR', body='This is New CR Number' + str(message))
        return super(CustodyLines, self).create(vals)
    
    # def done(self):
    #     lines = []

        # debit_val = {
        #             'name': self.name,
        #             'account_id': self.env.user.company_id.petty_account_id.id,
        #             'debit': self.cost,

        #         }
        # lines.append((0, 0, debit_val))
        # credit_val = { 
        #     'move_id': self.move_id.id,
        #     'name': self.name,
        #     'account_id': self.statement_id.account_id.id,
        #     'credit': self.cost,
        #     'partner_id': self.custody_request_id.employee_id.address_home_id.id,

        # }
        # # datal = {
        # #     'price_unit': self.cost,
        # #     "account_id":self.statement_id.account_id.id,
        # #     'name':self.name,
        # # }

        # lines.append((0, 0, credit_val))

        # move_id = self.env['account.move'].create( {
        #     "date": self.date,
        #     "journal_id": self.statement_id.journal_id.id ,
        #     "ref": self.name,
        #     "line_ids": lines,
            
        # })

        # self.move_id = move_id