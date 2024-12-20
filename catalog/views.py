from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify
from django.views.generic import ListView, DetailView, TemplateView, CreateView, UpdateView, DeleteView

from .forms import BlogPostForm, ProductForm, VersionForm
from .models import Product, BlogPost, Version
from .services import get_categories, get_products


class CategoryListView(TemplateView):
    template_name = 'catalog/category_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = get_categories()
        return context


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'catalog/index.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['object_list'] = get_products()

        for product in context['object_list']:
            active_version = product.versions.filter(is_active=True).first()
            product.active_version = active_version

        return context


class ContactView(TemplateView):
    template_name = 'catalog/contacts.html'

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        print(f'{name}, ({email}): {message}')
        return self.render_to_response(self.get_context_data())


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('catalog:index')

    def form_valid(self, form):
        form.instance.owner = self.request.user  # Привязываем текущего пользователя
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('catalog:index')

    def dispatch(self, request, *args, **kwargs):
        """Проверка прав доступа: владелец или пользователь с правами модератора."""
        product = self.get_object()
        if not (product.owner == self.request.user or self.request.user.has_perm(
                'catalog.can_edit_product_description')):
            messages.error(self.request, "У вас нет прав на редактирование этого продукта.")
            return redirect('catalog:index')
        return super().dispatch(request, *args, **kwargs)


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'catalog/product_confirm_delete.html'
    success_url = reverse_lazy('catalog:index')


class BlogPostListView(ListView):
    model = BlogPost
    template_name = 'catalog/blogpost_list.html'
    context_object_name = 'blog_posts'

    def get_queryset(self):
        # Фильтруем только опубликованные статьи
        return BlogPost.objects.filter(is_published=True)


class BlogPostDetailView(DetailView):
    model = BlogPost
    template_name = 'catalog/blogpost_detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        self.object = super().get_object(queryset)
        # Увеличиваем счетчик просмотров
        self.object.views_count += 1
        self.object.save()  # Сохраняем изменения в базе данных
        return self.object


class BlogPostCreateView(CreateView):
    model = BlogPost
    form_class = BlogPostForm
    template_name = 'catalog/blogpost_form.html'

    def form_valid(self, form):
        # Сохраняем статью
        new_blog = form.save(commit=False)
        # Генерация slug на основе заголовка
        new_blog.slug = slugify(new_blog.title)
        new_blog.save()  # Сохраняем статью с уникальным slug
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('catalog:blogpost_detail', kwargs={'slug': self.object.slug})


class BlogPostUpdateView(UpdateView):
    model = BlogPost
    form_class = BlogPostForm
    template_name = 'catalog/blogpost_form.html'

    def get_success_url(self):
        return reverse('catalog:blogpost_detail', kwargs={'slug': self.object.slug})


class BlogPostDeleteView(DeleteView):
    model = BlogPost
    template_name = 'catalog/blogpost_confirm_delete.html'

    def get_success_url(self):
        return reverse('catalog:blogpost_list')


# Функция для отправки письма
def send_congratulation_email(post):
    subject = 'Поздравляем с 100 просмотров!'
    message = f"Поздравляем! Ваша статья '{post.title}' достигла 100 просмотров!"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = ['your-email@yandex.ru']  # Тот же email для получения уведомления

    send_mail(subject, message, from_email, recipient_list)


# Сигнал для отслеживания количества просмотров
@receiver(post_save, sender=BlogPost)
def check_views_count(sender, instance, created, **kwargs):
    # Проверяем, если статья была обновлена, а не создана
    if not created and instance.views_count >= 100:
        send_congratulation_email(instance)


def add_version(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = VersionForm(request.POST)
        if form.is_valid():
            version = form.save(commit=False)
            version.product = product  # Связка версии с продуктом
            version.save()
            messages.success(request, "Version added successfully!")
            return redirect(reverse('catalog:product_detail', args=[product_id]))
    else:
        form = VersionForm()
    return render(request, 'catalog/add_version.html', {'form': form, 'product': product})


def edit_version(request, product_id, version_id):
    version = get_object_or_404(Version, pk=version_id, product_id=product_id)
    if request.method == 'POST':
        form = VersionForm(request.POST, instance=version)
        if form.is_valid():
            form.save()
            messages.success(request, "Version updated successfully!")
            return redirect(reverse('catalog:product_detail', args=[product_id]))
    else:
        form = VersionForm(instance=version)
    return render(request, 'catalog/edit_version.html', {'form': form, 'product_id': product_id})


def delete_version(request, product_id, version_id):
    version = get_object_or_404(Version, pk=version_id, product_id=product_id)
    if request.method == 'POST':
        version.delete()
        messages.success(request, "Version deleted successfully!")
        return redirect(reverse('catalog:product_detail', args=[product_id]))
    return render(request, 'catalog/delete_version.html', {'version': version, 'product_id': product_id})
