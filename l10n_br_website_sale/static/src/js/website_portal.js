odoo.define('br_website_portal_my_account.address', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');

    publicWidget.registry.BrWebsiteMyAccount = publicWidget.Widget.extend({
        selector: '.l10n_br_public_contact_form',
        events: {
            'change #checkbox_responsible_license': 'onChangeCheckboxResponsibleLicense',
        },
        init: function (parent, options) {
            this._super(parent, options);
        },

        start: function() {
            this.onChangeCheckboxResponsibleLicense();
        },

        onChangeCheckboxResponsibleLicense: function() {
            var checkBox = document.getElementById("checkbox_responsible_license");
            var licence_holder_data = document.getElementById("lincese_checkbox_div");
            if (checkBox){
                if (checkBox.checked) {
                    licence_holder_data.style.display = "none";
                } else {
                    licence_holder_data.style.display = "contents";
                }
            }
        },
    });

    return publicWidget.registry.BrWebsiteMyAccount;

});
