# -*- coding: utf-8
from __future__ import unicode_literals

import threading
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.forms import Textarea
from django.http import Http404
from django.shortcuts import render
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from djng.forms import NgFormValidationMixin

from repanier.models import Customer, Staff
from repanier.tools import send_email
from repanier.views.forms import RepanierForm


class MembersContactForm(RepanierForm):
    recipient = forms.CharField(label=_('Recipient(s)'))
    your_email = forms.EmailField(label=_('Your Email'))
    subject = forms.CharField(label=_('Subject'), max_length=100)
    message = forms.CharField(label=_('Message'), widget=Textarea)

    def __init__(self, *args, **kwargs):
        super(MembersContactForm, self).__init__(*args, **kwargs)


class MembersContactValidationForm(NgFormValidationMixin, MembersContactForm):
    pass


@login_required()
@csrf_protect
@never_cache
def send_mail_to_all_members_view(request):
    from repanier.apps import REPANIER_SETTINGS_DISPLAY_WHO_IS_WHO
    if not REPANIER_SETTINGS_DISPLAY_WHO_IS_WHO:
        raise Http404
    if request.user.is_staff:
        raise Http404
    is_coordinator = request.user.is_superuser or request.user.is_staff or Staff.objects.filter(
        customer_responsible_id=request.user.customer.id, is_coordinator=True, is_active=True
    ).order_by('?').first() is not None
    if request.method == 'POST':
        form = MembersContactValidationForm(request.POST)  # A form bound to the POST data
        user_customer = Customer.objects.filter(
            id=request.user.customer.id,
            is_active=True
        ).order_by('?').first()
        if form.is_valid() and user_customer is not None:  # All validation rules pass
            to_email_customer = []
            if is_coordinator:
                qs = Customer.objects.filter(is_active=True, represent_this_buyinggroup=False, may_order=True)
            else:
                qs = Customer.objects.filter(is_active=True, accept_mails_from_members=True,
                                             represent_this_buyinggroup=False, may_order=True)
            for customer in qs:
                if customer.user_id != request.user.id:
                    to_email_customer.append(customer.user.email)
                # if customer.email2 is not None and customer.email2 != EMPTY_STRING:
                #     to_email_customer.append(customer.email2)
            to_email_customer.append(request.user.email)
            email = EmailMessage(
                strip_tags(form.cleaned_data.get('subject')),
                strip_tags(form.cleaned_data.get('message')),
                from_email=request.user.email,
                cc=to_email_customer
            )
            # send_email(email=email, from_name=user_customer.long_basket_name)
            # thread.start_new_thread(send_email,(email, user_customer.long_basket_name, True))
            t = threading.Thread(target=send_email, args=(email, user_customer.long_basket_name, True))
            t.start()
            email = form.fields["your_email"]
            email.initial = request.user.email
            email.widget.attrs['readonly'] = True
            recipient = form.fields["recipient"]
            if is_coordinator:
                recipient.initial = _("All members as coordinator")
            else:
                recipient.initial = _("All members accepting to show they mail address")
            recipient.widget.attrs['readonly'] = True
            return render(request, "repanier/send_mail_to_all_members.html",
                          {'form': form, 'update': '2'})
    else:
        form = MembersContactValidationForm()  # An unbound form
        email = form.fields["your_email"]
        email.initial = request.user.email
        email.widget.attrs['readonly'] = True
        recipient = form.fields["recipient"]
        if is_coordinator:
            recipient.initial = _("All members as coordinator")
        else:
            recipient.initial = _("All members accepting to show they mail address")
        recipient.widget.attrs['readonly'] = True

    return render(request, "repanier/send_mail_to_all_members.html",
                  {'form': form, 'coordinator': is_coordinator})
