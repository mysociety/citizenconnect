from django.contrib import admin
from .models import Review, Rating


class RatingAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'score',  'review']


class RatingInline(admin.TabularInline):
    model = Rating
    extra = 1


class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'api_posting_id', 'title', 'author_display_name']
    search_fields = ['title', 'api_posting_id', 'content']
    inlines = [RatingInline]


admin.site.register(Review, ReviewAdmin)
admin.site.register(Rating, RatingAdmin)
