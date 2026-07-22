from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .forms import GuestPrescriptionRequestForm
from .models import GuestPrescriptionRequest
from .telegram_utils import send_telegram_message


def guest_prescription_upload(request):
    """Public, no-login page where a guest uploads a photo of their
    prescription (روشتة) and leaves their name/phone so staff can reach
    them, then gets a link to check back for the reply."""
    if request.method == 'POST':
        form = GuestPrescriptionRequestForm(request.POST, request.FILES)
        if form.is_valid():
            guest_request = form.save()

            send_telegram_message(
                f'📋 روشتة جديدة #{guest_request.id}\n'
                f'الاسم: {guest_request.guest_name}, الموبايل: {guest_request.guest_phone}\n'
                f'رابط المراجعة: {request.build_absolute_uri(reverse("pharmacy:staff_prescription_reply", args=[guest_request.id]))}'
            )

            return redirect('pharmacy:guest_prescription_status', token=guest_request.tracking_token)
    else:
        form = GuestPrescriptionRequestForm()

    return render(request, 'pharmacy/public/prescription_upload.html', {'form': form})


def guest_prescription_status(request, token):
    """Public tracking page - the guest can bookmark/revisit this to check
    whether staff has replied yet."""
    guest_request = get_object_or_404(GuestPrescriptionRequest, tracking_token=token)
    return render(request, 'pharmacy/public/prescription_status.html', {'req': guest_request})


@login_required
def staff_prescription_queue(request):
    """Staff-facing queue of guest prescription requests, pending first."""
    pending = GuestPrescriptionRequest.objects.filter(status='PENDING')
    replied = GuestPrescriptionRequest.objects.filter(status='REPLIED')[:20]
    return render(request, 'pharmacy/staff/prescription_queue.html', {
        'pending': pending,
        'replied': replied,
    })


@login_required
def staff_prescription_reply(request, pk):
    """Staff view/reply screen for a single guest prescription request."""
    guest_request = get_object_or_404(GuestPrescriptionRequest, pk=pk)

    if request.method == 'POST':
        reply_text = request.POST.get('reply_text', '').strip()
        if reply_text:
            guest_request.reply_text = reply_text
            guest_request.status = 'REPLIED'
            guest_request.replied_at = timezone.now()
            guest_request.replied_by_username = request.user.username
            guest_request.save()
            messages.success(request, 'تم إرسال الرد للعميل / Reply saved')
            return redirect('pharmacy:staff_prescription_queue')
        messages.error(request, 'الرجاء كتابة الرد / Please write a reply')

    return render(request, 'pharmacy/staff/prescription_reply.html', {'req': guest_request})
