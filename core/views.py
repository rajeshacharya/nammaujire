from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from locations.models import Place
from services.models import ServiceProvider, Booking
from .forms import LocalUpdateSubmissionForm
from .models import EmergencyContact, LocalUpdate, OTPVerification
import random
import re


QUICK_ASKS = [
    'Plumber near me',
    'Auto to Dharmasthala',
    'Bus update',
    'Rain alert',
    'Local jobs',
    'Emergency doctor',
    'Temple event',
    'Buy and sell',
]

SERVICE_KEYWORDS = {
    'AUTO': ['auto', 'rickshaw', 'ride', 'drop', 'pickup', 'dharmasthala', 'bus stand'],
    'PLUMBER': ['plumber', 'pipe', 'water leak', 'tap', 'bathroom', 'motor'],
    'ELECTRICIAN': ['electric', 'electrician', 'current', 'power', 'wiring', 'switch', 'fan'],
    'BARBER': ['barber', 'haircut', 'shaving', 'salon'],
}

UPDATE_KEYWORDS = {
    LocalUpdate.Category.ANNOUNCEMENT: ['announcement', 'notice', 'news', 'today'],
    LocalUpdate.Category.BUS: ['bus', 'transport', 'route', 'timing', 'delay', 'stand'],
    LocalUpdate.Category.TEMPLE: ['temple', 'festival', 'pooja', 'jatre', 'dharmasthala', 'devasthana'],
    LocalUpdate.Category.HEALTH: ['health', 'doctor', 'clinic', 'hospital', 'camp', 'blood'],
    LocalUpdate.Category.FARMER: ['farmer', 'farm', 'arecanut', 'crop', 'market rate', 'krishi'],
    LocalUpdate.Category.SCHOOL: ['school', 'college', 'exam', 'holiday', 'sdm', 'class'],
    LocalUpdate.Category.PANCHAYAT: ['panchayat', 'water supply', 'road work', 'ration', 'office'],
    LocalUpdate.Category.JOB: ['job', 'work', 'helper', 'vacancy', 'kelasa', 'daily wage'],
    LocalUpdate.Category.MARKET: ['sell', 'buy', 'market', 'rent', 'second hand', 'offer'],
    LocalUpdate.Category.WEATHER: ['rain', 'weather', 'male', 'flood', 'landslide', 'alert'],
}

CONTACT_KEYWORDS = {
    EmergencyContact.Category.HEALTH: ['doctor', 'hospital', 'ambulance', 'health', 'medical', 'accident'],
    EmergencyContact.Category.POLICE: ['police', 'theft', 'fight', 'safety'],
    EmergencyContact.Category.FIRE: ['fire', 'smoke', 'burn'],
    EmergencyContact.Category.PANCHAYAT: ['panchayat', 'water', 'road', 'garbage'],
    EmergencyContact.Category.TRANSPORT: ['auto', 'taxi', 'transport', 'vehicle'],
    EmergencyContact.Category.WOMEN_CHILD: ['women', 'child', 'harassment', 'help'],
    EmergencyContact.Category.DISASTER: ['emergency', 'flood', 'landslide', 'danger', 'sos'],
}


def _tokens(query):
    return [word for word in re.split(r'[^a-z0-9]+', query.lower()) if len(word) >= 3]


def _has_any(query, keywords):
    return any(keyword in query for keyword in keywords)


def _text_filter(tokens, fields):
    query_filter = Q()
    for token in tokens:
        for field in fields:
            query_filter |= Q(**{f'{field}__icontains': token})
    return query_filter

def home(request):
    daily_highlights = LocalUpdate.published()[:4]
    emergency_contacts = EmergencyContact.objects.filter(is_active=True)[:3]
    return render(request, 'core/home.html', {
        'daily_highlights': daily_highlights,
        'home_emergency_contacts': emergency_contacts,
    })


def ask_ujire_view(request):
    query = request.GET.get('q', '').strip()
    normalized_query = query.lower()
    query_tokens = _tokens(query)

    service_filter = Q()
    for service_type, keywords in SERVICE_KEYWORDS.items():
        if _has_any(normalized_query, keywords):
            service_filter |= Q(service_type=service_type)
    service_text_filter = _text_filter(query_tokens, ['name', 'location']) if query_tokens else Q()
    if query:
        services = ServiceProvider.objects.filter(is_approved=True).filter(
            service_filter | service_text_filter
        ).order_by('-is_available', 'name')[:6]
    else:
        services = ServiceProvider.objects.filter(is_approved=True).order_by('-is_available', 'name')[:4]

    update_filter = Q()
    for category, keywords in UPDATE_KEYWORDS.items():
        if _has_any(normalized_query, keywords):
            update_filter |= Q(category=category)
    update_text_filter = _text_filter(query_tokens, ['title', 'description', 'location']) if query_tokens else Q()
    if query:
        updates = LocalUpdate.published().filter(update_filter | update_text_filter)[:8]
    else:
        updates = LocalUpdate.published()[:5]

    contact_filter = Q()
    show_all_contacts = _has_any(normalized_query, ['emergency', 'urgent', 'sos', 'help'])
    for category, keywords in CONTACT_KEYWORDS.items():
        if _has_any(normalized_query, keywords):
            contact_filter |= Q(category=category)
    if query and not show_all_contacts:
        contacts = EmergencyContact.objects.filter(is_active=True).filter(contact_filter).distinct()[:5]
    else:
        contacts = EmergencyContact.objects.filter(is_active=True)[:6]

    place_filter = _text_filter(query_tokens, ['name', 'short_description', 'description', 'category__name']) if query_tokens else Q()
    if query:
        places = Place.objects.filter(place_filter).order_by('-rating')[:6]
    else:
        places = Place.objects.order_by('-rating', 'name')[:4]

    has_results = any([services, updates, contacts, places])

    return render(request, 'core/ask_ujire.html', {
        'query': query,
        'quick_asks': QUICK_ASKS,
        'services': services,
        'updates': updates,
        'contacts': contacts,
        'places': places,
        'has_results': has_results,
    })


