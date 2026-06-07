from django.shortcuts import render, get_object_or_404
from .models import Category, Place

def explore_index(request):
    categories = Category.objects.all()
    selected_category = request.GET.get('category')

    if selected_category:
        places = Place.objects.filter(category__slug=selected_category)
    else:
        places = Place.objects.all()

    return render(request, 'locations/explore.html', {
        'categories': categories,
        'places': places,
        'selected_category': selected_category
    })

def place_detail(request, place_id):
    place = get_object_or_404(Place, id=place_id)
    return render(request, 'locations/place_detail.html', {'place': place})