<template>
  <div class="shipment-tracking">
    <h2>成品流向系统</h2>

    <div class="page-actions-bar">
      <div>
        <button @click="openAddShipmentModal" class="btn-action btn-primary">添加新流向记录</button>
        <button @click="openImportModal" class="btn-action btn-secondary">从XLSX导入</button>
        <button @click="backupDatabase" class="btn-action btn-info">备份数据库</button>
        <button @click="openImportDBModal" class="btn-action btn-warning">导入数据库</button>
      </div>
      <div class="year-selector">
        <label for="year-select">选择年份:</label>
        <select id="year-select" v-model="selectedYear" @change="fetchShipments" class="year-select-input">
          <option v-for="year in availableYears" :key="year" :value="year">{{ year }}年</option>
        </select>
      </div>
      <div class="export-controls">
        <label for="export-start-date">开始日期:</label>
        <input type="date" id="export-start-date" v-model="exportStartDate" class="date-filter-input" :max="today">
        <label for="export-end-date">结束日期:</label>
        <input type="date" id="export-end-date" v-model="exportEndDate" class="date-filter-input" :max="today">
        <button @click="exportToXLSX" class="btn-action btn-success">导出为XLSX</button>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="isAddShipmentModalVisible" class="modal-overlay">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>{{ modalTitle }}</h3>
          <button @click="closeAddShipmentModal" class="modal-close-button" aria-label="关闭">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="handleAddShipmentSubmit" class="shipment-form-in-modal">
            <div class="form-grid">
              <div>
                <label for="modal-shipment-date">发货日期:</label>
                <input type="date" id="modal-shipment-date" v-model="newShipment.shipment_date" :max="today" />
              </div>
              <div>
                <label for="modal-shipment-area-code">区域码:</label>
                <input type="text" id="modal-shipment-area-code" v-model="newShipment.area_code" @blur="fetchCustomerByAreaCode" placeholder="输入区域码自动填充" />
              </div>
              <div>
                <label for="modal-shipment-customer-name">客户名称:</label>
                <input type="text" id="modal-shipment-customer-name" v-model="newShipment.customer_name" readonly />
              </div>
              <div>
                <label for="modal-shipment-shipping-address">送货地址:</label>
                <textarea id="modal-shipment-shipping-address" v-model="newShipment.shipping_address" readonly></textarea>
              </div>
              <div>
                <label for="modal-material-select">选择物料:</label>
                <select id="modal-material-select" v-model="selectedMaterial" @change="updateMaterialDetails" required>
                  <option disabled value="">请选择一个物料</option>
                  <option v-for="material in materials" :key="material.number" :value="material">
                    {{ material.number }} - {{ material.description }}
                  </option>
                </select>
              </div>
              <div>
                <label for="modal-material-number-display">物料编号:</label>
                <input type="text" id="modal-material-number-display" v-model="newShipment.material_number" readonly required />
              </div>
              <div>
                <label for="modal-material-description-display">物料描述:</label>
                <input type="text" id="modal-material-description-display" v-model="newShipment.material_description" readonly required />
              </div>
              <div>
                <label for="modal-outer-box-date">外箱日期:</label>
                <input type="date" id="modal-outer-box-date" v-model="newShipment.outer_box_date" :max="today" required />
              </div>
              <div>
                <label for="modal-batch-number">批次:</label>
                <input 
                  type="text" 
                  id="modal-batch-number" 
                  v-model="newShipment.batch_number" 
                  placeholder="例: 1.31" 
                  pattern="^[1-9]|1[0-2]\.[1-9]|[1-9]\.[1-9]$|^[1-9]|1[0-2]\.[1-2][0-9]|^[1-9]|1[0-2]\.3[01]$" 
                  required 
                  novalidate
                  :class="{ 'input-error': batchFormatError }" 
                />
                <span class="field-hint">格式: 月.日（如 1.31）</span>
                <span v-if="batchFormatError" class="field-error">格式错误：应为 月.日，如 1.31</span>
              </div>
              <div>
                <label for="modal-specification">规格 (每板箱数):</label>
                <input type="text" id="modal-specification" v-model="newShipment.specification" required />
              </div>
              <div>
                <label for="modal-packaging-line">包装线:</label>
                <select id="modal-packaging-line" v-model="newShipment.packaging_line" required>
                  <option value="A">A</option>
                  <option value="B">B</option>
                  <option value="C">C</option>
                </select>
              </div>
            </div>
             <p v-if="customerFetchError" class="error-message modal-error">{{ customerFetchError }}</p>
            <div class="production-slots-form-in-modal section-block-modal">
              <h4>生产时间段详情</h4>
              <!-- <button type="button" @click="addProductionSlotRow" class="btn-add-slot">添加生产时间段</button> -->
              <div v-for="(slot, index) in newShipment.production_slots" :key="index" class="production-slot-row form-grid-slots">
                <div>
                  <label :for="'modal-slot-start-' + index">开始时间 (HHMM):</label>
                  <input type="text" :id="'modal-slot-start-' + index" v-model="slot.start_time_str" placeholder="例如: 1648" maxlength="4" @keydown="handleFormNavigation($event, 'production_slots', index, 'start_time_str')" />
                </div>
                <div>
                  <label :for="'modal-slot-end-' + index">结束时间 (HHMM):</label>
                  <input type="text" :id="'modal-slot-end-' + index" v-model="slot.end_time_str" placeholder="例如: 1713" maxlength="4" @keydown="handleFormNavigation($event, 'production_slots', index, 'end_time_str')" />
                </div>
                <button type="button" @click="removeProductionSlotRow(index)" class="btn-remove-slot" tabindex="-1">移除</button> <!-- tabindex -1 to exclude from default tab order for consistency with arrow nav -->
              </div>
              <p v-if="newShipment.production_slots.length === 0" style="text-align: center; margin-top: 10px;">请添加至少一个生产时间段。</p>
            </div>
             <pre v-if="addError" class="error-message modal-error">{{ addError }}</pre>
            <button type="submit" style="display: none;"></button> <!-- Hidden submit button for form submission on enter -->
          </form>
        </div>
        <div class="modal-footer">
          <!-- 追加时间段模式（409 后出现） -->
          <template v-if="existingRecordIdForAppend">
            <button @click="appendTimeSlots" class="btn-action btn-warning" :disabled="isSubmitting">
              {{ isSubmitting ? '追加中...' : '追加时间段' }}
            </button>
            <button @click="closeAddShipmentModal" class="btn-action btn-cancel" :disabled="isSubmitting">取消</button>
          </template>
          <!-- 正常录入/编辑模式 -->
          <template v-else>
            <button @click="handleAddShipmentSubmit" class="btn-action btn-primary" :disabled="isSubmitting" @keydown="handleFormNavigation($event, 'footer_submit')">
              {{ isSubmitting ? '提交中...' : modalSubmitButtonText }}
            </button>
            <button @click="closeAddShipmentModal" class="btn-action btn-cancel" :disabled="isSubmitting">取消</button>
          </template>
        </div>
      </div>
    </div>

    <!-- XLSX Import Modal -->
    <div v-if="isImportModalVisible" class="modal-overlay" @click.self="closeImportModal">
      <div class="modal modal-md">
        <div class="modal-header">
          <h3>从XLSX导入流向记录</h3>
          <button @click="closeImportModal" class="modal-close-button" aria-label="关闭">&times;</button>
        </div>
        <div class="modal-body">
          <div class="xlsx-import-form-in-modal">
            <div>
              <label for="modal-file-upload">选择XLSX文件:</label>
              <input type="file" id="modal-file-upload" @change="handleFileUpload" accept=".xlsx" />
            </div>
            <div>
              <label for="modal-sheet-name">工作表名称 (可选):</label>
              <input type="text" id="modal-sheet-name" v-model="selectedSheetName" placeholder="例如: 2023年 (默认为第一个表)" />
            </div>
            <div v-if="importStatusMessage" class="import-status-message" :class="{'error-message': importErrors.length > 0 && !isImporting, 'success-message': importErrors.length === 0 && importStatusMessage && !isImporting, 'info-message': isImporting}">
              {{ importStatusMessage }}
            </div>
            <ul v-if="importErrors.length > 0 && !isImporting" class="import-errors error-message modal-error">
              <li v-for="(error, index) in importErrors" :key="index">{{ error }}</li>
            </ul>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="triggerImport" :disabled="!selectedFile || isImporting" class="btn-action btn-primary">
            {{ isImporting ? '正在导入...' : '开始导入' }}
          </button>
          <button @click="closeImportModal" class="btn-action btn-cancel">关闭</button>
        </div>
      </div>
    </div>

    <!-- Database Import Modal -->
    <div v-if="isImportDBModalVisible" class="modal-overlay" @click.self="closeImportDBModal">
      <div class="modal modal-md">
        <div class="modal-header">
          <h3>导入数据库</h3>
          <button @click="closeImportDBModal" class="modal-close-button" aria-label="关闭">&times;</button>
        </div>
        <div class="modal-body">
          <div class="db-import-form-in-modal">
            <p class="warning-message"><b>警告:</b> 这是一个危险操作！上传的数据库文件将完全覆盖现有数据库。请确保您已备份当前数据。</p>
            <div>
              <label for="modal-db-file-upload">选择 .sqlite3 文件:</label>
              <input type="file" id="modal-db-file-upload" @change="handleDBFileUpload" accept=".sqlite3" />
            </div>
            <div v-if="importDBStatusMessage" class="import-status-message" :class="{'error-message': importDBError, 'success-message': !importDBError && importDBStatusMessage, 'info-message': isImportingDB}">
              {{ importDBStatusMessage }}
            </div>
            <div v-if="importDBError" class="import-errors error-message modal-error">
              {{ importDBError }}
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="triggerDBImport" :disabled="!selectedDBFile || isImportingDB" class="btn-action btn-danger">
            {{ isImportingDB ? '正在导入...' : '确认导入' }}
          </button>
          <button @click="closeImportDBModal" class="btn-action btn-cancel">关闭</button>
        </div>
      </div>
    </div>

    <h3>流向记录列表</h3>
    <div class="record-count-bar">
      <span>已加载 <strong>{{ shipments.length }}</strong> 条记录（当前筛选结果 <strong>{{ shipmentsWithGroupTotals.filter(r => !r.isGroupTotalRow).length }}</strong> 条）</span>
      <span v-if="selectedYear">，显示年份：{{ selectedYear }}</span>
    </div>
    <div v-if="isLoading && shipments.length === 0 && !isAddShipmentModalVisible && !isImportModalVisible" class="loading-message">正在加载流向数据...</div>
    <div v-if="fetchError" class="error-message">{{ fetchError }}</div>
    <div v-if="deleteError" class="error-message">{{ deleteError }}</div>
    <div v-if="clearAllError" class="error-message">{{ clearAllError }}</div>

    <div class="filters-container section-block">
      <h4>筛选记录</h4>
      <div class="filter-grid">
        <div>
          <label>发货日期:</label>
          <input type="date" v-model="filters.shipment_date" />
        </div>
        <input type="text" v-model="filters.outer_box_date" placeholder="筛选外箱日期 (如 20250911)">
        <select v-model="filters.material_filter">
          <option value="">所有物料</option>
          <option v-for="item in uniqueMaterials" :key="item.value" :value="item.value">
            {{ item.text }}
          </option>
        </select>
        <select v-model="filters.packaging_line">
          <option value="">所有包装线</option>
          <option value="A">A线</option>
          <option value="B">B线</option>
          <option value="C">C线</option>
        </select>
        <input type="text" v-model="filters.batch_number" placeholder="筛选批次..." />
        <input type="text" v-model="filters.production_time" placeholder="筛选起止时间..." />
        <!-- 区域码：可输入关键字，也可从下拉列表选择 -->
        <div class="combobox-wrapper">
          <input
            type="text"
            v-model="filters.area_code"
            placeholder="筛选区域码..."
            list="area-code-list"
          />
          <datalist id="area-code-list">
            <option v-for="code in uniqueAreaCodes" :key="code" :value="code" />
          </datalist>
        </div>
        <!-- 客户名称：可输入关键字，也可从下拉列表选择 -->
        <div class="combobox-wrapper">
          <input
            type="text"
            v-model="filters.customer_name"
            placeholder="筛选客户名称..."
            list="customer-name-list"
          />
          <datalist id="customer-name-list">
            <option v-for="name in uniqueCustomerNames" :key="name" :value="name" />
          </datalist>
        </div>
        <!-- 送货地址：可输入关键字，也可从下拉列表选择 -->
        <div class="combobox-wrapper">
          <input
            type="text"
            v-model="filters.shipping_address"
            placeholder="筛选送货地址..."
            list="shipping-address-list"
          />
          <datalist id="shipping-address-list">
            <option v-for="addr in uniqueShippingAddresses" :key="addr" :value="addr" />
          </datalist>
        </div>
        <button @click="clearFilters" class="btn-action btn-secondary">清除筛选</button>
      </div>
    </div>

    <div class="table-container" ref="tableContainer">
      <table ref="actualTable">
        <thead>
          <tr>
            <th class="date-column">发货日期</th>
            <th class="area-code-column">区域码</th>
            <th class="customer-name-column">客户名称</th>
            <th class="shipping-address-column">送货地址</th>
            <th class="material-number-column">物料编号</th>
            <th class="material-description-column">物料描述</th>
            <th class="date-column">外箱日期</th>
            <th class="batch-column">批次</th>
            <th class="spec-column">规格</th>
            <th class="line-column">包装线</th>
            <template v-for="idx in max_production_slots" :key="'header-slot-' + idx">
              <th class="dynamic-slot-time-column">时间 {{ idx }}</th>
            </template>
            <th class="actions-column">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="shipmentsWithGroupTotals.length === 0 && !isLoading && !fetchError">
            <td :colspan="10 + max_production_slots" style="text-align: center;">暂无流向数据或无匹配结果。</td>
          </tr>
          <template v-for="item in shipmentsWithGroupTotals" :key="item.id">
            <tr v-if="!item.isGroupTotalRow" class="shipment-row" :class="{ 'highlight-new': item.id === lastAddedShipmentId }" :data-shipment-id="item.id">
            <td class="date-column">{{ item.shipment_date || item.outer_box_date }}</td>
            <td class="area-code-column">{{ item.customer_details.area_code }}</td>
            <td class="customer-name-column">{{ item.customer_details.name }}</td>
            <td class="shipping-address-column">{{ item.customer_details.shipping_address }}</td>
            <td class="material-number-column">{{ item.material_number }}</td>
            <td class="material-description-column">{{ item.material_description }}</td>
            <td class="date-column">{{ formatOuterBoxDateForDisplay(item.outer_box_date) }}</td>
            <td class="batch-column">{{ item.batch_number }}</td>
            <td class="spec-column">{{ item.specification }}</td>
            <td class="line-column">{{ item.packaging_line }}</td>
              <template v-for="idx in max_production_slots" :key="'data-slot-' + item.id + '-' + idx">
                <td class="dynamic-slot-time-column">
                  <span v-if="item.production_time_slots && item.production_time_slots[idx-1]">
                    <span v-if="item.production_time_slots[idx-1].start_time_str && item.production_time_slots[idx-1].start_time_str.toUpperCase() === 'F'" class="slot-f">F</span>
                    <span v-else>{{ formatSlot(item.production_time_slots[idx-1]) }}</span>
                  </span>
                </td>
              </template>
              <td class="actions-column">
                <button @click="startEditShipment(item)" class="btn-edit">编辑</button>
                <button @click="confirmDeleteShipment(item.original_id || item.id)" class="btn-delete">删除</button>
              </td>
            </tr>
            <tr v-else class="group-total-row">
              <td :colspan="6" class="total-label"><strong>车次小计 ({{ item.firstShipmentDetails.shipment_date }} - {{ item.firstShipmentDetails.customer_name }} - {{ item.firstShipmentDetails.material_description }})</strong></td>
              <td></td> <!-- Outer Box Date -->
              <td></td> <!-- Batch -->
              <td class="spec-column total-value"><strong>{{ item.totalSpecification }}</strong></td>
              <td></td> <!-- Packaging Line -->
              <td :colspan="max_production_slots + 1"></td> <!-- Production Slots + Actions -->
            </tr>
          </template>
          <tr v-if="shipmentsWithGroupTotals.length > 0" class="grand-total-row">
            <td :colspan="8" class="total-label"><strong>合计总数</strong></td>
            <td class="spec-column total-value"><strong>{{ grandTotalSpecification }}</strong></td>
            <td :colspan="1 + max_production_slots"></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Floating Action Button (FAB) Container -->
    <div class="fab-container" @mouseenter="fabIsHovered = true" @mouseleave="fabIsHovered = false">
      <div class="fab-actions" :class="{ 'is-expanded': fabIsHovered }">
        <button @click="scrollToTop" class="fab-action-item fab-action-secondary">
          <span class="fab-icon">↑</span>
          <span class="fab-text">返回顶部</span>
        </button>
        <button @click="openAddShipmentModal" class="fab-action-item fab-action-primary">
          <span class="fab-icon">+</span>
          <span class="fab-text">添加记录</span>
        </button>
      </div>
      <button class="fab-main-trigger" aria-label="操作菜单">
        <span class="fab-icon">☰</span>
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import ExcelJS from 'exceljs';

