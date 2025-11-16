from django.urls import path, include
from . import views
from .api_views import BlogPostCreateAPIView, api_status

app_name = 'blog'

urlpatterns = [
    # Public blog views
    path('<slug:slug>/', views.blog_detail, name='blog_detail'),

    # API endpoints
    path('api/', include([
        path('create-post/', BlogPostCreateAPIView.as_view(), name='api_create_post'),
        path('status/', api_status, name='api_status'),
    ])),
]