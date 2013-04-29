from django.contrib import admin
from .models import Review

class ReviewAdmin(admin.ModelAdmin):
    list_display  = [ 'id', 'api_posting_id', 'title', 'author_display_name']
    search_fields = ['title', 'api_posting_id', 'content']

admin.site.register( Review, ReviewAdmin )
