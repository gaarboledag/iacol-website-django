from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .serializers import BlogPostSerializer
from .authentication import APIKeyAuthentication
import logging

logger = logging.getLogger(__name__)


class BlogPostCreateAPIView(APIView):
    """
    API endpoint for creating blog posts from external services (N8N).

    Authentication: API Key via X-API-Key header or Authorization: Bearer <key>
    Rate limiting: 10 requests per minute per API key
    """

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='user', rate='10/m', method='POST'))
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        """
        Create a new blog post.

        Expected JSON payload:
        {
            "title": "Post Title",
            "category": "guias",
            "excerpt": "Brief description",
            "is_published": false,
            "problem_section": "Problem description...",
            "why_automate_section": "Why automate...",
            "sales_angle_section": "Sales angle...",
            "how_it_works_section": "How it works...",
            "benefits_section": "Benefits...",
            "hypothetical_case_section": "Case study...",
            "final_cta_section": "Call to action...",
            "meta_description": "SEO description",

            // Image options (choose one per image type):
            "hero_image_url": "https://example.com/image.jpg",
            "hero_image_base64": "data:image/jpeg;base64,...",

            "problem_image_url": "https://example.com/image.jpg",
            "agent_diagram_image_url": "https://example.com/diagram.jpg",
            "case_image_url": "https://example.com/case.jpg",
            "optional_icon_image_url": "https://example.com/icon.jpg"
        }
        """
        try:
            serializer = BlogPostSerializer(data=request.data)

            if serializer.is_valid():
                # Log the creation attempt
                logger.info(f"Blog post creation attempt by API user: {request.user.username}")
                logger.info(f"Post title: {serializer.validated_data.get('title', 'Unknown')}")

                blog_post = serializer.save()

                # Log successful creation
                logger.info(f"Blog post created successfully: {blog_post.title} (ID: {blog_post.id})")

                # Construct URL manually to avoid reverse issues
                blog_url = f"/blog/{blog_post.slug}/"
                absolute_url = request.build_absolute_uri(blog_url)

                response_data = {
                    'success': True,
                    'message': 'Blog post created successfully',
                    'data': {
                        'id': blog_post.id,
                        'title': blog_post.title,
                        'slug': blog_post.slug,
                        'url': absolute_url,
                        'is_published': blog_post.is_published,
                        'category': blog_post.category,
                        'created_at': blog_post.published_date.isoformat(),
                    }
                }

                return Response(response_data, status=status.HTTP_201_CREATED)

            else:
                # Log validation errors
                logger.warning(f"Blog post validation failed: {serializer.errors}")

                return Response({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error creating blog post: {str(e)}", exc_info=True)

            return Response({
                'success': False,
                'message': 'Internal server error',
                'error': str(e) if request.user.is_staff else 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_status(request):
    """
    Simple endpoint to test API connectivity and authentication.
    """
    return Response({
        'status': 'API is working',
        'user': request.user.username,
        'authenticated': True,
        'timestamp': request._request.META.get('HTTP_DATE', 'Unknown')
    })