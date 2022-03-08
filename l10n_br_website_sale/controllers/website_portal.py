import re
from odoo import http, tools, _
from odoo.http import request
from werkzeug.exceptions import Forbidden
import odoo.addons.website_sale.controllers.main as main
from odoo.addons.portal.controllers.portal import CustomerPortal

class BrWebsiteMyAccount(CustomerPortal):
    # def _get_mandatory_billing_fields(self):
    #     res = super(BrWebsiteMyAccount, self)._get_mandatory_billing_fields()
    #     return res + [
    #         "name_responsible",
    #         "email_responsible",
    #         "phone_responsible",
    #         "name_responsible_for_license",
    #         "email_responsible_for_license",
    #         "phone_responsible_for_license",
    #         "is_licence_holder_input",
    #     ]

    @http.route(["/my/account"], type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        if "zip" in post:
            post["zipcode"] = post.pop("zip")
        return super(BrWebsiteMyAccount, self).account(
            redirect=redirect, **post
        )
