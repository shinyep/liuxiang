from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Customer, Shipment, ProductionTimeSlot
from .serializers import CustomerSerializer, ShipmentSerializer

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from django.db import transaction
import openpyxl
from datetime import datetime
import re
from django.db.models import Count, Sum, F, Case, When, Value, ExpressionWrapper, FloatField, CharField, Q
from django.db.models.functions import Cast
from django.db.models import IntegerField
from django.http import JsonResponse
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.conf import settings
import os
import shutil

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'area_code']

    @action(detail=False, methods=['get'], url_path='by-area-code/(?P<area_code>[^/.]+)')
    def by_area_code(self, request, area_code=None):
        try:
            customer = Customer.objects.get(area_code=area_code)
            serializer = self.get_serializer(customer)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found with this area code"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ShipmentViewSet(viewsets.ModelViewSet):
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = (
            Shipment.objects
            .select_related('customer')
            .prefetch_related('production_time_slots')
            .order_by('-outer_box_date', '-id')
        )
        year = self.request.query_params.get('year')
        if year:
            try:
                year_int = int(year)
                # 逻辑：如果 shipment_date 存在，则匹配其年份；
                # 如果 shipment_date 为空，则匹配 outer_box_date 的年份。
                # 这与前端显示逻辑 (shipment_date || outer_box_date) 一致。
                queryset = queryset.filter(
                    Q(shipment_date__year=year_int) | 
                    Q(shipment_date__isnull=True, outer_box_date__year=year_int)
                )
            except ValueError:
                pass # 如果年份格式不正确，忽略过滤器，返回所有（或可以处理为返回空）
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        customer_id = data.get('customer_id')
        area_code = str(data.get('area_code', '') or '').strip()
        customer_name = str(data.get('customer_name', '') or '').strip()
        shipping_address = str(data.get('shipping_address', '') or '').strip()
        material_number = data.get('material_number')
        material_description = data.get('material_description')
        # shipment_date_str is what frontend sends as "发货日期"
        # outer_box_date_str is what frontend sends as "外箱日期"
        # For matching, we will use outer_box_date as the primary date field in the DB model.
        shipment_date_str = data.get('shipment_date') 
        outer_box_date_str = data.get('outer_box_date')
        batch_number = data.get('batch_number')
        specification = data.get('specification')
        packaging_line = data.get('packaging_line')
        # Corrected to match the key sent by the frontend,
        # which will then be correctly handled by the serializer's 'source' mapping.
        production_slots_input = data.get('production_time_slots', [])

        # Basic validation for non-customer key fields
        if not all([material_number, material_description, outer_box_date_str, batch_number, specification, packaging_line]):
            return Response({
                "error": "Missing one or more key fields for matching/creating (material_number, material_description, outer_box_date, batch_number, specification, packaging_line)."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 客户处理：如果没有 customer_id，用 area_code 查找或自动创建只有区域码的客户
        if not customer_id:
            if not area_code:
                return Response({
                    "error": "请提供区域码（area_code）或有效的客户ID（customer_id）。"
                }, status=status.HTTP_400_BAD_REQUEST)
            customer_obj, created = Customer.objects.get_or_create(
                area_code=area_code,
                defaults={
                    'name': customer_name,
                    'shipping_address': shipping_address,
                }
            )
            customer_id = customer_obj.id
            if created:
                print(f"Auto-created customer for area_code={area_code}, id={customer_id}")

        # 构建可变数据副本，注入解析后的 customer_id
        mutable_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        mutable_data['customer_id'] = customer_id

        try:
            # Convert date strings to date objects for consistent querying
            # The shipment_date from frontend is primarily for UI display; outer_box_date is used for DB matching.
            # If shipment_date is not provided, it defaults to outer_box_date in the serializer.
            # For matching, we strictly use outer_box_date.
            outer_box_date_for_match = datetime.strptime(outer_box_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format for outer_box_date. Expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Prepare shipment_date for matching if provided
                shipment_date_for_match = None
                if shipment_date_str:
                    try:
                        shipment_date_for_match = datetime.strptime(shipment_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        return Response({"error": "Invalid date format for shipment_date. Expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
                
                # Build the filter query
                query_filters = Q(
                    customer_id=customer_id,
                    material_number=material_number,
                    material_description=material_description,
                    outer_box_date=outer_box_date_for_match,
                    batch_number=batch_number,
                    specification=specification,
                    packaging_line=packaging_line
                )
                
                # Add shipment_date to the filter only if it's provided and valid
                # If shipment_date_for_match is None (because shipment_date_str was empty/null), 
                # we match records where shipment_date in DB is also NULL.
                # If shipment_date_for_match has a date, we match that specific date.
                query_filters &= Q(shipment_date=shipment_date_for_match)

                existing_shipment = Shipment.objects.filter(query_filters).first()

                if existing_shipment:
                    # MODIFICATION: Handle slot "appending" directly here for POST requests that match an existing shipment.
                    # The serializer's update method (called by PUT) will now handle full replacement for editing.
                    # This separates the "append" logic for continuous entry from the "replace" logic for editing.
                    
                    new_slots_data = request.data.get('production_time_slots', [])
                    if not new_slots_data:
                        # If no new slots are provided, just return the existing shipment data.
                        serializer = self.get_serializer(existing_shipment)
                        return Response(serializer.data, status=status.HTTP_200_OK)

                    existing_start_times = set(existing_shipment.production_time_slots.values_list('start_time_str', flat=True))
                    
                    added_slots_count = 0
                    for slot_data in new_slots_data:
                        start_time = slot_data.get('start_time_str')
                        if start_time and start_time not in existing_start_times:
                            ProductionTimeSlot.objects.create(shipment=existing_shipment, **slot_data)
                            existing_start_times.add(start_time) # Avoid duplicates from the same request
                            added_slots_count += 1
                    
                    if added_slots_count > 0:
                        existing_shipment.refresh_from_db()

                    serializer = self.get_serializer(existing_shipment)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    # No existing shipment found, proceed with normal creation using the serializer
                    # Use mutable_data which has the resolved customer_id injected
                    serializer = self.get_serializer(data=mutable_data)
                    serializer.is_valid(raise_exception=True)
                    self.perform_create(serializer)
                    headers = self.get_success_headers(serializer.data)
                    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            # Log the exception e for debugging
            print(f"Error in ShipmentViewSet create: {str(e)}")
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='clear-all')
    def clear_all_shipments(self, request):
        try:
            slots_total_deleted, slots_deleted_details_dict = ProductionTimeSlot.objects.all().delete()
            slots_deleted_count = slots_deleted_details_dict.get('api.ProductionTimeSlot', 0)
            
            shipments_total_deleted, shipments_deleted_details_dict = Shipment.objects.all().delete()
            shipments_deleted_count = shipments_deleted_details_dict.get('api.Shipment', 0)
            
            message = f"数据清空尝试：删除了 {slots_deleted_count} 条生产时间段记录，以及 {shipments_deleted_count} 条流向记录。"
            return Response({"message": message}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"清空数据时发生严重错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ShipmentImportView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        sheet_name_or_index = request.data.get('sheet', 0)

        if not file_obj: return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        if not file_obj.name.endswith(('.xlsx')): return Response({"error": "Invalid file format. Please upload an XLSX file."}, status=status.HTTP_400_BAD_REQUEST)

        try: workbook = openpyxl.load_workbook(file_obj, data_only=True)
        except Exception as e: return Response({"error": f"Error opening workbook: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if isinstance(sheet_name_or_index, str) and sheet_name_or_index.strip(): worksheet = workbook[sheet_name_or_index.strip()]
            else: worksheet = workbook.active 
        except KeyError: return Response({"error": f"Sheet '{sheet_name_or_index}' not found."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e: return Response({"error": f"Error accessing sheet: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        imported_count, error_count, errors = 0, 0, []
        
        COL_IDX = { 'outer_box_date': 0, 'area_code': 1, 'customer_name': 2, 'shipping_address': 3, 
                    'material_number': 4, 'material_description': 5, 'production_date_code': 6, 'batch_number': 7, 
                    'specification_quantity': 8, 'packaging_line': 9, 'time_slot_start_col': 10, 'num_time_slots': 10 }
        
        HEADER_KEYWORDS = {"发货日期", "区域码", "客户名称", "外箱日期"} # Case-sensitive for now, adjust if needed

        def get_cell_value_from_row(row_tuple, col_idx, default_val=''):
            val = row_tuple[col_idx] if col_idx < len(row_tuple) and row_tuple[col_idx] is not None else default_val
            return str(val).strip()

        try:
            with transaction.atomic():
                for i, row_cells_tuple in enumerate(worksheet.iter_rows(min_row=1, values_only=True)): # Always iterate from actual row 1
                    row_number_in_sheet = i + 1 # 1-based row number for user messages
                    
                    try:
                        # Get key values for header/empty row check first
                        potential_header_val = get_cell_value_from_row(row_cells_tuple, COL_IDX['outer_box_date'])
                        area_code_check = get_cell_value_from_row(row_cells_tuple, COL_IDX['area_code'])
                        material_number_check = get_cell_value_from_row(row_cells_tuple, COL_IDX['material_number'])

                        if potential_header_val in HEADER_KEYWORDS: continue # Skip header row
                        if not area_code_check and not material_number_check: continue # Skip likely empty data row
                        
                        # Now proceed to get all values for the row
                        area_code = area_code_check # Already fetched
                        customer_name_excel = get_cell_value_from_row(row_cells_tuple, COL_IDX['customer_name'])
                        shipping_address_excel = get_cell_value_from_row(row_cells_tuple, COL_IDX['shipping_address'])
                        material_number = material_number_check # Already fetched
                        material_description = get_cell_value_from_row(row_cells_tuple, COL_IDX['material_description'])
                        outer_box_date_raw = potential_header_val # This was the outer_box_date cell
                        production_date_code = get_cell_value_from_row(row_cells_tuple, COL_IDX['production_date_code'])
                        batch_number = get_cell_value_from_row(row_cells_tuple, COL_IDX['batch_number'])
                        specification_raw = get_cell_value_from_row(row_cells_tuple, COL_IDX['specification_quantity'])
                        packaging_line = get_cell_value_from_row(row_cells_tuple, COL_IDX['packaging_line'])

                        if not area_code: errors.append(f"Row {row_number_in_sheet}: Missing Area Code. Customer Name: '{customer_name_excel}', Material: '{material_number}'."); error_count += 1; continue
                        # Customer name and address can be blank if area_code exists
                        
                        if not material_number: errors.append(f"Row {row_number_in_sheet} (Cust: {area_code}): Missing Material Number."); error_count += 1; continue
                        
                        outer_box_date_obj = None
                        if isinstance(outer_box_date_raw, datetime):
                            outer_box_date_obj = outer_box_date_raw.date()
                        elif isinstance(outer_box_date_raw, str):
                            # Try common datetime formats
                            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', 
                                        '%Y-%m-%d', '%Y/%m/%d',
                                        '%m/%d/%Y %H:%M:%S', '%m/%d/%Y'):
                                try:
                                    outer_box_date_obj = datetime.strptime(outer_box_date_raw, fmt).date()
                                    break 
                                except ValueError:
                                    continue
                        # Fallback for Excel serial dates (numbers)
                        if not outer_box_date_obj and isinstance(outer_box_date_raw, (int, float)):
                            try:
                                outer_box_date_obj = openpyxl.utils.datetime.from_excel(outer_box_date_raw).date()
                            except:
                                pass
                        
                        if not outer_box_date_obj: 
                            errors.append(f"Row {row_number_in_sheet} (Cust: {area_code}): Invalid/missing Outer Box Date. Value: '{outer_box_date_raw}'. Could not parse as date.")
                            error_count += 1
                            continue
                        
                        customer, _ = Customer.objects.get_or_create(area_code=area_code, defaults={'name': customer_name_excel, 'shipping_address': shipping_address_excel})
                        # Always update if name/address from Excel is different and not blank, or if current DB is blank
                        if (customer_name_excel and customer.name != customer_name_excel) or \
                           (shipping_address_excel and customer.shipping_address != shipping_address_excel) or \
                           (not customer.name and customer_name_excel) or \
                           (not customer.shipping_address and shipping_address_excel) :
                            if customer_name_excel : customer.name = customer_name_excel
                            if shipping_address_excel : customer.shipping_address = shipping_address_excel
                            customer.save()
                        
                        slot_quantity_str = str(specification_raw).strip()
                        slot_quantity = 0
                        if slot_quantity_str: # If not empty
                            try: 
                                slot_quantity_float = float(slot_quantity_str)
                                if slot_quantity_float < 0: raise ValueError("Quantity cannot be negative")
                                slot_quantity = int(slot_quantity_float) # Convert to int after ensuring it's a valid number
                            except ValueError: errors.append(f"Row {row_number_in_sheet} (Cust: {area_code}): Invalid Spec/Qty value '{specification_raw}'. Must be a non-negative number."); error_count += 1; continue
                        
                        shipment = Shipment(customer=customer, material_number=material_number, material_description=material_description, outer_box_date=outer_box_date_obj, 
                                            production_date_code=production_date_code, batch_number=batch_number, specification=str(specification_raw), packaging_line=packaging_line)
                        
                        slots_to_create, row_had_any_slot_text = [], False
                        for slot_i in range(COL_IDX['num_time_slots']):
                            time_raw_orig = get_cell_value_from_row(row_cells_tuple, COL_IDX['time_slot_start_col'] + slot_i)
                            if not time_raw_orig: continue
                            row_had_any_slot_text = True
                            
                            time_raw_cleaned = re.sub(r'\s+', '', time_raw_orig) 
                            time_raw_cleaned = re.sub(r'-+', '-', time_raw_cleaned).strip('-') 

                            s_time, e_time = '', ''
                            if time_raw_cleaned.upper() == 'F': s_time = 'F'
                            else:
                                parts = time_raw_cleaned.split('-')
                                if len(parts) == 1 and parts[0]: 
                                    part_val = parts[0]
                                    if not part_val.isdigit(): errors.append(f"Row {row_number_in_sheet}, Slot {slot_i+1}: Single time part '{part_val}' in '{time_raw_orig}' is not numeric."); continue
                                    if len(part_val) > 4: errors.append(f"Row {row_number_in_sheet}, Slot {slot_i+1}: Single time part '{part_val}' in '{time_raw_orig}' is too long (max 4 digits)."); continue
                                    s_time = part_val.zfill(4)
                                    if not (int(s_time[:2]) < 24 and int(s_time[2:]) < 60): errors.append(f"Row {row_number_in_sheet}, Slot {slot_i+1}: Invalid HHMM '{s_time}' from '{time_raw_orig}'. Hrs<24, Min<60."); s_time = ''; continue # Mark as invalid
                                elif len(parts) == 2 and parts[0] and parts[1]: 
                                    s_part, e_part = parts[0], parts[1]
                                    if not s_part.isdigit(): errors.append(f"Row {row_number_in_sheet}, Slot {slot_i+1}: Start time part '{s_part}' in '{time_raw_orig}' is not numeric."); continue
                                    if len(s_part) > 4: errors.append(f"Row {row_number_in_sheet}, Slot {slot_i+1}: Start time part '{s_part}' in '{time_raw_orig}' is too long."); continue
                                    s_time = s_part.zfill(4)

                                    if not e_part.isdigit(): errors.append(f"Row {row_number_in_sheet}, Slot {slot_i+1}: End time part '{e_part}' in '{time_raw_orig}' is not numeric."); continue
                                    if len(e_part) > 4: errors.append(f"Row {row_number_in_sheet}, Slot {slot_i+1}: End time part '{e_part}' in '{time_raw_orig}' is too long."); continue
                                    e_time = e_part.zfill(4)
                                    
                                    if not (int(s_time[:2])<24 and int(s_time[2:])<60 and int(e_time[:2])<24 and int(e_time[2:])<60):
                                        errors.append(f"Row {row_number_in_sheet}, Slot {slot_i+1}: Invalid HHMM range '{s_time}-{e_time}' from '{time_raw_orig}'. Hrs<24, Min<60."); s_time = ''; e_time = ''; continue
                                else: errors.append(f"Row {row_number_in_sheet}, Slot {slot_i+1}: Unrecognized time structure '{time_raw_orig}'. Problem with parts: {parts}"); continue
                            
                            if s_time: # Only add if s_time was successfully parsed
                                slots_to_create.append(ProductionTimeSlot(start_time_str=s_time, end_time_str=e_time, quantity=slot_quantity))

                        # Determine if shipment should be saved and if slots should be saved
                        save_shipment_flag = False
                        save_slots_flag = False

                        if slots_to_create:
                            # Case 1: Valid production time slots were parsed
                            save_shipment_flag = True
                            save_slots_flag = True
                        else:
                            # Case 2: No valid production time slots were parsed
                            # Check if spec/qty is present to justify saving the shipment without slots
                            if bool(slot_quantity_str): # slot_quantity_str is from parsed specification_raw
                                save_shipment_flag = True # Save shipment, but no slots
                                # Add an informational message
                                if row_had_any_slot_text: # Slots were attempted but failed
                                    errors.append(f"Row {row_number_in_sheet} (Cust: {area_code}): Info: Had time slot text, but none were valid. Shipment saved without time slots due to present spec/qty.")
                                else: # No slot text was provided at all
                                    errors.append(f"Row {row_number_in_sheet} (Cust: {area_code}): Info: No time slots provided. Shipment saved without time slots due to spec/qty.")
                            else:
                                # Case 3: No slots AND no spec/qty - this is an error, skip row
                                if row_had_any_slot_text: # Slots were attempted but failed
                                    errors.append(f"Row {row_number_in_sheet} (Cust: {area_code}): Had time slot text, but none were valid after parsing (and no spec/qty).")
                                else: # No slot text was provided at all
                                    errors.append(f"Row {row_number_in_sheet} (Cust: {area_code}): No production time slots were successfully parsed or provided (and no spec/qty).")
                                error_count += 1
                                continue # Skip this row from being processed further in the current iteration

                        # If the code reaches here, it means either the row is being skipped (due to 'continue'),
                        # or save_shipment_flag is True (with or without slots).
                        
                        if save_shipment_flag:
                            shipment.save()
                            if save_slots_flag: # This will be true only if slots_to_create is non-empty
                                for slot_obj in slots_to_create:
                                    slot_obj.shipment = shipment
                                    slot_obj.save()
                            imported_count += 1
                        # If save_shipment_flag is false, it means an error occurred and 'continue' was hit.
                    except Exception as e_row:
                        errors.append(f"Row {row_number_in_sheet}: Critical error '{str(e_row)}'. Skipped.")
                        error_count += 1; continue
            # End transaction
        except Exception as e_transaction:
            return Response({"error": "Critical DB transaction error.", "detail": str(e_transaction)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_status = status.HTTP_200_OK
        if imported_count > 0 and error_count == 0: response_status = status.HTTP_201_CREATED
        elif imported_count > 0 and error_count > 0: response_status = status.HTTP_207_MULTI_STATUS
        elif imported_count == 0 and error_count > 0: response_status = status.HTTP_400_BAD_REQUEST
        elif imported_count == 0 and error_count == 0 and not errors : errors.append("No data rows found or processed.")

        return Response({"message": f"Import finished. {imported_count} records imported. {error_count} records failed/skipped.", "errors": errors}, status=response_status)


class ShipmentStatisticsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Provides statistics on shipments, grouped by shipment date, customer name, and material description.
        The 'quantity' is the count of shipment records for each group.
        """
        try:
            # Step 1: Group shipments by date, customer, and material
            # We can't directly annotate with the complex calculation in one go with .values().annotate()
            # So, we'll fetch relevant shipments and then process them.
            
            # Get all unique combinations of shipment_date, customer_area_code, customer_name, material_description
            grouping_keys = Shipment.objects.values_list(
                'shipment_date',
                'customer__area_code', 
                'customer__name', 
                'material_description'
            ).distinct().order_by('-shipment_date', 'customer__area_code', 'customer__name', 'material_description')

            result_list = []

            for key_tuple in grouping_keys:
                s_date, cust_area_code, cust_name, mat_desc = key_tuple
                
                # Get all shipments for the current group
                shipments_in_group = Shipment.objects.filter(
                    shipment_date=s_date,
                    customer__area_code=cust_area_code,
                    customer__name=cust_name,
                    material_description=mat_desc
                ).prefetch_related('production_time_slots') # Important for performance

                group_total_quantity = 0
                for shipment_item in shipments_in_group:
                    try:
                        specification_val = int(shipment_item.specification) if shipment_item.specification else 0
                    except ValueError:
                        specification_val = 0 # Handle cases where specification is not a valid integer

                    # Count valid production time slots for this specific shipment_item
                    # A slot is valid if start_time_str is not empty and not 'F'
                    valid_time_slots_for_shipment = shipment_item.production_time_slots.filter(
                        Q(start_time_str__isnull=False) &
                        ~Q(start_time_str__exact='') &
                        ~Q(start_time_str__iexact='F')
                    ).count()

                    group_total_quantity += specification_val * valid_time_slots_for_shipment
                
                if group_total_quantity > 0 or shipments_in_group.exists(): # Add if there's quantity or if the group existed
                    result_list.append({
                        'shipment_date': s_date.strftime('%Y-%m-%d') if s_date else None,
                        'customer_area_code': cust_area_code,
                        'customer_name': cust_name,
                        'item_name': mat_desc,
                        'total_quantity': group_total_quantity
                    })

            return Response(result_list, status=status.HTTP_200_OK)
        except Exception as e:
            # Log the exception e for debugging
            print(f"Error in ShipmentStatisticsView: {str(e)}")
            return Response({"error": f"An error occurred while fetching statistics: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MaterialShipmentStatisticsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        year = request.query_params.get('year')
        month = request.query_params.get('month') # New month parameter

        shipments_query = Shipment.objects.all()

        if year:
            try:
                year_int = int(year)
                # Filtering based on shipment_date for year
                shipments_query = shipments_query.filter(shipment_date__year=year_int)
            except ValueError:
                return Response({"error": "Invalid year format. Please provide an integer year."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Year parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if month: 
            try:
                month_int = int(month)
                if month_int != 0: # 0 means 'All Months'
                    if not (1 <= month_int <= 12):
                        return Response({"error": "Invalid month. Must be between 1 and 12 (or 0 for all months)."}, status=status.HTTP_400_BAD_REQUEST)
                    # Filtering based on shipment_date for month
                    shipments_query = shipments_query.filter(shipment_date__month=month_int)
            except ValueError:
                return Response({"error": "Invalid month format. Please provide an integer month (0-12)."}, status=status.HTTP_400_BAD_REQUEST)


        # Annotate each shipment with the count of its 'valid' production time slots
        # A slot is valid if start_time_str is not empty and not 'F'
        shipments_with_valid_slots_and_spec = shipments_query.annotate(
            valid_slot_count=Count(
                'production_time_slots',
                filter=Q(production_time_slots__start_time_str__isnull=False) &
                       ~Q(production_time_slots__start_time_str__exact='') &
                       ~Q(production_time_slots__start_time_str__iexact='F')
            )
        ).values( # Select only necessary fields for further processing in Python
            'material_number',
            'material_description',
            'specification', # Keep as string for now
            'valid_slot_count'
        )

        # Aggregate in Python to safely handle specification conversion
        material_summary = {}
        for item in shipments_with_valid_slots_and_spec:
            key = (item['material_number'], item['material_description'])
            if key not in material_summary:
                material_summary[key] = {
                    'material_number': item['material_number'],
                    'material_description': item['material_description'],
                    'total_shipped_quantity': 0.0
                }
            
            try:
                spec_float = float(item['specification']) if item['specification'] else 0.0
            except ValueError:
                spec_float = 0.0 # Treat non-numeric specification as 0 for this calculation
            
            material_summary[key]['total_shipped_quantity'] += spec_float * item['valid_slot_count']

        # Convert total_shipped_quantity to int and sort
        final_material_stats = []
        for data_item in material_summary.values(): # Renamed data to data_item to avoid conflict
            data_item['total_shipped_quantity'] = int(round(data_item['total_shipped_quantity']))
            final_material_stats.append(data_item)
        
        sorted_material_stats = sorted(final_material_stats, key=lambda x: x['material_number'])
        
        return Response(sorted_material_stats, status=status.HTTP_200_OK)

class CustomerShipmentStatisticsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        if not year:
            return Response({"error": "Year parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        shipments_query = Shipment.objects.all()

        try:
            year_int = int(year)
            shipments_query = shipments_query.filter(shipment_date__year=year_int)
        except ValueError:
            return Response({"error": "Invalid year format."}, status=status.HTTP_400_BAD_REQUEST)

        if month:
            try:
                month_int = int(month)
                if month_int != 0: # 0 means 'All Months'
                    if not (1 <= month_int <= 12):
                        return Response({"error": "Invalid month. Must be between 1 and 12."}, status=status.HTTP_400_BAD_REQUEST)
                    shipments_query = shipments_query.filter(shipment_date__month=month_int)
            except ValueError:
                return Response({"error": "Invalid month format."}, status=status.HTTP_400_BAD_REQUEST)

        # Annotate with valid slot count and specification value
        shipments_with_details = shipments_query.annotate(
            valid_slot_count=Count(
                'production_time_slots',
                filter=Q(production_time_slots__start_time_str__isnull=False) &
                       ~Q(production_time_slots__start_time_str__exact='') &
                       ~Q(production_time_slots__start_time_str__iexact='F')
            )
        ).values(
            'customer__area_code',
            'customer__name',
            'customer__shipping_address',
            'material_number',
            'material_description',
            'specification',
            'valid_slot_count'
        )

        # Aggregate in Python
        customer_summary = {}
        for item in shipments_with_details:
            key = (
                item['customer__area_code'],
                item['customer__name'],
                item['customer__shipping_address'],
                item['material_number'],
                item['material_description']
            )
            
            if key not in customer_summary:
                customer_summary[key] = {
                    'area_code': item['customer__area_code'],
                    'customer_name': item['customer__name'],
                    'shipping_address': item['customer__shipping_address'],
                    'material_number': item['material_number'],
                    'material_description': item['material_description'],
                    'quantity': 0
                }
            
            try:
                spec_float = float(item['specification']) if item['specification'] else 0.0
            except ValueError:
                spec_float = 0.0
            
            customer_summary[key]['quantity'] += spec_float * item['valid_slot_count']

        final_stats = [
            {**data, 'quantity': int(round(data['quantity']))}
            for data in customer_summary.values()
        ]
        
        sorted_stats = sorted(final_stats, key=lambda x: (x['area_code'], x['customer_name'], x['material_number']))

        return Response(sorted_stats, status=status.HTTP_200_OK)


class UniqueMaterialsView(APIView):
    """
    Provides a list of unique materials (number and description) that exist in shipments.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            unique_materials = Shipment.objects.values(
                'material_number',
                'material_description'
            ).distinct().order_by('material_number')
            
            return Response(list(unique_materials), status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error in UniqueMaterialsView: {str(e)}")
            return Response({"error": "An error occurred while fetching unique materials."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DatabaseBackupView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        db_path = settings.DATABASES['default']['NAME']
        if os.path.exists(db_path):
            with open(db_path, 'rb') as db_file:
                response = HttpResponse(db_file.read(), content_type='application/x-sqlite3')
                response['Content-Disposition'] = 'attachment; filename="db.sqlite3"'
                return response
        else:
            return Response({"error": "Database file not found."}, status=status.HTTP_404_NOT_FOUND)

class DatabaseImportView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = (MultiPartParser,)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        if not file_obj.name.endswith('.sqlite3'):
            return Response({"error": "Invalid file format. Please upload a .sqlite3 file."}, status=status.HTTP_400_BAD_REQUEST)

        db_path = settings.DATABASES['default']['NAME']
        
        try:
            # It's safer to write to a temporary file first
            temp_path = db_path + '.tmp'
            with open(temp_path, 'wb+') as temp_file:
                for chunk in file_obj.chunks():
                    temp_file.write(chunk)
            
            # Replace the original file with the new one
            shutil.move(temp_path, db_path)
            
            return Response({"message": "Database imported successfully. The server may need to be restarted."}, status=status.HTTP_200_OK)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return Response({"error": f"An error occurred during import: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
