from odoo import http, tools, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import ValidationError

class BrWebsiteMyAccount(CustomerPortal):
    def update_client(self, post):
        responsible = ['name_responsible', 'email_responsible', 
        'name_responsible_for_license', 'email_responsible_for_license',
        'checkbox_responsible_license', 'phone_responsible', 'phone_responsible_for_license']

        if len(post) != 0:
            partner = request.env['res.users'].search([('id', '=', request.uid)]).partner_id.id
            request.env['res.partner'].write_partner_contact(partner, post, 'checkbox_responsible_license')
            
            for i in responsible:
                if i in post:
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

    @http.route(["/my/account"], type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        if "zip" in post:
            post["zipcode"] = post.pop("zip")
        return super(BrWebsiteMyAccount, self).account(
            redirect=redirect, **post
        )

    # AX4B - M_ECM_0014 - Validação dos campos ao Editar
    def details_form_validate(self, data):
        error = dict()
        error_message = []
        partner = request.env["res.partner"].sudo()

        # Validation
        for field_name in self.MANDATORY_BILLING_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'

        if not partner.validate_zip(data.get("zipcode", '')):        
            error["zip"] = u"invalid"
            error_message.append(_("Invalid zip code"))
        if not partner.validate_number(data.get("l10n_br_number", '')):        
            error["l10n_br_number"] = u"invalid"
            error_message.append(_("Invalid number"))
        if not partner.validate_phone(data.get("phone", '')):        
            error["phone"] = u"invalid"
            error_message.append(_("Invalid phone"))
        if not partner.validate_cpf_cnpj(data.get("l10n_br_cnpj_cpf", "0")):
            error["l10n_br_cnpj_cpf"] = u"invalid"
            error_message.append(_("Invalid CPF/CNPJ"))
        
        if not partner.validate_phone(data.get("phone_responsible", ''), False):        
            error["phone_responsible"] = u"invalid"
            error_message.append(_("Invalid responsible phone"))
        if not partner.validate_phone(data.get("phone_responsible_for_license", ''), False):        
            error["phone_responsible_for_license"] = u"invalid"
            error_message.append(_("Invalid responsible for license phone"))
        
        self.update_client(data)

        # email validation
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append(_('Invalid Email! Please enter a valid email address.'))

        # vat validation
        partner = request.env.user.partner_id
        if data.get("vat") and partner and partner.vat != data.get("vat"):
            if partner.can_edit_vat():
                if hasattr(partner, "check_vat"):
                    if data.get("country_id"):
                        data["vat"] = request.env["res.partner"].fix_eu_vat_number(int(data.get("country_id")), data.get("vat"))
                    partner_dummy = partner.new({
                        'vat': data['vat'],
                        'country_id': (int(data['country_id'])
                                       if data.get('country_id') else False),
                    })
                    try:
                        partner_dummy.check_vat()
                    except ValidationError:
                        error["vat"] = 'error'
            else:
                error_message.append(_('Changing VAT number is not allowed once document(s) have been issued for your account. Please contact us directly for this operation.'))

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        unknown = [k for k in data if k not in self.MANDATORY_BILLING_FIELDS + self.OPTIONAL_BILLING_FIELDS]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message
    # AX4B - M_ECM_0014 - Validação dos campos ao Editar