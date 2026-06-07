from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ServiceProvider, Booking
from .forms import BookingForm

def services_list(request):
    services = ServiceProvider.objects.filter(is_approved=True)
    return render(request, 'services/list.html', {'services': services})

@login_required
def book_service(request, provider_id):
    provider = get_object_or_404(ServiceProvider, id=provider_id, is_approved=True)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.provider = provider
            booking.customer_user = request.user
            booking.save()
            
            messages.success(request, f"Successfully booked {provider.name}! You can view the status in your dashboard.")
            return redirect('dashboard')
    else:
        # Pre-fill form with logged in user details if possible
        initial_data = {
            'name': request.user.username,
            'email': request.user.email
        }
        form = BookingForm(initial=initial_data)

    return render(request, 'services/book_service.html', {
        'provider': provider,
        'form': form
    })

@login_required
def update_booking_status(request, booking_id, status):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Ensure only the provider can update it
    if hasattr(request.user, 'serviceprovider') and booking.provider == request.user.serviceprovider:
        if status in dict(Booking.STATUS_CHOICES).keys():
            booking.status = status
            booking.save()
            messages.success(request, f"Booking status updated to {status}.")
        else:
            messages.error(request, "Invalid status.")
    else:
        messages.error(request, "You are not authorized to update this booking.")
        
    return redirect('dashboard')