const API_URL = '/api/v1';

export default {
  name: 'ShipmentTracking',
  data() {
    // Assuming data structure from a previous known good state.
    // The placeholders /* ... data ... */ were problematic.
    return {
      materials: [
        { number: '4070151N', description: '王老吉凉茶(16盒促销装)' },
        { number: '4070161N', description: '王老吉凉茶16盒（自动装)' },
        { number: '4070162N', description: '王老吉凉茶24盒（手提装）' },
        { number: '4070166N', description: '王老吉凉茶24盒手提装（促销装）' },
        { number: '4070272N', description: '王老吉凉茶(30盒电商专供装)' },
        { number: '4070274N', description: '王老吉凉茶24盒（电商特供）' },
        { number: '4070429N', description: '王老吉凉茶20盒礼品装(配礼品袋)' },
        { number: '4070277N', description: '王老吉凉茶12盒（电商特供）' },
        { number: '4070431N', description: '王老吉凉茶12盒手提礼品装（2021版）' },
        { number: '4070428N', description: '王老吉凉茶（六联包彩膜装）' },
        { number: '4070275N', description: '王老吉凉茶16盒自动(电商特供)' },
        { number: '4070276N', description: '王老吉凉茶（六联包特供电商）' },
        { number: '4070325N', description: '王老吉凉茶(21盒手提吉庆装)' },
        { number: '4070522N', description: '王老吉凉茶12盒手提礼品装（2025版）' },
        { number: '4070525N', description: '王老吉凉茶20盒手提礼品装(25版配礼品袋)' },
        { number: '4070562N', description: '王老吉凉茶250毫升*24盒手提（吉庆装）' },
      ],
      selectedMaterial: '',
      shipments: [],
      lastAddedShipmentId: null,  // 新录入记录高亮用的ID
      newShipment: {
        customer: null, 
        area_code: '', 
        customer_name: '', 
        shipping_address: '', 
        material_number: '', 
        material_description: '', 
        outer_box_date: '',
        shipment_date: '', 
        batch_number: '',
        specification: '',
        packaging_line: '',
        production_slots: [] 
      },
      max_production_slots: 10, 
      isLoading: false,
      fetchError: null,
      addError: null,
      isCustomerFetching: false,
      customerFetchError: null,
      selectedFile: null,
      selectedSheetName: '', 
      importStatusMessage: '',
      importErrors: [],
      isImporting: false,
      deleteError: null,
      clearAllError: null,
      filters: {
        shipment_date: '',
        outer_box_date: '',
        material_filter: '',
        packaging_line: '',
        batch_number: '',
        production_time: '',
        area_code: '',
        customer_name: '',
        shipping_address: '',
      },
      isAddShipmentModalVisible: false,
      isImportModalVisible: false,
      editingShipmentId: null,
      isSubmitting: false,
      fabIsHovered: false,
      exportStartDate: '',
      exportEndDate: '',
      pollingId: null,
      isImportDBModalVisible: false,
      selectedDBFile: null,
      isImportingDB: false,
      importDBStatusMessage: '',
      importDBError: null,
      selectedYear: new Date().getFullYear(),

      existingRecordIdForAppend: null,  // 409 时存储已有记录 ID，用于追加时间段
    };
  },
  computed: {
    availableYears() {
      const currentYear = new Date().getFullYear();
      const years = [];
      for (let i = currentYear; i >= 2020; i--) {
        years.push(i);
      }
      return years;
    },
    today() {
      return new Date().toISOString().split('T')[0];
    },
    isAnyFilterActive() {
      return Object.values(this.filters).some(value => value !== null && value !== '');
    },
    modalTitle() {
      return this.editingShipmentId ? '编辑流向记录' : '添加新流向记录';
    },
    modalSubmitButtonText() {
      return this.editingShipmentId ? '确认修改' : '确认添加';
    },
    // 批次格式验证：月.日（1-12月，1-31日）
    batchFormatError() {
      const val = this.newShipment.batch_number;
      if (!val) return false;
      const match = val.match(/^(\d+)\.(\d+)$/);
      if (!match) return true;
      const month = parseInt(match[1], 10);
      const day = parseInt(match[2], 10);
      return month < 1 || month > 12 || day < 1 || day > 31;
    },
    uniqueMaterials() {
      if (!this.shipments) return [];
      const materials = new Map();
      this.shipments.forEach(s => {
        if (s.material_number) {
          const value = `${s.material_number}|${s.material_description}`;
          if (!materials.has(value)) {
            const text = `${s.material_number} - ${s.material_description}`;
            materials.set(value, { value, text });
          }
        }
      });
      return Array.from(materials.values()).sort((a, b) => a.text.localeCompare(b.text));
    },

    // 从已加载数据中动态提取唯一客户名称列表（用于 datalist 下拉）
    uniqueCustomerNames() {
      if (!this.shipments) return [];
      const names = new Set();
      this.shipments.forEach(s => {
        const name = s.customer_details && s.customer_details.name;
        if (name) names.add(name);
      });
      return Array.from(names).sort((a, b) => a.localeCompare(b));
    },

    // 从已加载数据中动态提取唯一区域码列表（用于 datalist 下拉）
    uniqueAreaCodes() {
      if (!this.shipments) return [];
      const codes = new Set();
      this.shipments.forEach(s => {
        const code = s.customer_details && s.customer_details.area_code;
        if (code) codes.add(code);
      });
      return Array.from(codes).sort((a, b) => a.localeCompare(b));
    },

    // 从已加载数据中动态提取唯一送货地址列表（用于 datalist 下拉）
    uniqueShippingAddresses() {
      if (!this.shipments) return [];
      const addrs = new Set();
      this.shipments.forEach(s => {
        const addr = s.customer_details && s.customer_details.shipping_address;
        if (addr) addrs.add(addr);
      });
      return Array.from(addrs).sort((a, b) => a.localeCompare(b));
    },

    filteredShipments() {
      if (!this.shipments) return [];

      const { shipment_date, outer_box_date, material_filter, packaging_line } = this.filters;
      const batchFilter = this.filters.batch_number.toLowerCase().trim();
      const prodTimeFilter = this.filters.production_time.trim();
      const isTimeFilterActive = prodTimeFilter && /^\d+$/.test(prodTimeFilter);
      const filterTime = isTimeFilterActive ? parseInt(prodTimeFilter, 10) : NaN;
      const areaCodeFilter = this.filters.area_code.toLowerCase().trim();
      const customerNameFilter = this.filters.customer_name.toLowerCase().trim();
      const shippingAddressFilter = this.filters.shipping_address.toLowerCase().trim();

      return this.shipments.filter(shipment => {
        // 发货日期精确匹配
        if (shipment_date) {
          const sd = shipment.shipment_date || shipment.outer_box_date;
          if (sd !== shipment_date) return false;
        }

        if (batchFilter && !String(shipment.batch_number || '').toLowerCase().includes(batchFilter)) {
          return false;
        }
        if (packaging_line && shipment.packaging_line !== packaging_line) {
          return false;
        }
        if (outer_box_date && outer_box_date.trim()) {
          const filterDate = outer_box_date.trim().replace(/-/g, '');
          const shipmentDate = shipment.outer_box_date ? shipment.outer_box_date.replace(/-/g, '') : '';
          if (!shipmentDate.startsWith(filterDate)) {
            return false;
          }
        }

        if (material_filter) {
          const [number, description] = material_filter.split('|');
          if (shipment.material_number !== number || shipment.material_description !== description) {
            return false;
          }
        }

        // 区域码模糊匹配（关键字包含即通过）
        if (areaCodeFilter) {
          const code = (shipment.customer_details && shipment.customer_details.area_code) ? shipment.customer_details.area_code.toLowerCase() : '';
          if (!code.includes(areaCodeFilter)) return false;
        }

        // 客户名称模糊匹配（关键字包含即通过）
        if (customerNameFilter) {
          const name = (shipment.customer_details && shipment.customer_details.name) ? shipment.customer_details.name.toLowerCase() : '';
          if (!name.includes(customerNameFilter)) return false;
        }

        // 送货地址模糊匹配（关键字包含即通过）
        if (shippingAddressFilter) {
          const addr = (shipment.customer_details && shipment.customer_details.shipping_address) ? shipment.customer_details.shipping_address.toLowerCase() : '';
          if (!addr.includes(shippingAddressFilter)) return false;
        }

        if (isTimeFilterActive && !isNaN(filterTime)) {
          const hasMatchingSlot = shipment.production_time_slots && shipment.production_time_slots.some(slot => {
            if (!slot.start_time_str) return false;
            const startTime = parseInt(slot.start_time_str, 10);
            const endTime = (slot.end_time_str && slot.end_time_str.trim() !== '') ? parseInt(slot.end_time_str, 10) : startTime;
            if (isNaN(startTime) || isNaN(endTime)) return false;
            if (startTime <= endTime) {
              return filterTime >= startTime && filterTime <= endTime;
            } else {
              return filterTime >= startTime || filterTime <= endTime;
            }
          });
          if (!hasMatchingSlot) {
            return false;
          }
        }
        return true;
      });
    },

    shipmentsWithGroupTotals() {
      let processedShipments = [...this.filteredShipments];

      processedShipments.sort((a, b) => {
        const dateA = new Date(a.shipment_date || a.outer_box_date);
        const dateB = new Date(b.shipment_date || b.outer_box_date);
        if (dateA < dateB) return -1;
        if (dateA > dateB) return 1;
        const idA = a.original_id || a.id;
        const idB = b.original_id || b.id;
        if (idA < idB) return -1;
        if (idA > idB) return 1;
        return 0;
      });

      const MAX_SLOTS_PER_ROW = this.max_production_slots;

      const prodTimeFilter = this.filters.production_time.trim();
      const isTimeFilterActive = prodTimeFilter && /^\d+$/.test(prodTimeFilter);
      const filterTime = isTimeFilterActive ? parseInt(prodTimeFilter, 10) : NaN;

      // 无筛选时：含F记录不参与分组，各自独立成行；其余记录按6字段分组
      const grouped = {};
      const fOnlyRecords = [];
      processedShipments.forEach(originalShipment => {
        if (!originalShipment.customer_details) return;

        // 时间段筛选：只保留匹配时间段的数据行
        let slotsToDisplay = originalShipment.production_time_slots || [];
        if (isTimeFilterActive && !isNaN(filterTime)) {
          slotsToDisplay = slotsToDisplay.filter(slot => {
            if (!slot.start_time_str) return false;
            const startTime = parseInt(slot.start_time_str, 10);
            const endTime = (slot.end_time_str && slot.end_time_str.trim() !== '') ? parseInt(slot.end_time_str, 10) : startTime;
            if (isNaN(startTime) || isNaN(endTime)) return false;
            if (startTime <= endTime) {
              return filterTime >= startTime && filterTime <= endTime;
            } else {
              return filterTime >= startTime || filterTime <= endTime;
            }
          });
        }
        // 无匹配时间段 → 跳过该记录（和时间筛选逻辑一致）
        if (isTimeFilterActive && slotsToDisplay.length === 0) return;

        const hasF = (originalShipment.production_time_slots || []).some(
          slot => slot && typeof slot.start_time_str === 'string' && slot.start_time_str.trim().toUpperCase() === 'F'
        );
        if (hasF) {
          for (let i = 0; i < slotsToDisplay.length; i += MAX_SLOTS_PER_ROW) {
            const slotChunk = slotsToDisplay.slice(i, i + MAX_SLOTS_PER_ROW);
            const displayRow = { ...originalShipment, id: `${originalShipment.id}-row-${i / MAX_SLOTS_PER_ROW}`, original_id: originalShipment.id, production_time_slots: slotChunk, isGroupTotalRow: false, display_row_index: i / MAX_SLOTS_PER_ROW };
            fOnlyRecords.push(displayRow);
          }
          return;
        }

        const dateForKey = originalShipment.shipment_date || originalShipment.outer_box_date;
        const groupKey = [ dateForKey, originalShipment.customer_details.area_code, originalShipment.customer_details.name, originalShipment.customer_details.shipping_address, originalShipment.material_number, originalShipment.material_description ].join('|');
        if (!grouped[groupKey]) {
          grouped[groupKey] = { displayRows: [], totalSpecification: 0, firstShipmentDetails: { shipment_date: dateForKey, area_code: originalShipment.customer_details.area_code, customer_name: originalShipment.customer_details.name, shipping_address: originalShipment.customer_details.shipping_address, material_number: originalShipment.material_number, material_description: originalShipment.material_description, } };
        }
        const specValue = parseFloat(originalShipment.specification);
        let totalValidSlotsInOriginal = 0;
        if (originalShipment.production_time_slots && Array.isArray(originalShipment.production_time_slots)) {
          totalValidSlotsInOriginal = originalShipment.production_time_slots.filter(slot => slot && typeof slot.start_time_str === 'string' && slot.start_time_str.trim() !== '').length;
        }
        if (!isNaN(specValue) && totalValidSlotsInOriginal > 0) {
          grouped[groupKey].totalSpecification += (specValue * totalValidSlotsInOriginal);
        }
        const allSlots = slotsToDisplay;

        if (allSlots.length === 0) {
            const displayRow = { ...originalShipment, id: originalShipment.id + '-row-0', original_id: originalShipment.id, production_time_slots: [], isGroupTotalRow: false, display_row_index: 0, };
            grouped[groupKey].displayRows.push(displayRow);
        } else {
            for (let i = 0; i < allSlots.length; i += MAX_SLOTS_PER_ROW) {
                const slotChunk = allSlots.slice(i, i + MAX_SLOTS_PER_ROW);
                const displayRow = { ...originalShipment, id: `${originalShipment.id}-row-${i / MAX_SLOTS_PER_ROW}`, original_id: originalShipment.id, production_time_slots: slotChunk, isGroupTotalRow: false, display_row_index: i / MAX_SLOTS_PER_ROW, };
                grouped[groupKey].displayRows.push(displayRow);
            }
        }
      });
      const result = [];
      fOnlyRecords.forEach(row => result.push(row));
      for (const groupKey in grouped) {
        const group = grouped[groupKey];
        group.displayRows.forEach(displayRow => { result.push(displayRow); });
        if (group.displayRows.length > 0) {
          result.push({ isGroupTotalRow: true, id: `total-${groupKey.replace(/[^a-zA-Z0-9]/g, "")}`, firstShipmentDetails: group.firstShipmentDetails, totalSpecification: group.totalSpecification, customer_details: {}, production_time_slots: [] });
        }
      }
      return result;
    },
    grandTotalSpecification() {
      return this.shipmentsWithGroupTotals
        .filter(item => item.isGroupTotalRow)
        .reduce((sum, item) => sum + (item.totalSpecification || 0), 0);
    }
  },
  methods: {
    // 显示成功提示（不阻塞 UI）
    showSuccessToast(message) {
      // 移除已有 toast
      const existing = document.getElementById('shipment-toast');
      if (existing) existing.remove();
      const toast = document.createElement('div');
      toast.id = 'shipment-toast';
      toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #28a745;
        color: white;
        padding: 12px 20px;
        border-radius: 6px;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        font-size: 14px;
        max-width: 360px;
        animation: toastIn 0.3s ease;
      `;
      toast.textContent = message;
      document.body.appendChild(toast);
      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s';
        setTimeout(() => toast.remove(), 500);
      }, 4000);
    },
    async backupDatabase() {
      try {
        const response = await axios({
          url: `${API_URL}/database/backup/`,
          method: 'GET',
          responseType: 'blob', // Important
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        link.setAttribute('download', `backup-db-${timestamp}.sqlite3`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        alert('数据库备份成功！');
      } catch (error) {
        console.error('数据库备份失败:', error);
        alert('数据库备份失败。');
      }
    },
    openImportDBModal() {
      this.selectedDBFile = null;
      this.isImportingDB = false;
      this.importDBStatusMessage = '';
      this.importDBError = null;
      this.isImportDBModalVisible = true;
    },
    closeImportDBModal() {
      this.isImportDBModalVisible = false;
    },
    handleDBFileUpload(event) {
      this.selectedDBFile = event.target.files[0];
      this.importDBStatusMessage = '';
      this.importDBError = null;
      if (this.selectedDBFile) {
        this.importDBStatusMessage = `已选择文件: ${this.selectedDBFile.name}`;
      }
    },
    triggerDBImport() {
      if (window.confirm('您确定要用这个文件覆盖当前数据库吗？此操作无法撤销！')) {
        this.importDatabase();
      }
    },
    async importDatabase() {
      if (!this.selectedDBFile) return;
      this.isImportingDB = true;
      this.importDBStatusMessage = '正在上传并导入数据库...';
      this.importDBError = null;

      const formData = new FormData();
      formData.append('file', this.selectedDBFile);

      try {
        const response = await axios.post(`${API_URL}/database/import/`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        this.importDBStatusMessage = response.data.message || '数据库导入成功！请刷新页面或重启服务。';
        alert('数据库导入成功！建议刷新页面。');
        this.closeImportDBModal();
        this.fetchShipments(); // Refresh data
        this.$emit('shipment-data-updated');
      } catch (error) {
        console.error('数据库导入失败:', error.response || error);
        this.importDBError = (error.response && error.response.data && error.response.data.error) || '导入失败，请检查文件或联系管理员。';
        this.importDBStatusMessage = '';
      } finally {
        this.isImportingDB = false;
      }
    },
    clearFilters() {
      this.filters.shipment_date = '';
      this.filters.outer_box_date = '';
      this.filters.material_filter = '';
      this.filters.packaging_line = '';
      this.filters.batch_number = '';
      this.filters.production_time = '';
      this.filters.area_code = '';
      this.filters.customer_name = '';
      this.filters.shipping_address = '';
    },
    // Restoring methods based on typical implementations and previous context
    openAddShipmentModal() {
      this.editingShipmentId = null;
      // Do not reset the whole form. Instead, clear fields that should be new for each entry.
      this.newShipment.production_slots = [];
      this.addError = null;
      this.customerFetchError = null;
      this.isCustomerFetching = false;

      // Ensure there's at least one slot row when opening
      if (this.newShipment.production_slots.length === 0) {
        this.addProductionSlotRow();
      }

      this.isAddShipmentModalVisible = true;
      
      // Focus the first production slot field as it's the first to be entered now.
      this.$nextTick(() => {
        const firstSlotInput = this.$el.querySelector('#modal-slot-start-0');
        if (firstSlotInput) {
          firstSlotInput.focus();
        }
      });
    },
    closeAddShipmentModal() {
      this.isAddShipmentModalVisible = false;
      this.editingShipmentId = null;
      // We no longer reset the form on close, to preserve the data for the next opening.
    },
    openImportModal() {
      this.resetImportForm(); 
      this.isImportModalVisible = true;
    },
    closeImportModal() {
      this.isImportModalVisible = false;
      this.resetImportForm(); 
    },
    resetNewShipmentForm() { // This is for full reset when closing/opening modal
      this.newShipment.production_slots = [];
      this.selectedMaterial = '';
      this.newShipment.area_code = '';
      this.newShipment.customer_name = '';
      this.newShipment.shipping_address = '';
      this.newShipment.customer = null;
      this.newShipment.material_number= '';
      this.newShipment.material_description= '';
      this.newShipment.outer_box_date= '';
      this.newShipment.shipment_date= '';
      this.newShipment.batch_number= '';
      this.newShipment.specification= '';
      this.newShipment.packaging_line= '';
      this.addError = null;
      this.customerFetchError = null;
      // Only add a default slot row if not editing and no slots exist.
      // When opening for a new entry, this ensures one slot row.
      if (this.newShipment.production_slots.length === 0 && !this.editingShipmentId) {
        this.addProductionSlotRow();
      }
    },
    resetForNextSlotEntry() { // New method to reset only slots for continuous entry
      this.newShipment.production_slots = [];
      this.addError = null; // Clear previous submission errors for slots
      this.editingShipmentId = null; // CRITICAL: Ensure next submission is POST if not explicitly editing
      // Do NOT reset other fields like customer, material, batch, etc.
      this.addProductionSlotRow(); // Add a fresh empty slot row
      // Optionally, focus the first new slot input
      this.$nextTick(() => {
        const firstSlotInput = this.$el.querySelector('#modal-slot-start-0');
        if (firstSlotInput) {
          firstSlotInput.focus();
        }
      });
    },
    resetImportForm() {
        this.selectedFile = null;
        const fileInput = document.getElementById('modal-file-upload');
        if (fileInput) fileInput.value = null; 
        this.selectedSheetName = '';
        this.importStatusMessage = '';
        this.importErrors = [];
        this.isImporting = false;
    },
    async fetchShipments() {
      if (this.isLoading) {
        console.log("Polling skipped: a fetch is already in progress.");
        return;
      }
      this.isLoading = true;
      this.fetchError = null;
      this.deleteError = null;
      this.clearAllError = null;
      try {
        const response = await axios.get(`${API_URL}/shipments/`, {
          params: { year: this.selectedYear }
        });
        this.shipments = response.data.results !== undefined ? response.data.results : response.data;
      } catch (error) {
        console.error('获取流向列表失败:', error);
        this.fetchError = '无法加载流向列表。';
      } finally {
        this.isLoading = false;
      }
    },
    async fetchCustomerByAreaCode() {
      this.isCustomerFetching = true;
      this.customerFetchError = null;
      this.newShipment.customer_name = '';
      this.newShipment.shipping_address = '';
      this.newShipment.customer = null;
      if (!this.newShipment.area_code) return;
      try {
        const response = await axios.get(`${API_URL}/customers/by-area-code/${this.newShipment.area_code}/`);
        if (response.data && response.data.id) {
          this.newShipment.customer = response.data.id;
          this.newShipment.customer_name = response.data.name;
          this.newShipment.shipping_address = response.data.shipping_address;
        } else {
          // 客户不存在，允许用户手动输入客户名称和地址，后端会自动创建客户
          this.customerFetchError = '区域码未注册，系统将自动创建新客户。请填写客户名称和地址（可选）。';
        }
      } catch (error) {
        console.error('查询客户信息失败:', error);
        // 客户不存在，允许用户手动输入客户名称和地址，后端会自动创建客户
        this.customerFetchError = '区域码未注册，系统将自动创建新客户。请填写客户名称和地址（可选）。';
      } finally {
        this.isCustomerFetching = false;
      }
    },
    validateTimeSlots() {
      const timeRegex = /^\d{4}$/;
      for (const slot of this.newShipment.production_slots) {
        const start = (slot.start_time_str || '').trim();
        const end = (slot.end_time_str || '').trim();

        // Skip empty rows, they will be filtered out later
        if (start === '' && end === '') {
          continue;
        }

        // Handle 'F' case for "Full Pallet"
        if (start.toUpperCase() === 'F') {
          if (end !== '' && end.toUpperCase() !== 'F') {
            return `时间段 "${start}-${end}" 格式错误: 如果开始时间为 'F', 结束时间必须为空或也为 'F'。`;
          }
          // Standardize to have end as empty if start is F for cleaner data
          if (end.toUpperCase() === 'F') {
              slot.end_time_str = '';
          }
          continue;
        }

        // Validate start time format if it's not empty and not 'F'
        if (start && !timeRegex.test(start)) {
          return `开始时间 "${start}" 格式错误，请输入4位数字 (HHMM)。`;
        }
        
        // Validate end time format if it's not empty
        if (end && !timeRegex.test(end)) {
          return `结束时间 "${end}" 格式错误，请输入4位数字 (HHMM)。`;
        }
      }
      return null; // All valid
    },
    handleAddShipmentSubmit() {
        this.addShipment();
    },
    async addShipment() {
      console.log("--- Debug: addShipment ---");
      console.log("newShipment.production_slots at start of addShipment:", JSON.parse(JSON.stringify(this.newShipment.production_slots)));

      if (this.isSubmitting) return;
      this.isSubmitting = true;
      this.addError = null;

      // 防止竞态：如果区域码查询尚未完成，等待完成后再继续
      if (this.isCustomerFetching) {
        this.addError = '正在查询区域码，请稍候...';
        this.isSubmitting = false;
        return;
      }

      // Perform validation before any other checks
      const validationError = this.validateTimeSlots();
      if (validationError) {
        this.addError = validationError;
        this.isSubmitting = false;
        return;
      }

      if (!this.newShipment.customer && !this.newShipment.area_code) {
        this.addError = "请填写区域码，系统将自动创建新客户（如果不存在）。";
        this.isSubmitting = false;
        return;
      }
       if (!this.newShipment.material_number) {
        this.addError = "物料信息未选择，请选择物料。";
        this.isSubmitting = false;
        return;
      }
      if (this.newShipment.production_slots.length === 0 || this.newShipment.production_slots.every(slot => !slot.start_time_str && !slot.end_time_str)) {
          if (!this.newShipment.production_slots.some(slot => slot.start_time_str && slot.start_time_str.toUpperCase() === 'F')) {
            this.addError = "请至少提供一个有效的生产时间段，或输入 'F' 表示整板/不区分时间。";
            this.isSubmitting = false;
            return;
          }
      }


      const shipmentPayload = {
        customer_id: this.newShipment.customer || null,
        area_code: this.newShipment.area_code || '',
        customer_name: this.newShipment.customer_name || '',
        shipping_address: this.newShipment.shipping_address || '',
        material_number: this.newShipment.material_number,
        material_description: this.newShipment.material_description,
        outer_box_date: this.newShipment.outer_box_date,
        shipment_date: this.newShipment.shipment_date || null,
        batch_number: this.newShipment.batch_number,
        specification: this.newShipment.specification,
        packaging_line: this.newShipment.packaging_line,
        production_time_slots: this.newShipment.production_slots
            .map(slot => {
                const isStartF = slot.start_time_str && slot.start_time_str.toUpperCase() === 'F';
                // If start_time is 'F', end_time should also be 'F' or a non-null representation if backend expects it.
                // Given the error "This field may not be null" for end_time_str,
                // and UI shows user entered 'F' for end time too, we should send 'F'.
                // If start_time is not 'F', end_time uses its value or null if empty.
                return {
                    start_time_str: isStartF ? 'F' : (slot.start_time_str || null),
                    end_time_str: isStartF ? 'F' : (slot.end_time_str || null), 
                };
            })
            .filter(slot => slot.start_time_str) // Only include slots that have a start_time_str
      };
      
      console.log("shipmentPayload.customer_id:", shipmentPayload.customer_id);
      console.log("shipmentPayload.production_time_slots being sent:", JSON.parse(JSON.stringify(shipmentPayload.production_time_slots)));
      // console.log("Full shipmentPayload being sent:", JSON.parse(JSON.stringify(shipmentPayload))); // Temporarily comment out full payload log

      // Basic frontend duplicate check for "F" case to prevent obviously redundant "F" entries if needed
      // This is a simplified example; backend should be the ultimate source of truth for duplicate checks
      if (shipmentPayload.production_time_slots.some(s => s.start_time_str === 'F')) {
          if (shipmentPayload.production_time_slots.filter(s => s.start_time_str === 'F').length > 1) {
              // Optionally, consolidate multiple 'F' entries or warn the user
              // For now, we allow multiple 'F's if user entered them, backend should handle if it's an issue
          }
          if (shipmentPayload.production_time_slots.some(s => s.start_time_str !== 'F' && s.start_time_str !== null)) {
              // If 'F' is present, other specific time slots might be redundant or lead to confusion.
              // Depending on business logic, this could be a warning or an error.
              // For now, allow it and let backend decide.
          }
      }


      try {
        let apiResponse = null;
        if (this.editingShipmentId) {
          apiResponse = await axios.put(`${API_URL}/shipments/${this.editingShipmentId}/`, shipmentPayload);
        } else {
          apiResponse = await axios.post(`${API_URL}/shipments/`, shipmentPayload);
        }
        // 保存响应数据以获取新记录 ID
        let newShipmentId = null;
        if (apiResponse && apiResponse.data && apiResponse.data.id) {
            newShipmentId = apiResponse.data.id;
        }
        // Moved success feedback before fetching shipments to isolate issues
        // MODIFICATION: Do not close modal, reset for next slot entry
        let successMessage = '流向记录已成功添加/更新！';
        if (this.editingShipmentId) {
            successMessage = '流向记录已成功修改！';
            // If editing, we might want to close or offer to continue editing other aspects.
            // For now, to match the request, we'll assume "continue editing/adding slots for this same record".
            // If a full close is desired after *editing an existing main record*, this logic would differ.
            // The current request seems focused on "add new shipment, then add more slots to it, or add another similar new shipment".
        }

        if (this.editingShipmentId) { // If we were in EDIT mode (after a PUT)
            this.closeAddShipmentModal(); // Close modal after successful edit
        } else { // If it was a NEW shipment (after a POST)
            // For new shipments, reset only the slots for continuous entry, as requested.
            this.resetFormForNextEntry();
        }

        // 先刷新列表
        // 优化：不再请求全量数据，直接将新记录插入列表头部
        if (apiResponse && apiResponse.data) {
            const newRecord = apiResponse.data;
            if (this.editingShipmentId) {
                // 编辑模式：用新数据替换列表中对应记录
                const idx = this.shipments.findIndex(s => s.id === newRecord.id);
                if (idx !== -1) {
                    this.$set(this.shipments, idx, newRecord);
                }
                this.closeAddShipmentModal();
            } else {
                // 新增模式：直接 unshift 到列表头部
                this.shipments.unshift(newRecord);
                this.lastAddedShipmentId = newShipmentId;
                // 高亮 + 滚动定位
                this.$nextTick(() => {
                    const row = this.$el.querySelector(`[data-shipment-id="${newShipmentId}"]`);
                    if (row) {
                        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                    setTimeout(() => { this.lastAddedShipmentId = null; }, 3000);
                });
            }
        }

        // 显示非阻塞提示
        if (newShipmentId) {
            this.showSuccessToast(`流向记录已添加（ID: ${newShipmentId}）。`);
        } else {
            this.showSuccessToast(successMessage);
        }

        this.$emit('shipment-data-updated');
        // Note: editingShipmentId is NOT reset here, so subsequent "Confirm Add" clicks for the same
        // form state (if user only changes slots) would still target the same existing record if one was matched.
        // If a *brand new* distinct record should be created next, user needs to change key fields or close/reopen.

      } catch(error) {
        console.error('添加/更新流向记录失败:', error.response || error);
        this.addError = null;

        // 处理 409 重复记录冲突 — existing_record 后端已序列化为 JSON 字符串
        if (error.response && error.response.status === 409 && error.response.data && error.response.data.duplicate) {
          const recStr = error.response.data.existing_record;
          this.addError = `⚠️ ${error.response.data.error}\n${typeof recStr === 'string' ? recStr : JSON.stringify(recStr, null, 2)}`;
          // 从 existing_record JSON 字符串中解析出 ID
          try {
            const recObj = typeof recStr === 'string' ? JSON.parse(recStr) : recStr;
            this.existingRecordIdForAppend = recObj.id || null;
          } catch(e) {
            this.existingRecordIdForAppend = null;
          }
        } else if (error.response && error.response.data) {
            if (typeof error.response.data === 'string') {
                 this.addError = error.response.data;
            } else if (error.response.data.detail) {
                this.addError = error.response.data.detail;
            } else if (typeof error.response.data === 'object') {
                let messages = [];
                for (const key in error.response.data) {
                    if (Array.isArray(error.response.data[key])) {
                         messages.push(`${key}: ${error.response.data[key].join(', ')}`);
                    } else {
                         messages.push(`${key}: ${error.response.data[key]}`);
                    }
                }
                this.addError = messages.join('; ') || "发生未知错误。";
            } else {
                 this.addError = "添加/更新流向记录失败，请检查输入或联系管理员。";
            }
        } else {
            this.addError = "添加/更新流向记录失败，网络错误或服务器无响应。";
        }
      } finally {
        this.isSubmitting = false;
      }
    },
    updateMaterialDetails() {
      if (this.selectedMaterial && this.selectedMaterial.number) {
        this.newShipment.material_number = this.selectedMaterial.number;
        this.newShipment.material_description = this.selectedMaterial.description;
      } else {
        this.newShipment.material_number = '';
        this.newShipment.material_description = '';
      }
    },
    addProductionSlotRow() {
      if (this.newShipment.production_slots.length < this.max_production_slots) {
        this.newShipment.production_slots.push({ start_time_str: '', end_time_str: '' }); 
      }
    },
    removeProductionSlotRow(index) {
      this.newShipment.production_slots.splice(index, 1);
    },
    handleFileUpload(event) {
      this.selectedFile = event.target.files[0];
      this.importStatusMessage = '';
      this.importErrors = [];
      if (this.selectedFile) {
        this.importStatusMessage = `已选择文件: ${this.selectedFile.name}`;
      }
    },
    triggerImport() { 
        this.importShipments();
    },
    async importShipments() {
      if (!this.selectedFile) { /* ... */ return; }
      this.isImporting = true;
      // ... (Full importShipments logic)
      try {
        // ... axios call ...
        this.fetchShipments();
        this.$emit('shipment-data-updated');
      } catch (error) { /* ... */ }
      finally {
        this.isImporting = false;
      }
    },
    async confirmDeleteShipment(shipmentId) {
      this.deleteError = null;
      if (window.confirm('您确定要删除这条流向记录吗？此操作无法撤销。')) {
        this.isLoading = true;
        try {
          await axios.delete(`${API_URL}/shipments/${shipmentId}/`);
          alert('流向记录已成功删除。');
          this.fetchShipments();
          this.$emit('shipment-data-updated');
        } catch (error) { /* ... */ }
        finally {
          this.isLoading = false; 
        }
      }
    },
    async confirmClearAllShipments() {
       this.clearAllError = null;
      if (window.confirm('警告：您确定要清空所有流向数据吗？此操作无法撤销，将永久删除所有记录！')) {
        // ... (Full confirmClearAllShipments logic)
        try { 
          this.fetchShipments();
        } catch(e) { 
          // console.error("Error during fetch after clear:", e); 
        }
        finally { 
          // No specific finally action needed here after removing scrollbar logic
        }
      }
    },
    startEditShipment(shipmentToEdit) {
      const originalShipmentId = shipmentToEdit.original_id || shipmentToEdit.id;
      const originalShipment = this.shipments.find(s => s.id === originalShipmentId);

      if (!originalShipment) {
        console.error("Could not find the original shipment to edit with ID:", originalShipmentId);
        this.addError = "无法找到要编辑的原始记录。请刷新页面后重试。";
        this.isAddShipmentModalVisible = true; // Open modal to show the error
        return;
      }

      this.editingShipmentId = originalShipment.id;
      
      // Populate general fields from the full original shipment object
      this.newShipment.shipment_date = originalShipment.shipment_date || originalShipment.outer_box_date;
      this.newShipment.area_code = originalShipment.customer_details.area_code;
      this.newShipment.customer_name = originalShipment.customer_details.name;
      this.newShipment.shipping_address = originalShipment.customer_details.shipping_address;
      this.newShipment.customer = originalShipment.customer_details.id;

      this.newShipment.material_number = originalShipment.material_number;
      this.newShipment.material_description = originalShipment.material_description;
      const materialToSelect = this.materials.find(m => m.number === originalShipment.material_number);
      this.selectedMaterial = materialToSelect || '';

      this.newShipment.outer_box_date = originalShipment.outer_box_date;
      this.newShipment.batch_number = originalShipment.batch_number;
      this.newShipment.specification = originalShipment.specification;
      this.newShipment.packaging_line = originalShipment.packaging_line;

      // Populate ALL production_slots from the original shipment object
      let slotsToCopy = [];
      if (originalShipment.production_time_slots && Array.isArray(originalShipment.production_time_slots)) {
          slotsToCopy = originalShipment.production_time_slots;
      }
      
      this.newShipment.production_slots = slotsToCopy.map(s => ({
        start_time_str: s.start_time_str || '',
        end_time_str: s.end_time_str || ''
      }));

      if (this.newShipment.production_slots.length === 0) {
        this.addProductionSlotRow();
      }
      
      this.addError = null;
      this.customerFetchError = null;
      this.isAddShipmentModalVisible = true;
    },
    resetFormForNextEntry() {
      // This method is called after a successful submission for a NEW entry.
      // We clear only the fields that should be unique for the next entry.
      this.newShipment.production_slots = [];
      this.addError = null;
      this.isCustomerFetching = false;
      this.existingRecordIdForAppend = null;

      if (this.newShipment.production_slots.length === 0) {
        this.addProductionSlotRow();
      }
      
      this.editingShipmentId = null; 
      
      // Focus on the first production slot input for the next entry.
      this.$nextTick(() => {
        const firstSlotInput = this.$el.querySelector('#modal-slot-start-0');
        if (firstSlotInput) {
          firstSlotInput.focus();
        }
      });
    },
    async appendTimeSlots() {
      // 追加时间段到已有记录（409 后触发）
      if (!this.existingRecordIdForAppend) {
        this.addError = '错误：未找到目标记录ID';
        return;
      }

      // 验证时间段
      const validationError = this.validateTimeSlots();
      if (validationError) {
        this.addError = validationError;
        return;
      }

      if (this.newShipment.production_slots.length === 0) {
        this.addError = '请至少填写一个要追加的时间段';
        return;
      }

      this.isSubmitting = true;
      this.addError = null;

      const slots = this.newShipment.production_slots
        .filter(slot => slot.start_time_str)
        .map(slot => ({
          start_time_str: slot.start_time_str.toUpperCase() === 'F' ? 'F' : (slot.start_time_str || null),
          end_time_str: slot.start_time_str.toUpperCase() === 'F' ? 'F' : (slot.end_time_str || null),
        }));

      try {
        const resp = await axios.post(
          `${API_URL}/shipments/${this.existingRecordIdForAppend}/append-slots/`,
          { production_time_slots: slots }
        );

        const msg = resp.data.message || '时间段已追加';
        // 追加成功后：清空时间段（保留其他字段）、刷新列表、高亮
        this.resetFormForNextEntry();
        await this.fetchShipments();

        // 高亮 + 滚动定位
        this.$nextTick(() => {
            const row = this.$el.querySelector(`[data-shipment-id="${this.existingRecordIdForAppend}"]`);
            if (row) {
                row.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            this.lastAddedShipmentId = this.existingRecordIdForAppend;
            setTimeout(() => { this.lastAddedShipmentId = null; }, 3000);
        });

        this.showSuccessToast(`${msg}。`);
        this.closeAddShipmentModal();

      } catch (error) {
        console.error('追加时间段失败:', error.response || error);
        if (error.response && error.response.data) {
          if (typeof error.response.data === 'object' && error.response.data.error) {
            this.addError = `追加失败：${error.response.data.error}`;
          } else if (typeof error.response.data === 'string') {
            this.addError = `追加失败：${error.response.data}`;
          }
        } else {
          this.addError = '追加时间段失败，网络错误或服务器无响应。';
        }
      } finally {
        this.isSubmitting = false;
      }
    },
    async exportToXLSX() {
      let dataToExport = this.shipmentsWithGroupTotals.filter(item => !item.isGroupTotalRow);

      // Date Range Filtering
      if (this.exportStartDate && this.exportEndDate) {
        const startDate = new Date(this.exportStartDate);
        startDate.setHours(0, 0, 0, 0); // Set to start of day
        const endDate = new Date(this.exportEndDate);
        endDate.setHours(23, 59, 59, 999); // Set to end of day

        if (startDate > endDate) {
          alert('开始日期不能晚于结束日期。');
          return;
        }

        dataToExport = dataToExport.filter(item => {
          const itemDateStr = item.shipment_date || item.outer_box_date;
          if (!itemDateStr) return false;
          const itemDate = new Date(itemDateStr);
          return itemDate >= startDate && itemDate <= endDate;
        });
      }

      if (dataToExport.length === 0) {
        alert('没有符合筛选条件的数据可导出。');
        return;
      }
      
      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet('流向记录');

      const columns = [
        { header: '发货日期', key: 'shipment_date', width: 15 },
        { header: '客户名称', key: 'customer_name', width: 30 },
        { header: '送货地址', key: 'shipping_address', width: 40 },
        { header: '物料编号', key: 'material_number', width: 15 },
        { header: '物料描述', key: 'material_description', width: 30 },
        { header: '外箱日期', key: 'outer_box_date_display', width: 15 },
        { header: '规格', key: 'specification', width: 10 },
        { header: '包装线', key: 'packaging_line', width: 10 },
      ];

      for (let i = 1; i <= this.max_production_slots; i++) {
        columns.push({ header: `起止时间 ${i}`, key: `slot_${i}`, width: 20 });
      }
      worksheet.columns = columns;

      dataToExport.forEach(item => {
        const row = {
          shipment_date: item.shipment_date || item.outer_box_date,
          customer_name: item.customer_details.name,
          shipping_address: item.customer_details.shipping_address,
          material_number: item.material_number,
          material_description: item.material_description,
          outer_box_date_display: this.formatOuterBoxDateForDisplay(item.outer_box_date),
          specification: item.specification,
          packaging_line: item.packaging_line,
        };
        for (let i = 0; i < this.max_production_slots; i++) {
          const slot = item.production_time_slots && item.production_time_slots[i];
          if (slot) {
            if (slot.start_time_str && slot.start_time_str.toUpperCase() === 'F') {
              row[`slot_${i + 1}`] = 'F';
            } else if (slot.start_time_str) {
              row[`slot_${i + 1}`] = `${slot.start_time_str}${slot.end_time_str ? '-' + slot.end_time_str : ''}`;
            } else {
              row[`slot_${i + 1}`] = '';
            }
          } else {
            row[`slot_${i + 1}`] = '';
          }
        }
        worksheet.addRow(row);
      });

      worksheet.getRow(1).font = { bold: true };
      worksheet.getRow(1).alignment = { vertical: 'middle', horizontal: 'center' };
      worksheet.getRow(1).fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFD3D3D3' }
      };
      worksheet.getRow(1).border = {
        top: { style: 'thin' }, left: { style: 'thin' }, bottom: { style: 'thin' }, right: { style: 'thin' }
      };

      const defaultRowHeight = 15;
      const increasedRowHeight = defaultRowHeight * 1.5;

      worksheet.eachRow({ includeEmpty: true }, function(row, rowNumber) {
        row.height = increasedRowHeight;
        if (rowNumber === 1) {
          row.font = { bold: true };
          row.alignment = { vertical: 'middle', horizontal: 'center' };
          row.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFD3D3D3' } };
        }
        row.eachCell({ includeEmpty: true }, function(cell) {
          cell.border = { top: { style: 'thin' }, left: { style: 'thin' }, bottom: { style: 'thin' }, right: { style: 'thin' } };
          cell.alignment = { ...cell.alignment, vertical: 'middle' };
        });
      });

      try {
        const buffer = await workbook.xlsx.writeBuffer();
        const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        
        let fileName = `流向记录_${new Date().toISOString().slice(0, 10)}.xlsx`;
        if (this.exportStartDate && this.exportEndDate) {
            fileName = `流向记录_${this.exportStartDate}_至_${this.exportEndDate}.xlsx`;
        }
        link.download = fileName;

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
      } catch (err) {
        console.error("Error exporting to XLSX:", err);
        alert("导出XLSX文件失败。请查看控制台获取更多信息。");
      }
    },
    handleFormNavigation(event, section, index = -1, fieldName = '') {
      const focusableElements = Array.from(
        this.$el.querySelectorAll(
          '.modal-body input:not([readonly]):not([type="hidden"]), .modal-body select, .modal-body textarea:not([readonly]), .modal-footer button:not([disabled])'
        )
      ).filter(el => el.offsetParent !== null && !el.disabled); // Ensure elements are visible and enabled

      const currentIndex = focusableElements.indexOf(event.target);

      let targetIndex = -1;

      switch (event.key) {
        case 'ArrowDown':
        case 'ArrowRight':
          event.preventDefault();
          targetIndex = (currentIndex + 1) % focusableElements.length;
          break;
        case 'ArrowUp':
        case 'ArrowLeft':
          event.preventDefault();
          targetIndex = (currentIndex - 1 + focusableElements.length) % focusableElements.length;
          break;
        case 'Enter':
          // If Enter is pressed on a form field (not a button), and it's not a textarea,
          // try to submit the form. Otherwise, allow default behavior (e.g., new line in textarea).
          if (event.target.tagName !== 'BUTTON' && event.target.tagName !== 'TEXTAREA') {
            const isProductionSlotField = section === 'production_slots';
            const isLastSlotField = isProductionSlotField && 
                                    index === this.newShipment.production_slots.length - 1 &&
                                    fieldName === 'end_time_str';
            
            if (isProductionSlotField && !isLastSlotField) {
              // If in a slot field and not the very last one, move to next field or slot
              event.preventDefault();
              targetIndex = (currentIndex + 1) % focusableElements.length;
            } else if (isProductionSlotField && isLastSlotField) {
              // If on the last slot field (end_time_str of the last slot),
              // Enter should ideally focus the main submit button or just submit.
              // For now, let's try to focus the submit button directly.
              const submitButton = focusableElements.find(el => el.classList.contains('btn-primary') && el.textContent.includes(this.modalSubmitButtonText));
              if (submitButton) {
                event.preventDefault();
                submitButton.focus();
                // To actually trigger submit, we'd call this.handleAddShipmentSubmit() here,
                // but that might be too aggressive. Focusing is safer first.
              }
            } else if (!isProductionSlotField) {
              // If not in production slots (e.g., main form fields),
              // pressing Enter could also attempt to move to the next field or submit.
              // For now, just move to the next field.
              event.preventDefault();
              targetIndex = (currentIndex + 1) % focusableElements.length;
            }
            // If it's a button, Enter will trigger its default click action.
          }
          break;
      }

      if (targetIndex !== -1 && focusableElements[targetIndex]) {
        focusableElements[targetIndex].focus();
        if (focusableElements[targetIndex].select) {
          focusableElements[targetIndex].select(); // Select text in input/textarea
        }
      }
    },
    formatOuterBoxDateForDisplay(dateString) {
      if (!dateString) return '';
      const parts = dateString.split('-');
      if (parts.length !== 3) return dateString; 
      return `YY${parts[0]}${parts[1]}${parts[2]}`;
    },
    scrollToTop() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    formatSlot(slot) {
      if (!slot) return '';
      if (typeof slot.start_time_str !== 'string' || slot.start_time_str.trim() === '') {
        return '';
      }
      // F 类型流水号单独显示
      if (slot.start_time_str.toUpperCase() === 'F') {
        return 'F';
      }
      // 如果 end_time_str 也是 F，单独显示
      if (slot.end_time_str && slot.end_time_str.toUpperCase() === 'F') {
        return slot.start_time_str + '-F';
      }
      return slot.start_time_str + (slot.end_time_str ? '-' + slot.end_time_str : '');
    }
  },
  watch: {
    // No watch needed specifically for fixed scrollbar now
  },
  mounted() {
    this.fetchShipments();
    if (this.newShipment.production_slots.length === 0) {
        this.addProductionSlotRow();
    }
    // Set up polling to refresh data every 15 seconds
    this.pollingId = setInterval(this.fetchShipments, 15000);
  },
  beforeUnmount() {
    // Clear the polling interval when the component is destroyed
    if (this.pollingId) {
      clearInterval(this.pollingId);
    }
  }
};
</script>

<style scoped>
@keyframes toastIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* General Styles */
.shipment-tracking {
  box-sizing: border-box; 
  font-family: sans-serif;
  max-width: 95%;
  min-width: 1000px;
  margin: 20px auto;
  padding: 20px 20px 40px; 
  border: 1px solid #eee; /* Restore a light, standard border */
  border-radius: 8px; 
  box-shadow: none !important; /* Keep shadow explicitly removed */
  /* overflow-x: hidden; Removed to allow inner scroll */
}
h2, h3, h4 { color: #333; text-align: center; }
h3 { margin-top: 0;}
h4 { margin-bottom: 15px; }

.page-actions-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee; flex-wrap: wrap; gap: 15px;}
.year-selector { display: flex; align-items: center; gap: 10px; }
.year-selector label { font-size: 0.9em; font-weight: bold; }
.year-select-input { padding: 8px; border: 1px solid #ddd; border-radius: 4px; height: 38px; box-sizing: border-box; min-width: 100px; }
.export-controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.export-controls label { font-size: 0.9em; margin-left: 5px; }
.export-controls .date-filter-input { padding: 8px; border: 1px solid #ddd; border-radius: 4px; height: 38px; box-sizing: border-box; }
.btn-action { padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-right: 10px; }
.btn-primary { background-color: #007bff; color: white; } .btn-primary:hover { background-color: #0056b3; }
.btn-secondary { background-color: #6c757d; color: white; } .btn-secondary:hover { background-color: #545b62; }
.btn-success { background-color: #28a745; color: white; } .btn-success:hover { background-color: #218838; }
.btn-danger { background-color: #dc3545; color: white; } .btn-danger:hover { background-color: #c82333; }
.btn-warning { background-color: #ffc107; color: #212529; } .btn-warning:hover { background-color: #e0a800; }
.btn-info { background-color: #17a2b8; color: white; } .btn-info:hover { background-color: #138496; }
.btn-cancel { background-color: #f8f9fa; color: #333; border: 1px solid #ccc; } .btn-cancel:hover { background-color: #e2e6ea; }

.shipment-form-in-modal, .production-slots-form-in-modal, .xlsx-import-form-in-modal { padding: 0; background-color: transparent; border-radius: 0; margin-bottom: 0; box-shadow: none; border: none; }
.section-block-modal { margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 15px; align-items: start; }
.form-grid-slots { display: grid; grid-template-columns: 1fr 1fr auto; gap: 10px; padding-bottom: 10px; border-bottom: 1px solid #eee; margin-bottom: 10px; align-items: end; }
.form-grid-slots:last-child { border-bottom: none; margin-bottom: 0; }
.modal-body .form-grid div label, .modal-body .production-slot-row div label, .modal-body .xlsx-import-form-in-modal label { display: block; margin-bottom: 5px; font-weight: bold; font-size: 0.9em; }
.modal-body .form-grid div input[type="text"], .modal-body .form-grid div input[type="date"], .modal-body .form-grid div input[type="number"], .modal-body .form-grid div textarea, .modal-body .form-grid div select, .modal-body .form-grid-slots input[type="text"], .modal-body .xlsx-import-form-in-modal input[type="text"], .modal-body .xlsx-import-form-in-modal input[type="file"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; height: 38px; }
.modal-body .form-grid div textarea { height: 60px; resize: vertical; }
.modal-body .xlsx-import-form-in-modal input[type="file"] { padding: 5px; }
.modal-error { margin-top: 5px; margin-bottom: 10px; text-align: left; font-size: 0.9em; white-space: pre-wrap; font-family: inherit; }
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.6); display: flex; justify-content: center; align-items: center; z-index: 1000; padding: 20px; box-sizing: border-box; }
.modal { background-color: white; border-radius: 8px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; }
.modal-lg { width: 80%; max-width: 900px; } .modal-md { width: 60%; max-width: 600px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding: 15px 20px; }
.modal-header h3 { margin: 0; font-size: 1.3em; }
.modal-close-button { background: none; border: none; font-size: 1.8em; cursor: pointer; padding: 0; line-height: 1; color: #888; } .modal-close-button:hover { color: #333; }
.modal-body { padding: 20px; overflow-y: auto; flex-grow: 1; }
.modal-footer { border-top: 1px solid #eee; padding: 15px 20px; text-align: right; background-color: #f9f9f9; }
.modal-footer button { margin-left: 10px; }
.filter-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 10px; align-items: end; }
.filter-grid input[type="text"],
.filter-grid input[type="date"],
.filter-grid select {
  height: 38px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}
.filter-grid button {
  height: 38px;
  box-sizing: border-box;
}
/* combobox（datalist输入框）样式与其他筛选框保持一致 */
.combobox-wrapper {
  display: flex;
  flex-direction: column;
}
.combobox-wrapper input[type="text"] {
  width: 100%;
  height: 38px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}
.filters-container.section-block { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; margin-bottom: 20px; padding: 20px; background-color: #f9f9f9; border-radius: 6px; }
.table-container { 
  /* overflow-x: auto; */ /* Removed to allow page scroll for wide tables */
  border-top: 1px solid #ccc; 
  border-left: 1px solid #ccc; 
  border-right: 1px solid #ccc; 
  border-bottom: none !important; /* Remove bottom border for table container */
  margin-top: 0px; 
  position: relative; 
  margin-bottom: 20px; 
  outline: none !important; 
  box-shadow: none !important;
}
table { 
  border-collapse: collapse; 
  width: 100%; 
  border-bottom: none !important; /* Ensure table itself also has no bottom border */
  outline: none !important;
}
th, td { 
  box-sizing: border-box; 
  border: 1px solid #ddd; 
  padding: 8px; 
  text-align: left; 
  font-size: 0.85em; 
  vertical-align: middle; 
  box-shadow: none !important; /* Explicitly remove any shadow from cells */
  outline: none !important; /* Explicitly remove any outline from cells */
}
/* Ensure no other element is creating that bottom bar, check for pseudo-elements or empty divs if this doesn't fix it */
th { position: sticky; top: 0; z-index: 10; background-color: #f2f2f2; font-weight: bold; white-space: nowrap;}
.actions-column { min-width: 120px; text-align: center;}
.area-code-column { min-width: 80px; }
.customer-name-column { min-width: 200px; } 
.shipping-address-column { min-width: 250px; } 
.material-number-column { min-width: 100px; }
.material-description-column { min-width: 180px; white-space: nowrap; }
.date-column { min-width: 100px; } 
.batch-column { min-width: 80px; }
.spec-column { min-width: 70px; }
.line-column { min-width: 70px; }
.dynamic-slot-time-column { min-width: 130px; }
/* F 流水号样式 - 特殊标识 */
.dynamic-slot-time-column:has(span.slot-f) {
  color: #ff6600;
  font-weight: bold;
}
.slot-f {
  color: #ff6600;
  font-weight: bold;
}
tbody tr:nth-child(even) { background-color: #f9f9f9; }
.loading-message { text-align: center; padding: 20px; color: #555; }
.error-message { color: red; margin-top: 10px; text-align: center; margin-bottom: 10px;}
/* 批次格式验证样式 */
.field-hint { display: block; font-size: 0.8em; color: #666; margin-top: 2px; }
.field-error { display: block; font-size: 0.8em; color: #dc3545; margin-top: 2px; }
input.input-error { border-color: #dc3545 !important; }
.btn-edit, .btn-delete { padding: 5px 10px; margin: 0 3px; border-radius: 4px; cursor: pointer; font-size: 0.8em; border: 1px solid transparent; }
.btn-edit { background-color: #ffc107; color: #333; border-color: #ffc107; } .btn-edit:hover { background-color: #e0a800; } .btn-edit:disabled { background-color: #ccc; border-color: #bbb; color: #666; cursor: not-allowed; }
.btn-delete { background-color: #dc3545; color: white; border-color: #dc3545; } .btn-delete:hover { background-color: #c82333; }
.xlsx-import-form-in-modal .import-status-message { margin-top: 15px; padding: 10px; border-radius: 4px; text-align: center; }
.xlsx-import-form-in-modal .import-status-message.success-message { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.xlsx-import-form-in-modal .import-status-message.error-message, .xlsx-import-form-in-modal .import-errors.error-message { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
.xlsx-import-form-in-modal .import-status-message.info-message { background-color: #cce5ff; color: #004085; border: 1px solid #b8daff; }
.xlsx-import-form-in-modal .import-errors { list-style-type: none; padding-left: 0; margin-top: 10px; }
.xlsx-import-form-in-modal .import-errors li { padding: 5px; border-bottom: 1px solid #f5c6cb; font-size: 0.9em; } .xlsx-import-form-in-modal .import-errors li:last-child { border-bottom: none; }
.db-import-form-in-modal .warning-message { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; padding: 10px; border-radius: 4px; margin-bottom: 15px; }
.db-import-form-in-modal .import-status-message, .db-import-form-in-modal .import-errors { margin-top: 15px; padding: 10px; border-radius: 4px; text-align: center; }
.db-import-form-in-modal .import-status-message.success-message { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.db-import-form-in-modal .import-errors.error-message { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
.db-import-form-in-modal .import-status-message.info-message { background-color: #cce5ff; color: #004085; border: 1px solid #b8daff; }
.btn-add-slot { background-color: #007bff; color: white; padding: 8px 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; margin-bottom: 15px; } .btn-add-slot:hover { background-color: #0056b3; } .btn-add-slot:disabled { background-color: #ccc; cursor: not-allowed; }
.btn-remove-slot { background-color: #dc3545; color: white; padding: 8px 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; height: 38px; align-self: center; } .btn-remove-slot:hover { background-color: #c82333; }
/* Removed .fixed-scrollbar-container and .fixed-scrollbar-content styles */
.fab-container { position: fixed; bottom: 25px; left: 30px; right: auto; z-index: 990; display: flex; flex-direction: column-reverse; align-items: flex-start; }
.fab-main-trigger { background-color: #007bff; color: white; border: none; width: 56px; height: 56px; border-radius: 50%; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); display: flex; justify-content: center; align-items: center; cursor: pointer; transition: background-color 0.3s ease; font-size: 24px; }
.fab-main-trigger:hover { background-color: #0056b3; }
.fab-actions { display: flex; flex-direction: column-reverse; align-items: flex-start; margin-bottom: 10px; }
.fab-action-item { display: flex; align-items: center; background-color: #f8f9fa; color: #333; border: 1px solid #ddd; padding: 8px 12px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15); margin-bottom: 8px; cursor: pointer; white-space: nowrap; opacity: 0; transform: translateY(10px) scale(0.9); transition: opacity 0.2s ease-out, transform 0.2s ease-out, visibility 0s 0.2s; visibility: hidden; }
.fab-action-item:last-child { margin-bottom: 0; }
.fab-container:hover .fab-actions .fab-action-item, .fab-actions.is-expanded .fab-action-item { opacity: 1; transform: translateY(0) scale(1); visibility: visible; transition: opacity 0.2s ease-in, transform 0.2s ease-in, visibility 0s 0s; }
.fab-container:hover .fab-actions .fab-action-item:nth-child(1), .fab-actions.is-expanded .fab-action-item:nth-child(1) { transition-delay: 0.05s; }
.fab-container:hover .fab-actions .fab-action-item:nth-child(2), .fab-actions.is-expanded .fab-action-item:nth-child(2) { transition-delay: 0.1s; }
.fab-action-item:hover { background-color: #e2e6ea; border-color: #ccc; }
.fab-action-item .fab-icon { margin-right: 8px; font-size: 18px; }
.fab-action-item .fab-text { font-size: 14px; }
.fab-action-primary { background-color: #007bff; color: white; border-color: #007bff; } .fab-action-primary:hover { background-color: #0056b3; border-color: #0056b3; }
.fab-action-secondary { background-color: #6c757d; color: white; border-color: #6c757d; } .fab-action-secondary:hover { background-color: #545b62; border-color: #545b62; }
/* 合计总数行样式 */
.grand-total-row {
  background-color: #e6f7ff;
  font-weight: bold;
}
.grand-total-row td {
  border-top: 2px solid #007bff;
}

/* 高亮新录入记录 */
@keyframes highlightPulse {
  0%, 100% { background-color: rgba(76, 175, 80, 0.3); }
  50% { background-color: rgba(76, 175, 80, 0.6); }
}
.highlight-new {
  animation: highlightPulse 0.5s ease-in-out 3;
}
</style>
