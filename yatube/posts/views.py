from django.shortcuts import render, get_object_or_404
from .models import Post, Group, Follow, User
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm
from django.shortcuts import redirect
from .services import paging
from django.views.decorators.cache import cache_page


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    page_obj = paging(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paging(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    post_count = post_list.count()
    page_obj = paging(request, post_list)
    current_user = request.user
    is_following = current_user.is_authenticated and Follow.objects.filter(
        user=current_user,
        author=author,
    ).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'post_count': post_count,
        'following': is_following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    article = get_object_or_404(
        Post.objects.select_related('author'), pk=post_id
    )
    post_count = article.author.posts.count()
    form = CommentForm()
    comment_list = article.comments.all().order_by('-pub_date')
    comments = paging(request, comment_list)
    context = {
        'article': article,
        'post_count': post_count,
        'form': form,
        'page_obj': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {
        'form': form,
    }
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    edit_post = get_object_or_404(Post, id=post_id)
    if request.user != edit_post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=edit_post
    )
    context = {
        'post': edit_post,
        'form': form,
        'is_edit': True,
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    current_user = request.user
    post_list = Post.objects.filter(
        author__following__user=current_user
    )
    # 1) ищет всех user = текущему юзеру
    # 2) ищет все объекты Follow которые ссылаются на user через related_name
    # following
    # 3) ищет всех авторов от полученных объектов Follow
    # 4) фильтрует по автору
    paginator = paging(request, post_list)
    context = {
        'page_obj': paginator,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    current_user = request.user
    follow_author = get_object_or_404(User, username=username)
    if current_user == follow_author:
        return redirect('posts:profile', username=username)
    Follow.objects.get_or_create(
        user=current_user,
        author=follow_author,
    )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    current_user = request.user
    follow_author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=current_user,
        author=follow_author,
    ).delete()
    return redirect('posts:profile', username=username)
