odoo.define("payment_trustcode.Customize", function (require) {
    "use strict";

    require("web.dom_ready");

    // Pega o id do span onde está definido a url de
    // redirecionamento para pagamento.
    var span = $("#span_id");

    // Verifica se o elemento existe e então
    // redirecionamento para a tela de pagamento da Iugu
    if (span.length) {

        var countdown = document.getElementById('countdown')
        var timeleft = 5;

        var downloadTimer = setInterval(function () {
            
            if (timeleft <= 0) {
                clearInterval(downloadTimer);
                window.location.href = span.text();
            } else {
                countdown.innerHTML = 'Você será redirecionado em ... ' + timeleft;
            }
            timeleft -= 1;

        }, 1000);
    }

});