from django.contrib import admin
from .models import Category, Location, Post


admin.site.empty_value_display = 'Не задано'


class PostInline(admin.StackedInline):
    model = Post
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published')
    # prepopulated_fields = {'slug': ('title',)}
    inlines = (PostInline,)


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published')


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'pub_date',
        'author',
        'category',
        'location',
        'is_published'
    )
    list_editable = (
        'is_published',
        'category',
        'location'
    )
    list_display_links = ('title',)
    search_fields = ('title', 'text')
    list_filter = ('is_published', 'category', 'location', 'pub_date')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Post, PostAdmin)