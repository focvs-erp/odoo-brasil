odoo.define("payment_trustcode.Customize", function (require) {
    "use strict";

    require("web.dom_ready");

    // Pega o id do span onde está definido a url de
    // redirecionamento para pagamento.
    var span = $("#payment_span");

    // Verifica se o elemento existe e então
    // redirecionamento para a tela de pagamento da Iugu
    if (span.length) {
        // Pega o id do element onde será mostrado o contador
        var countdown = document.getElementById('payment_countdown')
        var timeleft = 3; // Tempo do contador de 3 segundos

        var downloadTimer = setInterval(function () {
            
            if (timeleft <= 0) {
                clearInterval(downloadTimer);
                // Redioreciona para faturamento quando o contador finalizar
                window.location.href = span.text();
            } else {
                countdown.innerHTML = 'Você será redirecionado em... ' + timeleft;
            }
            timeleft -= 1;

        }, 1000);
    }

});