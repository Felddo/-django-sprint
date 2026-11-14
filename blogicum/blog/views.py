import datetime
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Post, Category
from django.db import models
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserChangeForm
from django.core.paginator import Paginator
from django.shortcuts import redirect
from .forms import ProfileEditForm
from .forms import PostForm, CommentForm
from .models import Post, Category, Location, Comment
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator

from .forms import PostForm
from .models import Post, Category, Location

User = get_user_model()

def registration(request):
    form = UserCreationForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('login')

    return render(request,'registration/registration_form.html',{'form': form})


@login_required
def edit_profile(request):
    form = ProfileEditForm(
        request.POST or None,
        instance=request.user
    )

    if form.is_valid():
        form.save()
        return redirect(
            'blog:profile',
            username=request.user.username
        )

    return render(
        request,
        'blog/user.html',
        {'form': form}
    )


def profile(request, username):
    profile = get_object_or_404(
        User,
        username=username
    )

    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    ).annotate(
        comment_count=models.Count('comments')
    ).filter(
        author=profile
    )

    if request.user != profile:
        post_list = post_list.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )

    paginator = Paginator(post_list.order_by('-pub_date'), 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': profile,
        'page_obj': page_obj,
        'now': timezone.now(),
    }

    return render(
        request,
        'blog/profile.html',
        context
    )


def index(request):
    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    ).annotate(
        comment_count=models.Count('comments')
    ).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'now': timezone.now(),
    }

    return render(request, 'blog/index.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    ).annotate(
        comment_count=models.Count('comments')
    ).filter(
        category=category,
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
        'now': timezone.now(),
    }

    return render(request, 'blog/category.html', context)


def post_detail(request, pk):
    post = get_object_or_404(
        Post.objects.select_related(
            'category', 'location', 'author'
        ).annotate(
            comment_count=models.Count('comments')
        ),
        pk=pk
    )

    if request.user != post.author:
        if (
            not post.is_published
            or not post.category
            or not post.category.is_published
            or post.pub_date > timezone.now()
        ):
            from django.http import Http404
            raise Http404

    comments = post.comments.select_related(
        'author'
    ).order_by('created_at')

    context = {
        'post': post,
        'comments': comments,
        'form': CommentForm(),
        'now': timezone.now(),
    }

    return render(request, 'blog/detail.html', context)

@login_required
def create_post(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect(
            'blog:profile',
            username=request.user.username
        )

    return render(
        request,
        'blog/create.html',
        {'form': form}
    )


@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.user != post.author:
        return redirect('blog:post_detail', pk=post.pk)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', pk=post.pk)

    return render(
        request,
        'blog/create.html',
        {'form': form}
    )


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)

    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()

    return redirect('blog:post_detail', pk=post.pk)


@login_required
def edit_comment(request, pk, comment_id):
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        post_id=pk
    )

    if request.user != comment.author:
        return redirect('blog:post_detail', pk=pk)

    form = CommentForm(
        request.POST or None,
        instance=comment
    )

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', pk=pk)

    return render(
        request,
        'blog/edit_comment.html',
        {
            'form': form,
            'comment': comment,
            'post': comment.post,
        }
    )


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.user != post.author:
        return redirect('blog:post_detail', pk=post.pk)

    if request.method == 'POST':
        post.delete()
        return redirect(
            'blog:profile',
            username=request.user.username
        )

    form = PostForm(instance=post)

    return render(
        request,
        'blog/create.html',
        {'form': form}
    )


@login_required
def delete_comment(request, pk, comment_id):
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        post_id=pk
    )

    if request.user != comment.author:
        return redirect(
            'blog:post_detail',
            pk=pk
        )

    if request.method == 'POST':
        comment.delete()
        return redirect(
            'blog:post_detail',
            pk=pk
        )

    return render(
        request,
        'blog/comment.html',
        {'comment': comment}
    )