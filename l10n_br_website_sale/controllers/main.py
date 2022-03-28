import re
from odoo import http, tools, _
from odoo.http import request
from werkzeug.exceptions import Forbidden
import odoo.addons.website_sale.controllers.main as main
from typing import Dict, List
from validate_docbr import CPF, CNPJ
# from odoo.addons.br_base.tools.fiscal import validate_cnpj, validate_cpf
from odoo.addons.portal.controllers.portal import CustomerPortal


class L10nBrWebsiteSale(main.WebsiteSale):

    def _get_mandatory_billing_fields(self):
        res = super(L10nBrWebsiteSale, self)._get_mandatory_billing_fields()
        res.remove("city")
        return res + [
            "l10n_br_cnpj_cpf",
            "zip",
            "l10n_br_number",
            "l10n_br_district",
            "state_id",
            "city_id"
        ]

    def _get_mandatory_shipping_fields(self):
        res = super(L10nBrWebsiteSale, self)._get_mandatory_shipping_fields()
        res.remove("city")
        return res + [
            "zip",
            "l10n_br_number",
            "l10n_br_district",
            "state_id",
            "city_id"
        ]

    @http.route(
        ["/shop/get_cities"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def get_cities_json(self, state_id):
        if state_id and state_id.isdigit():
            cities = (
                request.env["res.city"]
                .sudo()
                .search([("state_id", "=", int(state_id))])
            )
            return [(city.id, city.name) for city in cities]
        return []

    @http.route(
        ["/shop/get_states"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def get_states_json(self, country_id):
        if country_id and country_id.isdigit():
            states = (
                request.env["res.country.state"]
                .sudo()
                .search([("country_id", "=", int(country_id))])
            )
            return [(state.id, state.name) for state in states]
        return []

    def validate_cpf_cnpj(self, cnpj_cpf):
        cpf = CPF()
        cnpj = CNPJ()
        if '/' in cnpj_cpf:
            if not cnpj.validate(cnpj_cpf):
                return False
        else:
            if not cpf.validate(cnpj_cpf):
                return False
        return True

    def checkout_form_validate(self, mode, all_form_values, data):
        errors, error_msg = super(
            L10nBrWebsiteSale, self
        ).checkout_form_validate(mode, all_form_values, data)
        cnpj_cpf = data.get("l10n_br_cnpj_cpf", "0")
        email = data.get("email", False)
        estado = data.get("state_id", False)
        nome = data.get("name", '')

        if not self.validate_cpf_cnpj(cnpj_cpf):
            errors["l10n_br_cnpj_cpf"] = u"invalid"
            error_msg.append(("CPF/CNPJ inválido"))
        
        if not estado:
            errors["state_id"] = u"invalid"
      
        partner_id = data.get("partner_id", False)
        if cnpj_cpf:
            domain = [("l10n_br_cnpj_cpf", "=", cnpj_cpf)]
            if partner_id and mode[0] == "edit":
                domain.append(("id", "!=", partner_id))
            existe = request.env["res.partner"].sudo().search_count(domain)
            if existe > 0:
                errors["l10n_br_cnpj_cpf"] = u"invalid"
                error_msg.append(("CPF/CNPJ já cadastrado"))
        if email:
            domain = [("email", "=", email)]
            if partner_id and mode[0] == "edit":
                domain.append(("id", "!=", partner_id))
            existe = request.env["res.partner"].sudo().search_count(domain)
            if existe > 0:
                errors["email"] = u"invalid"
                error_msg.append(("E-mail já cadastrado"))

        # AX4B - LICENSE HOLDER
        if data.get('email_responsible', False) and not tools.single_email_re.match(data.get('email_responsible')):
            errors["email_responsible"] = u"invalid"
            error_msg.append(_('Invalid email! Please enter a valid invoice owner\'s email address. '))

        if data.get('email_responsible_for_license', False) and not tools.single_email_re.match(data.get('email_responsible_for_license')):
            errors["email_responsible_for_license"] = u"invalid"
            error_msg.append(_('Invalid email! Please enter a valid license holder email address.'))
        # AX4B - LICENSE HOLDER    
        return errors, error_msg

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values, errors, error_msg = super(
            L10nBrWebsiteSale, self
        ).values_postprocess(order, mode, values, errors, error_msg)
        new_values["l10n_br_cnpj_cpf"] = values.get("l10n_br_cnpj_cpf", None)
        new_values["company_type"] = values.get("company_type", None)
        is_comp = (
            False if values.get("company_type", None) == "person" else True
        )
        new_values["is_company"] = is_comp
        if "city_id" in values and values["city_id"] != "":
            new_values["city_id"] = int(values.get("city_id", 0))
        if "state_id" in values and values["state_id"] != "":
            new_values["state_id"] = int(values.get("state_id", 0))
        if "country_id" in values and values["country_id"] != "":
            new_values["country_id"] = int(values.get("country_id", 0))
        new_values["l10n_br_number"] = values.get("l10n_br_number", None)
        new_values["street2"] = values.get("street2", None)
        new_values["l10n_br_district"] = values.get("l10n_br_district", None)
        # new_values['child_ids'] = self.get_child_ids(values)

        return new_values, errors, error_msg

    # @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    # def address(self, **kw):
    #     Partner = request.env['res.partner'].with_context(show_address=1).sudo()
    #     order = request.website.sale_get_order()

    #     redirection = self.checkout_redirection(order)
    #     if redirection:
    #         return redirection

    #     mode = (False, False)
    #     can_edit_vat = False
    #     values, errors = {}, {}

    #     partner_id = int(kw.get('partner_id', -1))

    #     # IF PUBLIC ORDER
    #     if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
    #         mode = ('new', 'billing')
    #         can_edit_vat = True
    #     # IF ORDER LINKED TO A PARTNER
    #     else:
    #         if partner_id > 0:
    #             if partner_id == order.partner_id.id:
    #                 mode = ('edit', 'billing')
    #                 can_edit_vat = order.partner_id.can_edit_vat()
    #             else:
    #                 shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
    #                 if order.partner_id.commercial_partner_id.id == partner_id:
    #                     mode = ('new', 'shipping')
    #                     partner_id = -1
    #                 elif partner_id in shippings.mapped('id'):
    #                     mode = ('edit', 'shipping')
    #                 else:
    #                     return Forbidden()
    #             if mode and partner_id != -1:
    #                 values = Partner.browse(partner_id)
    #         elif partner_id == -1:
    #             mode = ('new', 'shipping')
    #         else: # no mode - refresh without post?
    #             return request.redirect('/shop/checkout')

    #     # IF POSTED
    #     if 'submitted' in kw:
    #         pre_values = self.values_preprocess(order, mode, kw)
    #         errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
    #         post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

    #         if errors:
    #             errors['error_message'] = error_msg
    #             values = kw
    #             values['child_ids'] = self.get_child_ids(kw)
    #         else:
    #             partner_id = self._checkout_form_save(mode, post, kw)
    #             if mode[1] == 'billing':
    #                 order.partner_id = partner_id
    #                 order.with_context(not_self_saleperson=True).onchange_partner_id()
    #                 # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
    #                 order.partner_invoice_id = partner_id
    #                 if not kw.get('use_same'):
    #                     kw['callback'] = kw.get('callback') or \
    #                         (not order.only_services and (mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
    #             elif mode[1] == 'shipping':
    #                 order.partner_shipping_id = partner_id

    #             # TDE FIXME: don't ever do this
    #             order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
    #             if not errors:
    #                 return request.redirect(kw.get('callback') or '/shop/confirm_order')

    #     render_values = {
    #         'website_sale_order': order,
    #         'partner_id': partner_id,
    #         'mode': mode,
    #         'checkout': values,
    #         'can_edit_vat': can_edit_vat,
    #         'error': errors,
    #         'callback': kw.get('callback'),
    #         'only_services': order and order.only_services,
    #     }
    #     render_values.update(self._get_country_related_render_values(kw, render_values))
    #     return request.render("website_sale.address", render_values)

    def get_child_ids(self, vals):
        if 'child_ids' in vals:
            return self.build_child_ids_partner(vals)
        else:
            return self.build_child_ids_kw(vals)

    
    def build_child_ids_partner(self, values):
        child_ids = []
        for child in filter(lambda ch : ch['website_contact'], values['child_ids']):
            child_ids.append({
                'name': child.name,
                'phone':child.phone,
                'email':child.email,
                'website_contact': True
            })

        return child_ids

    def build_child_ids_kw(self, values):
        child_ids = []
        child_ids.append({
            'name': values.get('name_responsible', ''),
            'phone':values.get('phone_responsible', ''),
            'email':values.get('email_responsible', ''),
            'website_contact': True
        })
        child_ids.append({
            'name': values.get('name_responsible_for_license', ''),
            'phone':values.get('phone_responsible_for_license', ''),
            'email':values.get('email_responsible_for_license',''),
            'website_contact': True
        })

        return child_ids


    # AX4B - LICENSE HOLDER
    def _create_partner_contact(self, partner_id, all_values):
        Partner = request.env["res.partner"].sudo()

        if self._verify_who_is_resposible(all_values, ['name_responsible','email_responsible','phone_responsible']):
            partner_responsible = {
                'name': all_values.get('name_responsible'),
                'email': all_values.get('email_responsible'),
                'phone': all_values.get('phone_responsible'),
                'parent_id': partner_id.id,
                'website_contact': True,
                'responsible_billing': True,
                'responsible_license': True if all_values.get('is_licence_holder_input', None) or not all_values.get('is_licence_holder_input', False) and not self._verify_who_is_resposible(all_values, [
                    'name_responsible_for_license', 
                    'email_responsible_for_license',
                    'phone_responsible_for_license']) else False
            }
            partner_responsible['type'] = 'responsible' if partner_responsible.get('responsible_license', False) else 'contact'
            Partner.create(partner_responsible)

        if not all_values.get('is_licence_holder_input', None):
            if self._verify_who_is_resposible(all_values, [
                'name_responsible_for_license', 
                'email_responsible_for_license',
                'phone_responsible_for_license']):
                partner_responsible = {
                    'name': all_values.get('name_responsible_for_license'),
                    'email': all_values.get('email_responsible_for_license'),
                    'phone': all_values.get('phone_responsible_for_license'),
                    'parent_id': partner_id.id,
                    'type': 'responsible',
                    'website_contact': True,
                    'responsible_billing': True if not self._verify_who_is_resposible(all_values, ['name_responsible','email_responsible','phone_responsible']) else False,
                    'responsible_license': True
                }

                Partner.create(partner_responsible)

    # AX4B - LICENSE HOLDER
    def _checkout_form_save(self, mode, checkout, all_values):
        Partner = request.env["res.partner"]
        if mode[0] == "new":
            partner_id = Partner.sudo().create(checkout)

            # AX4B - LICENSE HOLDER
            self._create_partner_contact(partner_id, all_values)
            # AX4B - LICENSE HOLDER

        elif mode[0] == "edit":
            partner_id = int(all_values.get("partner_id", 0))
            if partner_id:
                # double check
                order = request.website.sale_get_order()
                shippings = Partner.sudo().search(
                    [
                        (
                            "id",
                            "child_of",
                            order.partner_id.commercial_partner_id.ids,
                        )
                    ]
                )
                if (
                    partner_id not in shippings.mapped("id")
                    and partner_id != order.partner_id.id
                ):
                    return Forbidden()
                
                checkout.pop('child_ids')

                Partner.browse(partner_id).sudo().write(checkout)

                request.env['res.partner'].write_partner_contact(partner_id, all_values, 'checkbox_responsible_license'== False)

        return partner_id

    @http.route()
    def address(self, **kw):
        result = super(L10nBrWebsiteSale, self).address(**kw)
        partner_id = 0
        if "partner_id" in result.qcontext:
            partner_id = result.qcontext["partner_id"]
        if partner_id > 0:
            partner_id = request.env["res.partner"].sudo().browse(partner_id)
            result.qcontext["city"] = partner_id.city_id
            result.qcontext["state"] = partner_id.state_id
        if "city_id" in kw and kw["city_id"]:
            result.qcontext["city"] = request.env['res.city'].browse(kw["city_id"])
        
        # if 'checkout' in result.qcontext and 'child_ids' not in result.qcontext['checkout']:
            # result.qcontext["checkout"]["child_ids"] = self.get_child_ids(kw)
        result.qcontext["child_ids"] = self.get_child_ids(partner_id if 'child_ids' in result.qcontext['checkout'] else kw)

        return result
        

           


    @http.route(
        ["/shop/zip_search"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def search_zip_json(self, zip):
        if zip and len(zip) >= 8:
            cep = re.sub("[^0-9]", "", zip)
            vals = (
                request.env["res.partner"].sudo().search_address_by_zip(cep)
            )

            if vals:
                return {
                    "sucesso": True,
                    "street": vals["street"],
                    "l10n_br_district": vals["l10n_br_district"],
                    "city_id": vals["city_id"],
                    "state_id": vals["state_id"],
                    "country_id": vals["country_id"],
                }

        return {"sucesso": False}
