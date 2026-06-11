"""
URL configuration for flow_system project.
"""
from pathlib import Path
from django.http import FileResponse, Http404
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

# drf_yasg（Swagger文档）为可选依赖，不影响主功能
try:
    from drf_yasg.views import get_schema_view
    from drf_yasg import openapi
    from rest_framework import permissions
    schema_view = get_schema_view(
        openapi.Info(
            title="Flow System API",
            default_version='v1',
            description="API documentation for the Finished Goods Flow System",
        ),
        public=True,
        permission_classes=(permissions.AllowAny,),
    )
    _YASG_AVAILABLE = True
except Exception:
    _YASG_AVAILABLE = False


def serve_vue_index(request):
    """提供 Vue 前端的 index.html"""
    dist_index = settings.FRONTEND_DIR / 'index.html'
    if not dist_index.exists():
        raise Http404(f"前端文件未找到: {dist_index}")
    return FileResponse(open(str(dist_index), 'rb'), content_type='text/html; charset=utf-8')


def serve_static_file(request, file_path):
    """提供 Vue 前端的静态资源（CSS/JS/图片等）"""
    full_path = settings.FRONTEND_DIR / file_path
    if not full_path.exists():
        raise Http404(f"文件未找到: {full_path}")
    import mimetypes
    content_type, _ = mimetypes.guess_type(str(full_path))
    return FileResponse(open(str(full_path), 'rb'), content_type=content_type or 'application/octet-stream')


urlpatterns = [
    # Vue 前端主页（根路径）
    path('', serve_vue_index, name='index'),
    # Vue 静态资源（css/js/img/fonts 等）
    re_path(r'^(?P<file_path>(?:css|js|img|fonts)/.*)', serve_static_file, name='vue-static'),
    re_path(r'^(?P<file_path>favicon\.ico)', serve_static_file, name='vue-favicon'),
    # Django 管理后台
    path('admin/', admin.site.urls),
    # REST API
    path('api/v1/', include('api.urls')),
]

# API 文档（drf_yasg 可选，未安装时跳过）
if _YASG_AVAILABLE:
    urlpatterns += [
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
