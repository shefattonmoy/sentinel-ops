# apps/search/urls.py
from django.urls import path
from .views import GlobalSearchViewSet

app_name = 'search'

urlpatterns = [
    path('', GlobalSearchViewSet.as_view({'post': 'search'}), name='search'),
    path('quick/', GlobalSearchViewSet.as_view({'post': 'quick_search'}), name='quick-search'),
]