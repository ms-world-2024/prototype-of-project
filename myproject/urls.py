from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin URL for accessing the Django admin site
    path('admin/', admin.site.urls),
    
    # Include all URL patterns from your 'myapp'
    # The empty string '' at the beginning means your app's URLs will be at the root of your project
    path('', include('myapp.urls')),
]

# This is important for serving static files in development
# In a production environment, a web server like Nginx or Apache would handle this
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)