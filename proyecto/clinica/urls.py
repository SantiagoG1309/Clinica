from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('usuarios/', include('usuarios.urls')),
    path('citas/', include('citas.urls')),
    path('reportes/', include('reportes.urls')),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

