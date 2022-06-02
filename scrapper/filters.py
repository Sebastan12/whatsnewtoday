import django_filters
from django_filters import NumberFilter, CharFilter, BooleanFilter
from .models import *

class ImageFilter(django_filters.FilterSet):
    title = CharFilter(field_name="title", lookup_expr="icontains", label="Titel")
    description = CharFilter(field_name="description", lookup_expr="icontains", label="Beschreibung")
    start_price = NumberFilter(field_name="price", lookup_expr="gte", label="Preis min")
    end_price = NumberFilter(field_name="price", lookup_expr="lte", label="Preis Max")
    is_searching_for = BooleanFilter(field_name="is_searching_for", lookup_expr="exact", label="Suche Anzeigen")
    class Meta:
        model = Image
        fields = '__all__'
        exclude = ['article_id','hash', 'created_at', 'price', 'title', 'description', 'is_searching_for']