odoo.define("payment_trustcode.Customize", function (require) {
    "use strict";

    require("web.dom_ready");

    // Pega o id do span onde está definido a url de
    // redirecionamento para pagamento.
    let span = $("#payment_span");

    // Verifica se o elemento existe e então
    // redirecionamento para a tela de pagamento da Iugu
    if (span.length) {
        // Pega o id do element onde será mostrado o contador
        let countdown = document.getElementById('payment_countdown')
        let timeleft = 2; // Tempo do contador de 3 segundos

        let downloadTimer = setInterval(function () {
            
            if (timeleft <= 0) {
                clearInterval(downloadTimer);
                // Redioreciona para faturamento quando o contador finalizar
                window.location.href = span.text();
            } else {
                countdown.innerHTML = 'Redirect in... ' + timeleft;
            }
            timeleft -= 1;

        }, 1000);
    }

});