from rest_framework import serializers
from .models import BlogPost
import requests
from django.core.files.base import ContentFile
from django.core.files import File
import base64
import os


class BlogPostSerializer(serializers.ModelSerializer):
    """
    Serializer for BlogPost model with support for image URLs and base64 uploads.
    """

    # Custom fields for image handling
    hero_image_url = serializers.URLField(write_only=True, required=False, allow_blank=True)
    problem_image_url = serializers.URLField(write_only=True, required=False, allow_blank=True)

    # Base64 image fields
    hero_image_base64 = serializers.CharField(write_only=True, required=False, allow_blank=True)
    problem_image_base64 = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = BlogPost
        fields = [
            # Basic fields
            'title', 'slug', 'is_published', 'category', 'excerpt', 'meta_description',

            # Content sections
            'problem_section', 'why_automate_section', 'sales_angle_section',
            'how_it_works_section', 'benefits_section', 'hypothetical_case_section',
            'final_cta_section',

            # Image URLs (for input)
            'hero_image_url', 'problem_image_url',

            # Base64 images (for input)
            'hero_image_base64', 'problem_image_base64',

            # Read-only fields
            'published_date', 'updated_date',
        ]
        read_only_fields = ['slug', 'published_date', 'updated_date']

    def validate_category(self, value):
        """
        Validate that category is one of the allowed choices.
        """
        allowed_categories = [choice[0] for choice in BlogPost._meta.get_field('category').choices]
        if value not in allowed_categories:
            raise serializers.ValidationError(f"Categoría debe ser una de: {', '.join(allowed_categories)}")
        return value

    def validate_title(self, value):
        """
        Validate title is not empty and reasonable length.
        """
        if not value.strip():
            raise serializers.ValidationError("El título no puede estar vacío")
        if len(value) < 5:
            raise serializers.ValidationError("El título debe tener al menos 5 caracteres")
        return value.strip()

    def download_image_from_url(self, url, filename_prefix):
        """
        Download image from URL and return a Django File object.
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Get file extension from content-type or URL
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = 'jpg'
            elif 'png' in content_type:
                ext = 'png'
            elif 'gif' in content_type:
                ext = 'gif'
            elif 'webp' in content_type:
                ext = 'webp'
            else:
                # Try to get from URL
                url_path = url.split('?')[0]  # Remove query params
                ext = os.path.splitext(url_path)[1].lstrip('.')
                if not ext:
                    ext = 'jpg'  # Default

            filename = f"{filename_prefix}_{self._get_timestamp()}.{ext}"

            return ContentFile(response.content, name=filename)

        except requests.RequestException as e:
            raise serializers.ValidationError(f"Error descargando imagen desde {url}: {str(e)}")

    def decode_base64_image(self, base64_string, filename_prefix):
        """
        Decode base64 image and return a Django File object.
        """
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                header, base64_string = base64_string.split(',', 1)

            # Decode base64
            image_data = base64.b64decode(base64_string)

            # Determine file extension from header or default to png
            ext = 'png'  # Default
            if 'data:image/' in header:
                ext = header.split('data:image/')[1].split(';')[0]

            filename = f"{filename_prefix}_{self._get_timestamp()}.{ext}"

            return ContentFile(image_data, name=filename)

        except Exception as e:
            raise serializers.ValidationError(f"Error procesando imagen base64: {str(e)}")

    def _get_timestamp(self):
        """
        Get current timestamp for unique filenames.
        """
        from django.utils import timezone
        return timezone.now().strftime('%Y%m%d_%H%M%S')

    def create(self, validated_data):
        """
        Create BlogPost instance with image handling.
        """
        # Extract image URLs and base64 data
        image_urls = {}
        base64_images = {}

        for field_name in ['hero_image', 'problem_image']:
            url_field = f"{field_name}_url"
            base64_field = f"{field_name}_base64"

            if url_field in validated_data:
                image_urls[field_name] = validated_data.pop(url_field)
            if base64_field in validated_data:
                base64_images[field_name] = validated_data.pop(base64_field)

        # Create the blog post
        blog_post = BlogPost.objects.create(**validated_data)

        # Handle image URLs
        for field_name, url in image_urls.items():
            if url:
                image_file = self.download_image_from_url(url, f"{field_name}_{blog_post.id}")
                setattr(blog_post, f"{field_name}_image", image_file)

        # Handle base64 images
        for field_name, base64_data in base64_images.items():
            if base64_data:
                image_file = self.decode_base64_image(base64_data, f"{field_name}_{blog_post.id}")
                setattr(blog_post, f"{field_name}_image", image_file)

        # Save with images
        blog_post.save()

        return blog_post