from rest_framework import serializers
from .models import Customer, Shipment, ProductionTimeSlot # Import new model

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'area_code', 'name', 'shipping_address']

class ProductionTimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionTimeSlot
        fields = ['id', 'start_time_str', 'end_time_str']
        read_only_fields = ['id']

class ShipmentSerializer(serializers.ModelSerializer):
    # For reading customer details
    customer_details = CustomerSerializer(source='customer', read_only=True) 
    # For writing customer association via ID
    # required=False, allow_null=True: 视图层已处理 area_code 自动创建客户，此处允许空值通过验证
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source='customer', 
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # Unified field for reading and writing production time slots
    production_time_slots = ProductionTimeSlotSerializer(many=True, required=False)
    # 'source' is implicitly 'production_time_slots' because the field name matches the model's related_name.
    # 'required=False' allows creating/updating shipments without providing slots.

    class Meta:
        model = Shipment
        fields = [
            'id',
            'customer_details', 
            'customer_id',      
            'material_number',
            'material_description',
            'shipment_date', # Added missing shipment_date field
            'outer_box_date',
            'batch_number',
            'production_date_code', # Added new field here
            'specification',
            'packaging_line',
            'production_time_slots',      # For both reading and writing slots
            # 'created_at', # Uncomment if these should be part of the API response
            # 'updated_at'  # Uncomment if these should be part of the API response
        ]

    def validate(self, data):
        """
        验证单个流向记录内部的生产时间段是否包含重复的开始时间。
        """
        # Now, 'production_time_slots' should be directly available in 'data' if provided in input.
        slots_data = data.get('production_time_slots')

        if not slots_data or len(slots_data) < 2: # This check is for *internal* duplicates, so if <2 slots, no internal dupes possible.
            # 如果没有时间段或只有一个时间段，则不可能有重复
            return data

        # 提取所有非空的开始时间字符串
        start_times = [
            slot['start_time_str'].strip() 
            for slot in slots_data 
            if 'start_time_str' in slot and slot.get('start_time_str') and str(slot.get('start_time_str')).strip()
        ]

        # 1. 内部重复检查: 检查当前提交的 slots_input 内部是否有重复的开始时间
        if len(start_times) > len(set(start_times)):
            raise serializers.ValidationError({
                'production_time_slots_input': '当前提交的生产时间段中包含了重复的开始时间，请检查输入。'
            })

        # 2. 外部重复检查 (针对 "F" 时间段):
        # 检查数据库中是否已存在具有相同核心关键信息且生产时间为 "F" 的记录。
        # 此检查主要在创建新记录 (self.instance is None) 时执行。
        input_has_f_slot = any(
            str(slot.get('start_time_str', '')).strip().upper() == 'F'
            for slot in (slots_data if slots_data else []) # Ensure slots_data is iterable
        )

        if input_has_f_slot: # Check if input contains an 'F' slot
            customer_instance = data.get('customer') 
            outer_box_date_obj = data.get('outer_box_date')

            if customer_instance and outer_box_date_obj:
                query_params = {
                    'customer': customer_instance,
                    'material_number': data.get('material_number'),
                    'outer_box_date': outer_box_date_obj,
                    'batch_number': data.get('batch_number'),
                    'specification': data.get('specification'),
                    'packaging_line': data.get('packaging_line'),
                }

                # Ensure all parts of the key for the duplicate check are present in the input data
                # If any key part is missing, this specific duplicate check cannot be reliably performed.
                # Field-level validators ('required=True', 'allow_blank=False') should catch missing mandatory fields earlier.
                mandatory_keys_for_check = ['customer', 'material_number', 'outer_box_date', 'batch_number', 'specification', 'packaging_line']
                # We use .get() for 'data' because it's the raw input. customer is already resolved.
                all_keys_present = all(
                    (k == 'customer' and data.get(k) is not None) or \
                    (k != 'customer' and data.get(k) is not None and str(data.get(k)).strip() != '')
                    for k in mandatory_keys_for_check
                )

                if all_keys_present:
                    # Query for existing shipments with the same core fields AND an 'F' slot
                    existing_f_records_query = Shipment.objects.filter(
                        **query_params, 
                        production_time_slots__start_time_str__iexact='F'
                    )

                    if self.instance: # If updating an existing shipment
                        # Exclude the current instance being updated from the check
                        existing_f_records_query = existing_f_records_query.exclude(pk=self.instance.pk)
                    
                    if existing_f_records_query.exists():
                        raise serializers.ValidationError(
                             "警告：系统中已存在另一条具有相同关键信息（日期、客户、物料、批次、包装线）且生产时间为 'F' 的流向记录。请检查输入或先修改/删除旧记录。"
                        )
        return data

    def create(self, validated_data):
        # Pop the nested slot data before creating the Shipment instance
        # The 'source' on production_time_slots_input means validated_data may contain 'production_time_slots' key
        slots_data = validated_data.pop('production_time_slots', [])

        shipment = Shipment.objects.create(**validated_data)

        for slot_data_item in slots_data: # Renamed to avoid conflict
            ProductionTimeSlot.objects.create(shipment=shipment, **slot_data_item)

        shipment.refresh_from_db() # Refresh to ensure related slots are loaded for the response
        return shipment

    def update(self, instance, validated_data):
        # Pop the nested slot data
        slots_data = validated_data.pop('production_time_slots', None)
        
        # Update Shipment instance fields (standard update logic)
        # This loop handles all fields in validated_data that are direct attributes of Shipment
        for attr, value in validated_data.items():
            # Special handling for 'customer' if 'customer_id' was used and resolved
            # by PrimaryKeyRelatedField with source='customer'
            if attr == 'customer' and isinstance(value, Customer): # value will be a Customer instance due to source='customer'
                 setattr(instance, attr, value)
            elif hasattr(instance, attr): # Check if it's a direct attribute
                setattr(instance, attr, value)
        
        instance.save() # Save the Shipment instance first

        # Handle updates to production_time_slots
        # CORRECTED BEHAVIOR FOR EDIT: Replace all existing slots with the new set.
        if slots_data is not None:
            # First, delete all existing time slots for this shipment.
            instance.production_time_slots.all().delete()
            
            # Then, create new time slots from the provided validated data.
            for slot_data_item in slots_data:
                ProductionTimeSlot.objects.create(shipment=instance, **slot_data_item)
        else:
            # If slots_data is explicitly None (e.g., not provided in a partial update meant to clear slots),
            # and the business logic requires clearing slots if an empty list or null is passed,
            # you might still want to delete existing slots.
            # However, if 'production_time_slots' is simply omitted from the request payload
            # during a partial update, slots_data will be None, and we might not want to touch existing slots.
            # The current behavior (if slots_data is None, do nothing to slots) is often desired for partial updates
            # where only other fields of the shipment are being modified.
            # If an empty list [] is passed for slots_data, the above loop won't run, and existing slots would have been deleted,
            # effectively clearing all slots, which is correct.
            pass
        
        instance.refresh_from_db() # Refresh to ensure all related slots (old and new) are loaded
        return instance
