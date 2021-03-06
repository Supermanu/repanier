# -*- coding: utf-8
from django.forms import NumberInput
import repanier.apps


class MoneyWidget(NumberInput):
    template_name = 'repanier/widgets/money.html'

    def __init__(self, attrs=None):
        super(MoneyWidget, self).__init__(attrs=attrs)

    def get_context(self, name, value, attrs):
        context = super(MoneyWidget, self).get_context(name, value, attrs)
        context['repanier_currency_after'] = repanier.apps.REPANIER_SETTINGS_AFTER_AMOUNT
        context['repanier_currency_str'] = repanier.apps.REPANIER_SETTINGS_CURRENCY_DISPLAY
        return context

    # class Media:
    #     css = {
    #         'all': ('css/checkbox_widget.css',)
    #     }
