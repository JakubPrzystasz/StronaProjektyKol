from django.contrib import admin

from .models import *

admin.site.register(StudentClub)
admin.site.register(Grade)
admin.site.register(Paper)
admin.site.register(CoAuthor)
admin.site.register(UploadedFile)
admin.site.register(Review)
admin.site.register(Announcement)
admin.site.register(Message)
admin.site.register(MessageSeen)
