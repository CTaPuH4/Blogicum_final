from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from .constants import POSTS_ON_PAGE
from .forms import CommentForm, PostForm, UserForm
from .mixins import OnlyAuthorMixin
from .models import Category, Comment, Post


class CommentUpdateView(OnlyAuthorMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'pk': self.object.post.pk}
        )


class CommentDeleteView(OnlyAuthorMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'pk': self.object.post.pk}
        )


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(instance=self.object)
        return context


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'pk': self.object.pk}
        )

    def handle_no_permission(self):
        post = self.get_object()
        return redirect('blog:post_detail', pk=post.pk)


class PostListView(ListView):
    model = Post
    paginate_by = POSTS_ON_PAGE
    template_name = 'blog/index.html'

    def get_queryset(self):
        return (Post.published_objects.published().annotate(
            comment_count=Count('comments')
        )).order_by('-pub_date',)


class PostDetailView(UserPassesTestMixin, DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def test_func(self):
        object = self.get_object()
        return not (object not in Post.published_objects.published()
                    and object.author != self.request.user)

    def handle_no_permission(self):
        raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.object.author.username}
        )


def category_detail(request, slug):
    category = get_object_or_404(
        Category, slug=slug, is_published=True,
    )
    posts = Post.published_objects.published().filter(
        category=category
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date',)
    page_obj = Paginator(posts, POSTS_ON_PAGE).get_page(
        request.GET.get('page')
    )
    context = {
        'category': category,
        'page_obj': page_obj
    }
    return render(request, 'blog/category.html', context)


def profile_detail(request, username):
    profile = get_object_or_404(
        User, username=username
    )
    if request.user == profile:
        posts = Post.objects.filter(
            author=profile
        ).annotate(
            comment_count=Count('comments')
        ).order_by(
            '-pub_date'
        ).select_related(
            'category',
            'location',
        )
    else:
        posts = Post.published_objects.published().filter(
            author=profile
        ).annotate(
            comment_count=Count('comments')
        ).order_by(
            '-pub_date'
        ).select_related(
            'category',
            'location',
        )
    page_obj = Paginator(posts, POSTS_ON_PAGE).get_page(
        request.GET.get('page')
    )
    context = {
        'profile': profile,
        'page_obj': page_obj
    }
    return render(request, 'blog/profile.html', context)


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', pk=pk)
