import re
from odoo import http, tools, _
from odoo.http import request
from werkzeug.exceptions import Forbidden
from typing import Dict, List
import odoo.addons.website_sale.controllers.main as main
from odoo.addons.portal.controllers.portal import CustomerPortal

class BrWebsiteMyAccount(CustomerPortal):
    def update_client(self, post):
        fields_billing = ['name_responsible', 'email_responsible', 'phone_responsible', 'name_responsible_for_license', 'email_responsible_for_license', 'phone_responsible_for_license']
        fields_license = ['checkbox_responsible_license']
        if 'name_responsible' in post:
            partner = request.env['res.users'].search([('id', '=', request.uid)]).partner_id.id
            self._write_partner_contact(partner, post)

            for i in fields_billing:
                del post[i]
            if 'checkbox_responsible_license' in post:
                for i in fields_license:
                    del post[i]


    MANDATORY_BILLING_FIELDS = [
        "name",
        "phone",
        "email",
        "street",
        "l10n_br_cnpj_cpf",
        "l10n_br_number",
        "l10n_br_district",
        "zipcode",
        "company_type",
        "city_id",
        "state_id",
        "country_id",
    ]
    OPTIONAL_BILLING_FIELDS = ["street2"]

    def _verify_who_is_resposible(self, all_values: Dict, attr_list: List) -> bool:
        return any({x: all_values.get(x, False) for x in attr_list}.values())

    # AX4B - LICENSE HOLDER
    def _write_partner_contact(self, partner_id, all_values):
        Partner = request.env["res.partner"].sudo()

        partner_responsible = {
            'name': all_values.get('name_responsible', False),
            'email': all_values.get('email_responsible', False),
            'phone': all_values.get('phone_responsible', False),
        }

        if self._verify_who_is_resposible(all_values, ['name_responsible','email_responsible','phone_responsible']):
            respo_billing = Partner.search([("responsible_billing", "=", True), ('parent_id', '=', partner_id)])
            if respo_billing.exists():
                if all_values.get('checkbox_responsible_license', False):
                    Partner.search([("responsible_billing", "=", False), ("responsible_license", "=", True), ('parent_id', '=', partner_id)]).unlink()
                    partner_responsible.update({'responsible_license': True, 'type': 'responsible'})
                    respo_billing.write(partner_responsible)

                else:
                    respo_billing.write(partner_responsible)
            else:
                partner_responsible.update({
                    'parent_id': partner_id,
                    'type': 'responsible',
                    'website_contact': True,
                    'responsible_billing': True,
                    'responsible_license': True if all_values.get('checkbox_responsible_license', None) or not all_values.get('checkbox_responsible_license', False) and not self._verify_who_is_resposible(all_values, [
                        'name_responsible_for_license', 
                        'email_responsible_for_license', 
                        'phone_responsible_for_license']) else False
                    }
                    )
                Partner.create(partner_responsible)

        if not all_values.get('checkbox_responsible_license', False):
            partner_responsible = {
                'name': all_values.get('name_responsible_for_license', False),
                'email': all_values.get('email_responsible_for_license', False),
                'phone': all_values.get('phone_responsible_for_license', False),
            }
            if self._verify_who_is_resposible(all_values, [
                'name_responsible_for_license', 
                'email_responsible_for_license',
                'phone_responsible_for_license']):

                respo_license = Partner.search([("responsible_license", "=", True), ('parent_id', '=', partner_id)])

                if respo_license.exists() and respo_license[0].responsible_billing == False:
                    respo_license.write(partner_responsible)

                else:
                    if respo_license.exists() and respo_license[0].responsible_billing == True:
                        respo_license.write({'type': 'contact','responsible_license': False})

                    partner_responsible.update({
                        'parent_id': partner_id,
                        'type': 'responsible',
                        'website_contact': True,
                        'responsible_billing': False,
                        'responsible_license': True
                    })
                    Partner.create(partner_responsible)
            else:
                Partner.search([("responsible_license", "=", True), ("responsible_billing", "=", False), ('parent_id', '=', partner_id)]).unlink()

    @http.route(["/my/account"], type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        self.update_client(post)
        if "zip" in post:
            post["zipcode"] = post.pop("zip")
        return super(BrWebsiteMyAccount, self).account(
            redirect=redirect, **post
        )
