odoo.define('payment_paystack.payment_alert_hide', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    publicWidget.registry.PaymentAlertHide = publicWidget.Widget.extend({
        selector: '.alert.alert-success, .alert.alert-danger',
        start: function () {
            const timeout = this.$el.hasClass('alert-success') ? 5000 : 15000; // 5s for success, 15s for error
            setTimeout(() => {
                this.$el.fadeOut('slow', () => {
                    this.$el.remove(); // fully remove after fade
                });
            }, timeout);
        },
    });
});
