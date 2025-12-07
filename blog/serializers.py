from rest_framework import serializers
from .models import BlogPost
from django.core.files.base import ContentFile
import base64
import os


class BlogPostSerializer(serializers.ModelSerializer):
    """
    Serializer for BlogPost model with support for image URLs and base64 uploads.
    """

    # Custom fields for image handling (URLs are now model fields)
    hero_image_url = serializers.URLField(required=False, allow_blank=True)
    problem_image_url = serializers.URLField(required=False, allow_blank=True)

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

            # Image URLs (model fields)
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

    def decode_base64_image(self, base64_string, filename_prefix, max_bytes=5 * 1024 * 1024):
        """
        Decode base64 image and return a Django File object with basic limits to avoid DoS.
        """
        try:
            header = ''
            # Remove data URL prefix if present
            if ',' in base64_string:
                header, base64_string = base64_string.split(',', 1)

            # Basic size guard before decoding
            if len(base64_string) > (max_bytes * 1.4):  # base64 adds ~33%
                raise serializers.ValidationError("La imagen en base64 es demasiado grande")

            # Decode base64
            image_data = base64.b64decode(base64_string)

            if len(image_data) > max_bytes:
                raise serializers.ValidationError("La imagen en base64 supera el tamaño permitido (5MB)")

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
        # Extra fields that are not model fields
        hero_image_base64 = validated_data.pop('hero_image_base64', '').strip()
        problem_image_base64 = validated_data.pop('problem_image_base64', '').strip()

        # Crear el post con los campos simples (incluyendo las URLs, que se almacenan en texto)
        blog_post = BlogPost.objects.create(**validated_data)

        # Procesar imágenes en base64 si vienen en la petición
        base64_images = {
            'hero_image': hero_image_base64,
            'problem_image': problem_image_base64,
        }

        for field_name, base64_data in base64_images.items():
            if base64_data:
                image_file = self.decode_base64_image(base64_data, f"{field_name}_{blog_post.id}")
                setattr(blog_post, field_name, image_file)

        # Guardar con archivos si aplica
        blog_post.save()

        return blog_post
