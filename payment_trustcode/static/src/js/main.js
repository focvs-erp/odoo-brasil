"use strict";
odoo.define("payment_trustcode.Customize", function (require) {

    require("web.dom_ready");

    var iframe = document.getElementById("payment-iugu");
    console.log(iframe)

    // var submit_form = iframe.contentWindow.document.getElementById("submit-form");
    // console.log(iframe)
    // console.log(submit_form);

    // if (submit_form) {
    //     submit_form.addEventListener("click", function (e) {
    //         window.location.href = `http://localhost:8069/payment/process`;
    //     });
    // }
    
});
