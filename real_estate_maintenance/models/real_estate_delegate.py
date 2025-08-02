

from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
import logging
_logger = logging.getLogger(__name__)
from werkzeug.urls import url_encode


class RealEstateDelegate(models.Model):

    _name = 'real.estate.delegate'
    _inherit = ['mail.thread', 'mail.activity.mixin','portal.mixin',]
    _description = 'real Estate delegate'

    @api.depends('marketing_amount', 'owner_amount')
    def get_total(self):
        for rec in self:
            if rec.marketing_amount and rec.owner_amount:
                rec.total_amount = rec.marketing_amount + rec.owner_amount
            else:
                rec.total_amount =0

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False

        if not template_id:
            template_id = self.env['ir.model.data'].xmlid_to_res_id('real_estate_maintenance.email_template_delegation', raise_if_not_found=False)

        return template_id

    def _send_delegate_confirmation_mail(self):
        for delegate in self:
            template_id = delegate._find_mail_template()
            if not template_id:
                raise UserError(_('No email template found for delegation confirmation.'))

            delegate.with_context(force_send=True).message_post_with_template(template_id, composition_mode='comment', email_layout_xmlid="mail.mail_notification_paynow")

    def action_quotation_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        self.write({'state':'wait_customer_sign'})
        template_id = self._find_mail_template()
        _logger.info('LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL  1')
        _logger.info(template_id)
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        _logger.info('LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL  2')
        _logger.info(template.name)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
            _logger.info(lang)
        ctx = {
            'default_model': 'real.estate.delegate',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            #'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'model_description': self.with_context(lang=lang)._description,
        }
        _logger.info('LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL  2')
        _logger.info(ctx)
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def preview_delegation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    def _compute_access_url(self):
        super(RealEstateDelegate, self)._compute_access_url()
        for rec in self:
            rec.access_url = '/my/delegations/%s' % (rec.id)

    def has_to_be_signed(self, include_draft=False):
        return (self.state == 'wait_customer_sign')  and not self.signature

    def _get_portal_return_action(self):
        """ Return the action used to display orders when returning from customer portal. """
        self.ensure_one()
        return self.env.ref('real_estate_maintenance.real_estate_delegate_act_window')

    @api.onchange('unit_id')
    def onchange_unit_id(self):
        if self.unit_id and self.unit_id.buyer_id:
            self.partner_id = self.unit_id.buyer_id.id

    name = fields.Char(string="Name" , default=lambda self: _('New'))
    real_estate_id = fields.Many2one(
        'real.estate',
        'Real Estate',
        help='Real Estate',
        related='unit_id.base_property_id',)
    unit_id = fields.Many2one('real.estate.units', 
                                string="Unit", 
                                required=True,
                                tracking=True,
                                domain=[('state','=','delivered')])
    state = fields.Selection([('new', 'New'),
                              ('wait_customer_sign', 'Waiting customer approval'),
                              ('confirmed', 'Confirmed'),
                              ('finance', 'Finance'),
                              ('approved', 'Approved'),
                              ('cancel', 'Cancelled'),],
                             'State', readonly=True,tracking=True, default='new')
    # base_property_id = fields.Many2one('Project Name', related='unit_id.base_property_id')
    room_count = fields.Integer('Room Count', store=True, related='unit_id.property_rooms')
    area = fields.Float('Area (m²)', store=True, related='unit_id.unit_space')
    # property_floors = fields.Many2one('Floor', related='unit_id.property_floors')
    apartment_number = fields.Char('Apartment Number', store=True, related='unit_id.code')

    contract_id = fields.Many2one('realestate.contract.model', required=True, tracking=True)
    partner_id=fields.Many2one("res.partner", string="Customer" , domain=[('partner_type','=','owner')],
     context="{'default_partner_type': 'owner'}", ondelete="cascade", required=True, tracking=True)
    user_id=fields.Many2one("res.users", string="Sales person",default= lambda self: self.env.user.id,  ondelete="cascade")
    date = fields.Date(string=' Date', index=True, required=True, tracking=True)
    
    total_amount = fields.Monetary(string='Total Amount', compute='get_total', tracking=True)
    marketing_amount = fields.Monetary(string='Marketing Amount', required=True, tracking=True)
    owner_amount = fields.Monetary(string="Owner's Amount", required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency",
         default=lambda self: self.env.company.currency_id.id)
    signature = fields.Image('Signature', tracking=True, help='Signature received through the portal.', copy=False, attachment=True, max_width=1024, max_height=1024)
    signed_by = fields.Char('Signed By', tracking=True, help='Name of the person that signed the SO.', copy=False)
    signed_on = fields.Datetime('Signed On', tracking=True, help='Date of the signature.', copy=False)
    payment_ids =fields.Many2many('account.payment', string='Payments')
    payment_move_id = fields.Many2one('account.move',string='payment Ref',readonly=True, tracking=True)



    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update the domain of contract_id based on the selected partner.

        """
        # domain = [('partner_id', '=', self.partner_id.id)]
        # domain += [('unit_id', '=', self.unit_id.id)]
        # return {'domain': {'contract_id': domain}}
        domain = [('partner_id', '=', self.partner_id.id)]
        if self.unit_id:
            domain.append(('unit_id', '=', self.unit_id.id))
        return {'domain': {'contract_id': domain}}
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.delegate') or _('New')

        result = super(RealEstateDelegate, self).create(vals)
        return result

    def set_to_new(self):
        self.write({'state':'new'})


    def action_wait(self):
        return self.write({'state': 'wait_customer_sign'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})


    def action_confirm(self):
        self.unit_id.write({'state': 'delegated'})
        return self.write({'state': 'confirmed'})

    def action_wait_finance(self):
        return self.write({'state': 'finance'})

    def action_approve(self):
        payment_id = self.env['cash.receive'].create({
                    'state': 'draft',
                    'date': fields.Date.today(),
                    'partner_id': self.partner_id.id,
                    'amount': self.total_amount,
                    'disc' : self.name + ' ' + 'مستند التفويض رقم',
                    'delegate_request_ids' : self.id,
                })

        return self.write({'state': 'approved'})

    def open_move(self):
    
        tree_view = self.env.ref('cash_request.cash_receive_tree_view')
        form_view = self.env.ref('cash_request.cash_receive_view')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Receipt Vouchers',
            'res_model': 'cash.receive',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': {'default_name': self.display_name},
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('delegate_request_ids', '=', self.id)],

    }


    
    