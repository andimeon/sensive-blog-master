from django.shortcuts import render, get_object_or_404
from blog.models import Post, Tag


def serialize_post(post):
    post_tags = post.tags.all()
    return {
        "title": post.title,
        "teaser_text": post.text[:200],
        "author": post.author.username,
        # Было замечание, что на этом этапе происходят дополнительные запросы к базе данных. На данном этапе
        # к post author уже был префетчен (в models.py фукнцкция fetch_with_posts_count). В сети был совет, что
        # к полю ForeignKey лучше применять не prefetch_related, а select_related. Я попробовал, и запросы уменьшились.
        # К примеру на главной странице с 9 до 7. Но дико возросло время загрузки страницы: с 300мс до 12000мс.
        # Поэтому решено было оставить прошлое решение
        
        "comments_amount": post.comments__count,
        "image_url": post.image.url if post.image else None,
        "published_at": post.published_at,
        "slug": post.slug,
        "tags": [serialize_tag(tag) for tag in post_tags],
        'first_tag_title': post_tags[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts__count,
    }


def index(request):
    posts = Post.objects.popular().fetch_with_posts_count()
    
    most_popular_posts = posts[:5].fetch_with_comments_count()
    
    most_fresh_posts = posts.order_by('-published_at')[:5].fetch_with_comments_count()
    
    most_popular_tags = Tag.objects.popular()[:5]
    
    context = {
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    posts = Post.objects.popular().fetch_with_posts_count()
    # Было замечание проверить, какая из этих функций здесь лишняя. Я проверил, как оказалось если
    # любую отсюда убирать, то код ломается.
    
    post = get_object_or_404(posts, slug=slug)
    
    comments = post.comments.prefetch_related('author')
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })
    
    related_tags = post.tags.all()
    
    serialized_post = {
        "title": post.title,
        "text": post.text,
        "author": post.author.username,
        "comments": serialized_comments,
        'likes_amount': post.likes__count,
        "image_url": post.image.url if post.image else None,
        "published_at": post.published_at,
        "slug": post.slug,
        "tags": [serialize_tag(tag) for tag in related_tags],
    }
    
    most_popular_tags = Tag.objects.popular()[:5]
    
    most_popular_posts = posts.fetch_with_comments_count()
    
    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tags = Tag.objects.popular()
    posts = Post.objects.popular().fetch_with_posts_count()
    
    most_popular_tags = tags[:5]
    
    most_popular_posts = posts[:5].fetch_with_comments_count()
    
    tag = get_object_or_404(tags, title=tag_title)
    related_posts = tag.posts[:20].fetch_with_comments_count()
    
    context = {
        "tag": tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        "posts": [serialize_post(post) for post in related_posts],
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
