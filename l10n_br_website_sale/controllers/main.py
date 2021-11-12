import re
from odoo import http, tools, _
from odoo.http import request
from werkzeug.exceptions import Forbidden
import odoo.addons.website_sale.controllers.main as main
from typing import Dict, List

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

    def checkout_form_validate(self, mode, all_form_values, data):
        errors, error_msg = super(
            L10nBrWebsiteSale, self
        ).checkout_form_validate(mode, all_form_values, data)
        cnpj_cpf = data.get("l10n_br_cnpj_cpf", "0")
        email = data.get("email", False)


        # TODO Validar campos
        # if cnpj_cpf and len(cnpj_cpf) == 18:
        #     # if not validate_cnpj(cnpj_cpf):
        #     errors["l10n_br_cnpj_cpf"] = u"invalid"
        #     error_msg.append(('CNPJ Inválido!'))
        # elif cnpj_cpf and len(cnpj_cpf) == 14:
        #     # if not validate_cpf(cnpj_cpf):
        #     errors["l10n_br_cnpj_cpf"] = u"invalid"
        #     error_msg.append(('CPF Inválido!'))
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

        return new_values, errors, error_msg

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

    # def _verify_partner_resposible_fields(self, all_values):
    #     return any([all_values.get('name_responsible', False), all_values.get('email_responsible', False), all_values.get('phone_responsible', False)])

    # def _verify_partner_resposible_license_fields(self, all_values):
    #     return any([all_values.get('name_responsible_for_license', False), all_values.get('email_responsible_for_license', False), all_values.get('phone_responsible_for_license', False)])
        
    def _verify_who_is_resposible(self, all_values: Dict, attr_list: List) -> bool:
        return any([{x: all_values[x] for x in attr_list}.values()])


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
                if all_values.get('is_licence_holder_input', False):
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
                    'responsible_license': True if all_values.get('is_licence_holder_input', None) or not all_values.get('is_licence_holder_input', False) and not self._verify_who_is_resposible(all_values, [
                        'name_responsible_for_license', 
                        'email_responsible_for_license', 
                        'phone_responsible_for_license']) else False
                    }
                    )
                Partner.create(partner_responsible)

        if not all_values.get('is_licence_holder_input', False):
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

                Partner.browse(partner_id).sudo().write(checkout)

                self._write_partner_contact(partner_id, all_values)

        return partner_id

    @http.route()
    def address(self, **kw):
        result = super(L10nBrWebsiteSale, self).address(**kw)
        partner_id = 0
        if "partner_id" in result.qcontext:
            partner_id = result.qcontext["partner_id"]
        if partner_id > 0:
            partner_id = request.env["res.partner"].sudo().browse(partner_id)
            result.qcontext["city"] = partner_id.city_id.id
            result.qcontext["state"] = partner_id.state_id.id
        if "city_id" in kw and kw["city_id"]:
            result.qcontext["city"] = kw["city_id"]
        return result

    @http.route(
        ["/shop/zip_search"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def search_zip_json(self, zip):
        if len(zip) >= 8:
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


class BrWebsiteMyAccount(CustomerPortal):

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

    @http.route(["/my/account"], type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        if "zip" in post:
            post["zipcode"] = post.pop("zip")
        return super(BrWebsiteMyAccount, self).account(
            redirect=redirect, **post
        )