def daily_hub_view(request):
    selected_category = request.GET.get('category', '')
    updates = LocalUpdate.published()

    if selected_category:
        updates = updates.filter(category=selected_category)

    urgent_updates = LocalUpdate.published().filter(is_urgent=True)[:3]
    emergency_contacts = EmergencyContact.objects.filter(is_active=True)

    return render(request, 'core/daily_hub.html', {
        'updates': updates,
        'urgent_updates': urgent_updates,
        'emergency_contacts': emergency_contacts,
        'categories': LocalUpdate.category_options(),
        'selected_category': selected_category,
    })


@login_required
def submit_local_update_view(request):
    if request.method == 'POST':
        form = LocalUpdateSubmissionForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.submitted_by = request.user
            update.status = LocalUpdate.Status.PENDING
            update.save()
            messages.success(request, "Thanks. Your update is waiting for admin review.")
            return redirect('daily_hub')
    else:
        form = LocalUpdateSubmissionForm()

    return render(request, 'core/submit_local_update.html', {'form': form})

def request_otp_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    next_url = request.GET.get('next', '')
        
    if request.method == 'POST':
        phone = request.POST.get('phone')
        if not phone:
            messages.error(request, "Please enter a valid phone number.")
            return redirect('login')
            
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # MOCK SMS BACKEND - Print to terminal
        print(f"\n{'='*50}\n[MOCK SMS] Sending OTP {otp_code} to phone number: {phone}\n{'='*50}\n")
        
        # Save to DB
        OTPVerification.objects.update_or_create(
            phone_number=phone,
            defaults={'otp': otp_code}
        )
        
        request.session['auth_phone'] = phone
        request.session['next_url'] = next_url
        
        return redirect('verify_otp')
            
    return render(request, 'core/login_phone.html', {'next_url': next_url})

def verify_otp_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    phone = request.session.get('auth_phone')
    if not phone:
        return redirect('login')
        
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        
        try:
            verification = OTPVerification.objects.get(phone_number=phone)
            if verification.otp == entered_otp and verification.is_valid():
                # OTP is correct!
                verification.delete()
                
                # Check if user exists
                user = User.objects.filter(username=phone).first()
                if user:
                    login(request, user)
                    messages.success(request, "Successfully logged in!")
                    next_url = request.session.pop('next_url', None)
                    if next_url:
                        return redirect(next_url)
                    return redirect('dashboard')
                else:
                    # New user -> go to profile completion
                    return redirect('register')
            else:
                messages.error(request, "Invalid or expired OTP.")
        except OTPVerification.DoesNotExist:
            messages.error(request, "No OTP request found for this number.")
            
    # Fetch OTP for display during development
    mock_otp = OTPVerification.objects.filter(phone_number=phone).first()
    otp_code = mock_otp.otp if mock_otp else None
            
    return render(request, 'core/login_verify.html', {'phone': phone, 'mock_otp': otp_code})

def complete_profile_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    phone = request.session.get('auth_phone')
    if not phone:
        return redirect('login')
        
    role = request.GET.get('role', 'customer')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        role_type = request.POST.get('role_type')
        
        # Create user using phone as username with an unusable password (perfect for OTP login)
        user = User.objects.create_user(username=phone, email=email)
        user.set_unusable_password()
        user.save()
        
        if role_type == 'provider':
            service_type = request.POST.get('service_type')
            location = request.POST.get('location')
            
            ServiceProvider.objects.create(
                user=user,
                name=name,
                service_type=service_type,
                phone=phone,
                location=location,
                is_approved=False
            )
            messages.success(request, "Registration successful! Awaiting admin approval to list your service.")
        else:
            messages.success(request, "Registration successful! You can now book services.")
            
        login(request, user)
        # Clear session
        request.session.pop('auth_phone', None)
        
        next_url = request.session.pop('next_url', None)
        if next_url:
            return redirect(next_url)
        return redirect('dashboard')
        
    return render(request, 'core/register_complete.html', {'role': role, 'phone': phone, 'service_choices': ServiceProvider.SERVICE_CHOICES})

@login_required
def dashboard_view(request):
    try:
        provider = request.user.serviceprovider
        is_provider = True
        bookings = Booking.objects.filter(provider=provider).order_by('-creation_datetime')
    except ServiceProvider.DoesNotExist:
        is_provider = False
        provider = None
        bookings = Booking.objects.filter(customer_user=request.user).order_by('-creation_datetime')
        
    return render(request, 'core/dashboard.html', {
        'is_provider': is_provider,
        'provider': provider,
        'bookings': bookings
    })
