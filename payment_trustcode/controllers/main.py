import logging
from odoo import http
from odoo.http import request
from werkzeug.utils import redirect

_logger = logging.getLogger(__name__)


class IuguController(http.Controller):
    _notify_url = '/iugu/notificacao/'

    @http.route(
        '/iugu/notificacao/', type='http', auth="none",
        methods=['GET', 'POST'], csrf=False)
    def iugu_form_feedback(self, **post):
        request.env['payment.transaction'].sudo().form_feedback(post, 'iugu')
        return "<status>OK</status>"

    # @http.route(
    #     '/iugu/checkout/redirect', type='http',
    #     auth='none', methods=['GET', 'POST'])
    # def iugu_checkout_redirect(self, **post):
    #     post = post
    #     if 'secure_url' in post:
    #         return redirect(post['secure_url'])

    @http.route(
        '/iugu/checkout/redirect', type='http', website=True,
        auth='none', methods=['GET', 'POST'])
    def iugu_checkout_redirect(self, **post):
        post = post
        # Adiciona a url da fatura no session para ser renderizado 
        # no template dentro do iframe
        if 'secure_url' in post:
            request.session['secure_url'] = post.get('secure_url')
            return redirect('/payment/redirect-iugu') # 1
        
    @http.route('/payment/redirect-iugu', auth='public',type='http' ,website=True) # 1
    def index(self, **kw):
        # View responsável por renderizar o iframe contendo a fatura.
        # url informada no request.session acima que será renderizada 
        # dentro do src do iframe
        return http.request.render("payment_trustcode.redirect_message")