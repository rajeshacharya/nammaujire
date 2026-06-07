from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def ads_list(request):
    return HttpResponse("List of ads, etc.")