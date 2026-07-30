from django.contrib import admin

from memberships import models

admin.site.register(models.Membership)
admin.site.register(models.Gym)
