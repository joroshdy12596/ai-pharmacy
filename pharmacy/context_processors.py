from django.conf import settings


def guest_contact(request):
    return {'whatsapp_number': settings.WHATSAPP_NUMBER}
