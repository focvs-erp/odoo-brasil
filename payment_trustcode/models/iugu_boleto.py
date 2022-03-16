import re
import logging
import datetime
import json
import requests

from odoo import api, fields, models
from odoo.http import request
from odoo.exceptions import UserError
from werkzeug import urls
from requests.auth import HTTPBasicAuth

_logger = logging.getLogger(__name__)
odoo_request = request

try:
    import iugu
except ImportError:
    _logger.exception("Não é possível importar iugu")

with open('/mnt/extras_addons/odoo-brasil/payment_trustcode/models/appsettings.json') as file:
	appsettings = json.load(file)

class IuguBoleto(models.Model):
    _inherit = "payment.acquirer"

    def _default_return_url(self):
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        return "%s%s" % (base_url, "/payment/process")

    provider = fields.Selection(selection_add=[("iugu", "Iugu")], ondelete = { 'iugu' : 'set default' })
    iugu_api_key = fields.Char("Iugu Api Token")
    return_url = fields.Char(
        string="Url de Retorno", default=_default_return_url, size=300
    )

    def iugu_form_generate_values(self, values):
        """ Função para gerar HTML POST do Iugu """
        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        )

        partner_id = values.get('billing_partner')
        
        # AX4B - ECM_0009 - Confirmar o pedido de compras
        order = self.env['sale.order'].search([('name','=', values['reference'].split("-")[0])])
        # AX4B - ECM_0009 - Confirmar o pedido de compras

        today = datetime.date.today()

        invoice_data = {
            "email": partner_id.email,
            "due_date": today.strftime('%Y-%m-%d'),
            "return_url": urls.url_join(base_url, "/shop/confirmation"),
            "notification_url": urls.url_join(  # ngrok_url
                base_url, "/iugu/notificacao/"
            ),
            # AX4B - ECM_0009 - Confirmar o pedido de compras
            "items": self.get_items(order),
            "custom_variables": self.get_custom_variables(order),
            # AX4B - ECM_0009 - Confirmar o pedido de compras

            "payer": {
                "name": partner_id.name,
                "cpf_cnpj": partner_id.l10n_br_cnpj_cpf,
                "address": {
                    "street": partner_id.street,
                    "city": partner_id.city_id.name,
                    "number": partner_id.l10n_br_number,
                    "zip_code": re.sub('[^0-9]', '', partner_id.zip or ''),
                },
            },
        }

        result = self.create(invoice_data)          
        if "errors" in result:
            if isinstance(result["errors"], str):
                msg = result['errors']
            else:
                msg = "\n".join(
                    ["A integração com IUGU retornou os seguintes erros"] +
                    ["Field: %s %s" % (x[0], x[1][0])
                     for x in result['errors'].items()])
            raise UserError(msg)

        acquirer_reference = result.get("id")
        payment_transaction_id = self.env['payment.transaction'].search(
            [("reference", "=", values['reference'])])

        payment_transaction_id.write({
            "acquirer_reference": acquirer_reference,
            "invoice_url": result['secure_url'],
        })

        url = result.get("secure_url")
        # AX4B - ECM_0009 - Confirmar o pedido de compras
        order.write({'invoice_code': result.get("id")})
        # AX4B - ECM_0009 - Confirmar o pedido de compras
        return {
            "checkout_url": urls.url_join(
                base_url, "/iugu/checkout/redirect"),
            "secure_url": url
        }

    # AX4B - ECM_0009 - Confirmar o pedido de compras
    def get_items(self, order):
        items = []
        for line in order.order_line:
            items.append({
                "description": line.product_id.name,
                "quantity": int(line.product_uom_qty),
                "price_cents": int(line.product_id.list_price * 100)
            })
        return items

    def get_custom_variables(self, order):
        custom_variables = [{
            "name": "Valor Total",
            "value": "R$ {0:.2f}".format(order.amount_total).replace('.',',')
        },{
            "name": "Pedido",
            "value": order.display_name
        }]
        return custom_variables
    # AX4B - ECM_0009 - Confirmar o pedido de compras

    def create(self, data):
        return self.base_request(self.make_url(['invoices']), "POST", data)

    def make_url(self, paths):
        url = appsettings['iugu']['URL']
        for path in paths:           
            url = url + '/' + path
        return url

    def headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def base_request(self, url, method, data={}):
        try:
            response = requests.request(method, url,
                                        auth=HTTPBasicAuth(self.iugu_api_key, ''),
                                        data=json.dumps(data),
                                        headers=self.headers())
            return json.loads(response.content.decode('utf-8'))
        except Exception as error:
            raise

class TransactionIugu(models.Model):
    _inherit = "payment.transaction"

    invoice_url = fields.Char(string="Fatura IUGU", size=300)

    @api.model
    def _iugu_form_get_tx_from_data(self, data):
        acquirer_reference = data.get("data[id]")
        tx = self.search([("acquirer_reference", "=", acquirer_reference)])
        return tx[0]

    def _iugu_form_validate(self, data):
        status = data.get("data[status]")

        if status in ('paid', 'partially_paid', 'authorized'):
            self._set_transaction_done()
            return True
        elif status == 'pending':
            self._set_transaction_pending()
            return True
        else:
            self._set_transaction_cancel()
            return False
