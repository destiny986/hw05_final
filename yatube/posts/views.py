from django.shortcuts import render, get_object_or_404
from .models import Post, Group, Follow, User
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm
from django.shortcuts import redirect
from .services import paging
from django.views.decorators.cache import cache_page
from django.db import IntegrityError


@cache_page(20, key_prefix="index_page")
def index(request):
    template = "posts/index.html"
    post_list = Post.objects.all().order_by("-pub_date")
    page_obj = paging(request, post_list)
    context = {
        "page_obj": page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = "posts/group_list.html"
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.order_by("-pub_date")
    page_obj = paging(request, post_list)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = "posts/profile.html"
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all().order_by("-pub_date")
    post_count = post_list.count()
    page_obj = paging(request, post_list)
    current_user = request.user  # AnonymousUser для неавторизованного
    try:
        Follow.objects.get(
            user=current_user,
            author=author,
        )
        is_following = True
    except (TypeError, Follow.DoesNotExist):
        is_following = False
    """
==============================================================================
    TypeError - анонимный юзер запрашивает страницу (request.user - ошибка)
    Follow.DoesNotExist - экземпляр подписки не найден
    Не лучше будет оставить все исключения? Типо, если получил Follow - 
    кнопка 'отписаться' (такое только у авторизированных юзеров может быть)
    Не получил Follow по любой из причин - кнопка 'отписаться'

    try:
        Follow.objects.get(
            user = current_user,
            author = author,
        )
        is_following = True
    except:
        is_following = False
==============================================================================
    Или таки вставлять ветвление проверки is_authenticated?

    if current_user.is_authenticated:
        try:
            Follow.objects.get(
                user = current_user,
                author = author,
            )
            is_following = True
        except (Follow.DoesNotExist):
            is_following = False
    else:
        is_following = False
==============================================================================
    """
    context = {
        "author": author,
        "page_obj": page_obj,
        "post_count": post_count,
        "following": is_following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = "posts/post_detail.html"
    article = get_object_or_404(
        Post.objects.select_related("author"), pk=post_id
    )
    post_count = article.author.posts.count()
    form = CommentForm(request.POST or None)
    comment_list = article.comments.all().order_by("-pub_date")
    comments = paging(request, comment_list)
    context = {
        "article": article,
        "post_count": post_count,
        "form": form,
        "page_obj": comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {
        "form": form,
    }
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:profile", username=request.user)
    return render(request, "posts/create_post.html", context)


@login_required
def post_edit(request, post_id):
    edit_post = get_object_or_404(Post, id=post_id)
    if request.user != edit_post.author:
        return redirect("posts:post_detail", post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=edit_post
    )
    context = {
        "post": edit_post,
        "form": form,
        "is_edit": True,
    }
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)
    return render(request, "posts/create_post.html", context)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    template = "posts/follow.html"
    current_user = request.user
    post_list = Post.objects.filter(
        author__following__user=current_user
    ).order_by("-pub_date")
    # 1) ищет всех user = текущему юзеру
    # 2) ищет все объекты Follow которые ссылаются на user через related_name
    # following
    # 3) ищет всех авторов от полученных объектов Follow
    # 4) фильтрует по автору
    paginator = paging(request, post_list)
    context = {
        "page_obj": paginator,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    current_user = request.user
    follow_author = get_object_or_404(User, username=username)
    if current_user == follow_author:
        return redirect("posts:profile", username=username)
    else:
        try:
            Follow.objects.create(
                user=current_user,
                author=follow_author,
            )
            return redirect("posts:profile", username=username)
        # отлавливает UNIQUE constraint failed (дубликат)
        # SQL ошибка
        except IntegrityError:
            return redirect("posts:profile", username=username)


"""
==============================================================================
Или через get_or_create:

@login_required
def profile_follow(request, username):
    current_user = request.user
    follow_author = get_object_or_404(User, username=username)
    if current_user == follow_author:
        return redirect('posts:profile', username=username)
    else:
        Follow.objects.get_or_create(
            user = current_user,
            author = follow_author,
        )
        return redirect('posts:profile', username=username)
==============================================================================
"""


@login_required
def profile_unfollow(request, username):
    current_user = request.user
    follow_author = get_object_or_404(User, username=username)
    get_object_or_404(
        Follow,
        user=current_user,
        author=follow_author,
    ).delete()
    return redirect("posts:profile", username=username)
