from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import BlogPost


def blog_detail(request, slug):
    """
    Vista de detalle de un post del blog
    """
    try:
        post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    except Http404:
        # Si no encuentra el post, redirigir a 404
        raise Http404("Post no encontrado")

    # Contexto para el template
    context = {
        'post': post,
        'page_title': post.title,
        'meta_description': post.meta_description or post.excerpt,
    }

    return render(request, 'blog_detail.html', context)


def blog_list(request):
    """
    Vista de lista de posts del blog (opcional, para futuras expansiones)
    """
    posts = BlogPost.objects.filter(is_published=True).order_by('-published_date')

    context = {
        'posts': posts,
        'page_title': 'Blog - IACOL Dev',
    }

    return render(request, 'blog_list.html', context)
