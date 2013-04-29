from django.contrib import admin
from .models import Review, Rating

class ReviewAdmin(admin.ModelAdmin):
    list_display  = [ 'id', 'api_posting_id', 'title', 'author_display_name']
    search_fields = ['title', 'api_posting_id', 'content']

class RatingAdmin(admin.ModelAdmin):
    list_display  = [ 'id', 'review', 'question', 'score']

admin.site.register( Review, ReviewAdmin )
admin.site.register( Rating, RatingAdmin )
