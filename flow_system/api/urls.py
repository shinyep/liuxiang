from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, ShipmentViewSet, ShipmentImportView, ShipmentStatisticsView, MaterialShipmentStatisticsView, UniqueMaterialsView, CustomerShipmentStatisticsView, DatabaseBackupView, DatabaseImportView

# 创建一个路由器并注册我们的视图集
router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'shipments', ShipmentViewSet, basename='shipment')

# API URL 由路由器自动确定。
urlpatterns = [
    path('shipments/import/', ShipmentImportView.as_view(), name='shipment-import'), # New URL for import
    path('shipment-statistics/', ShipmentStatisticsView.as_view(), name='shipment-statistics'),
    path('statistics/material-shipments/', MaterialShipmentStatisticsView.as_view(), name='material-shipment-statistics'), # New URL for material statistics
    path('materials/unique/', UniqueMaterialsView.as_view(), name='unique-materials'),
    path('statistics/customer-shipments/', CustomerShipmentStatisticsView.as_view(), name='customer-shipment-statistics'),
    path('database/backup/', DatabaseBackupView.as_view(), name='database-backup'),
    path('database/import/', DatabaseImportView.as_view(), name='database-import'),
    path('', include(router.urls)),
]
