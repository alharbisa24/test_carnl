from django.contrib import admin
from home import models as HomeModels



# Register your models here.

admin.site.register(HomeModels.Rating)
admin.site.register(HomeModels.Request)