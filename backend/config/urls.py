# backend/config/urls.py em 2025-12-13 18:30

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# Função para silenciar favicon
def empty_response(request):
    return HttpResponse(status=204) # 204 No Content

# Definição das rotas da API (v1)
api_v1_patterns = [
    # Autenticação (JWT)
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Apps da Vitalia (Placeholder por enquanto, criaremos os urls.py de cada app na sequência)
    path('social/', include('social.urls')), 
    path('medical/', include('medical.urls')),
    path('core/', include('core.urls')),
]

urlpatterns = [
    # Health Check simples para a raiz
    path('', lambda request: __import__('django.http').http.JsonResponse({"status": "ok"})),

    path('admin/', admin.site.urls),
    
    # Prefixo da API
    path('api/v1/', include(api_v1_patterns)),
    
    # Documentação da API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Interface Visual (Swagger UI) - Ótimo para testar manualmente
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Interface Visual (Redoc) - Ótimo para leitura
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # Health Check simples para o Frontend testar
    path('api/health/', lambda request: __import__('django.http').http.JsonResponse({"status": "ok"})),
    
    # --- SILENCIADORES DE LOG ---
    path('favicon.ico', empty_response),
    path('sitemap.xml', empty_response),
    path('robots.txt', empty_response),
    path('.well-known/security.txt', empty_response),
]

# Servir mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
