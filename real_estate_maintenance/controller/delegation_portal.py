import binascii
from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression
import logging
import json

_logger = logging.getLogger(__name__)

class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        delegation = request.env['real.estate.delegate']
        if 'delegation_count' in counters:
            values['delegation_count'] = delegation.search_count(self._prepare_delegation_domain(partner)) \
                if delegation.check_access_rights('read', raise_exception=False) else 0

        return values

    def _prepare_delegation_domain(self, partner):
        return [
            ('partner_id', '=', partner.id),
        ]

    def _delegate_get_page_view_values(self, delegate, access_token, **kwargs):
        _logger.info('IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII')
        _logger.info(delegate)
        values = {
            'page_name': 'delegation',
            'delegate_order': delegate,
            'action':delegate._get_portal_return_action(),
        }
        return self._get_page_view_values(delegate, access_token, values, 'my_delegations_history', False, **kwargs)
    
    def _delegate_get_page_view_values(self, delegate, access_token, **kwargs):
        values = {
            'delegate_order': delegate,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': delegate.partner_id.id,
            'report_type': 'html',
            'action': delegate._get_portal_return_action(),
        }

        history = request.session.get('my_delegations_history', [])
        values.update(get_records_pager(history, delegate))
        return values
    
    def _get_delegate_searchbar_sortings(self):
        return {
            'date': {'label': _('Delegate Date'), 'order': 'date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'state': {'label': _('State'), 'order': 'state'},
        }

    @http.route(['/my/delegations', '/my/delegations/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_delegates(self, page=1, date=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        delegation = request.env['real.estate.delegate']

        domain = self._prepare_delegation_domain(partner)

        searchbar_sortings = self._get_delegate_searchbar_sortings()

        if not sortby:
            sortby = 'date'
        sort_delegate = searchbar_sortings[sortby]['order']

        if date:
            domain += [('date', '=', date)]

        delegate_count = delegation.search_count(domain)
        pager = portal_pager(
            url="/my/delegations",
            url_args={ 'date': date, 'sortby': sortby},
            total=delegate_count,
            page=page,
            step=self._items_per_page
        )

        delegates = delegation.search(domain, order=sort_delegate, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_delegates_history'] = delegates.ids[:100]

        values.update({
            'date': date,
            'delegations': delegates.sudo(),
            'page_name': 'delegate',
            'pager': pager,
            'default_url': '/my/delegations',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("real_estate_maintenance.portal_my_delegations", values)

    @http.route(['/my/delegations/<int:delegate_id>'], type='http', auth="public", website=True)
    def portal_delegate_page(self, delegate_id, report_type=None, access_token=None, message=False, download=False, **kw):
        _logger.info('Attempting to access delegate page with ID: %s', delegate_id)
        try:
            delegate_sudo = self._document_check_access('real.estate.delegate', delegate_id, access_token=access_token)
        except (AccessError, MissingError):
            _logger.error('AccessError or MissingError occurred for delegate ID: %s', delegate_id)
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=delegate_sudo, report_type=report_type, report_ref='real_estate_maintenance.action_report_delegation', download=download)

        if delegate_sudo:
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_delegate_%s' % delegate_sudo.id)
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['view_delegate_%s' % delegate_sudo.id] = now
                body = _('Delegation viewed by customer %s', delegate_sudo.partner_id.name)
                _message_post_helper(
                    "real.estate.delegate",
                    delegate_sudo.id,
                    body,
                    token=delegate_sudo.access_token,
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=delegate_sudo.user_id.sudo().partner_id.ids,
                )

        values = self._delegate_get_page_view_values(delegate_sudo, access_token, **kw)
        values['message'] = message

        return request.render('real_estate_maintenance.delegate_real_estate_portal_template', values)

    @http.route(['/my/delegations/<int:delegate_id>/accept'], type='json', auth="public", website=True, csrf=False)
    def portal_delegation_accept(self, delegate_id, access_token=None, name=None, signature=None, **kwargs):
        _logger.info('Attempting to accept delegation with ID: %s', delegate_id)
        access_token = access_token or request.httprequest.args.get('access_token')

        try:
            delegate_sudo = self._document_check_access('real.estate.delegate', delegate_id, access_token=access_token)
        except (AccessError, MissingError):
            _logger.error('AccessError or MissingError occurred for delegate ID: %s', delegate_id)
            return {'error': _('Invalid delegate.')}

        if not delegate_sudo.has_to_be_signed():
            error_msg = _('The delegate is not in a state requiring customer signature.')
            return {'error': error_msg}

        if not signature:
            error_msg = _('Signature is missing.')
            return {'error': error_msg}

        try:
            delegate_sudo.write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'signature': signature,
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            _logger.error('Error occurred while writing signature for delegate ID: %s', delegate_id)
            error_msg = _('Invalid signature data.')
            return {'error': error_msg}

        if delegate_sudo.signature:
            delegate_sudo.action_confirm()
            delegate_sudo._send_delegate_confirmation_mail()

        pdf = request.env.ref('real_estate_maintenance.action_report_delegation').with_user(SUPERUSER_ID)._render_qweb_pdf([delegate_sudo.id])[0]

        _message_post_helper(
            'real.estate.delegate', delegate_sudo.id, _('Delegate signed by %s') % (name,),
            attachments=[('%s.pdf' % delegate_sudo.name, pdf)],
            **({'token': access_token} if access_token else {}))

        query_string = '&message=sign_ok'
        query_string += '#allow_payment=yes'

        response_data = {
            'force_refresh': True,
            'redirect_url': delegate_sudo.get_portal_url(query_string=query_string),
        }

        return response_data
    @http.route(['/my/delegations/<int:delegate_id>/decline'], type='http', auth="public", methods=['POST'], website=True)
    def decline(self, delegate_id, access_token=None, **post):
        _logger.info('Attempting to decline delegation with ID: %s', delegate_id)
        try:
            delegate_sudo = self._document_check_access('real.estate.delegate', delegate_id, access_token=access_token)
        except (AccessError, MissingError):
            _logger.error('AccessError or MissingError occurred for delegate ID: %s', delegate_id)
            return request.redirect('/my')

        message = post.get('decline_message')

        query_string = False
        if delegate_sudo.has_to_be_signed() and message:
            delegate_sudo.action_cancel()
            _message_post_helper('real.estate.delegate', delegate_id, message, **{'token': access_token} if access_token else {})
        else:
            query_string = "&message=cant_reject"

        return request.redirect(delegate_sudo.get_portal_url(query_string=query_string))
