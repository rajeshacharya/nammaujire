from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, help_text="FontAwesome icon class, e.g. fa-solid fa-graduation-cap")

    def __str__(self):
        return self.name

class Place(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='places')
    description = models.TextField()
    short_description = models.CharField(max_length=200)
    image = models.ImageField(upload_to='places/')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    reviews_count = models.IntegerField(default=0)
    map_url = models.URLField(blank=True, null=True, help_text="Google Maps URL")

    def __str__(self):
        return self.name
