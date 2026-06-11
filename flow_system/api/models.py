from django.db import models

class Customer(models.Model):
    area_code = models.CharField(max_length=50, unique=True, verbose_name="区域码")
    name = models.CharField(max_length=255, verbose_name="客户名称")
    shipping_address = models.TextField(verbose_name="送货地址")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True) # 暂时允许 null
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) # 暂时允许 null

    def __str__(self):
        return f"{self.name} ({self.area_code})"

class Shipment(models.Model):
    customer = models.ForeignKey(Customer, related_name='shipments', on_delete=models.CASCADE, verbose_name="客户")
    material_number = models.CharField(max_length=100, verbose_name="物料编号")
    material_description = models.CharField(max_length=255, verbose_name="物料描述")
    shipment_date = models.DateField(verbose_name="发货日期", null=True, blank=True) # 新增发货日期字段
    outer_box_date = models.DateField(verbose_name="外箱日期")
    batch_number = models.CharField(max_length=100, verbose_name="批次") # 将存储Excel H列 (如 "12.4")
    specification = models.CharField(max_length=100, verbose_name="规格") # 将存储Excel I列 (如 "168")
    packaging_line = models.CharField(max_length=50, verbose_name="包装线", default='') # Excel J列
    production_date_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="生产日期码") # 新增：对应Excel G列 (YT开头的生产日期码)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True) # 暂时允许 null
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) # 暂时允许 null

    def __str__(self):
        return f"Shipment {self.id} for {self.customer.name} on {self.outer_box_date}"

class ProductionTimeSlot(models.Model):
    shipment = models.ForeignKey(Shipment, related_name='production_time_slots', on_delete=models.CASCADE, verbose_name="所属流向记录")
    start_time_str = models.CharField(max_length=4, verbose_name="开始时间 (HHMM)") # 例如 "1648"
    end_time_str = models.CharField(max_length=4, verbose_name="结束时间 (HHMM)")   # 例如 "1713"
    # quantity = models.IntegerField(verbose_name="箱数/托盘数") # Removed as per frontend changes
    # sequence_number = models.PositiveIntegerField(verbose_name="序号 (1-10)") # 可选，如需显式排序

    class Meta:
        ordering = ['id'] # 默认排序

    def __str__(self):
        return f"Time Slot for Shipment {self.shipment_id}: {self.start_time_str}-{self.end_time_str}" # Removed quantity from string representation

    @property
    def time_range_display(self):
        """用于在Admin或模板中方便显示时间范围"""
        return f"{self.start_time_str}-{self.end_time_str}"
