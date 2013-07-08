from django.contrib import admin

import reversion

from .models import Article


class ArticleAdmin(reversion.VersionAdmin):
    pass

admin.site.register(Article, ArticleAdmin)
