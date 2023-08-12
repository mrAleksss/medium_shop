from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views


urlpatterns = [
    path('davinci/', admin.site.urls),
    
    path('', views.home, name='home'),
    path('store/', include("store.urls")),
    path('cart/', include("carts.urls")),
    path('accounts/', include("accounts.urls")),
    path('orders/', include('orders.urls')),
    path("__debug__/", include("debug_toolbar.urls")),
]  
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
