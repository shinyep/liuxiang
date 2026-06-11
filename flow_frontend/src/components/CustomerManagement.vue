<template>
  <div class="customer-management">
    <h2>客户信息管理</h2>

    <!-- 添加/编辑客户表单 -->
    <form @submit.prevent="handleSubmitCustomer" class="customer-form">
      <h3>{{ formTitle }}</h3>
      <div>
        <label for="area-code">区域码:</label>
        <input type="text" id="area-code" v-model="currentCustomer.area_code" required :disabled="isEditing" />
      </div>
      <div>
        <label for="name">客户名称:</label>
        <input type="text" id="name" v-model="currentCustomer.name" required />
      </div>
      <div>
        <label for="shipping-address">送货地址:</label>
        <textarea id="shipping-address" v-model="currentCustomer.shipping_address" required></textarea>
      </div>
      <button type="submit">{{ submitButtonText }}</button>
      <button type="button" v-if="isEditing" @click="cancelEdit" style="margin-left: 10px;">取消编辑</button>
      <p v-if="formError" class="error-message">{{ formError }}</p>
    </form>

    <!-- 客户列表 -->
    <h3>客户列表</h3>
    <div class="search-bar">
      <input type="text" v-model="searchQuery" placeholder="按客户名称或区域码搜索..." @input="handleSearchInput" />
    </div>
    <div v-if="isLoading" class="loading-message">正在加载客户数据...</div>
    <div v-if="fetchError" class="error-message">{{ fetchError }}</div>
    <ul v-if="customers.length > 0" class="customer-list">
      <li v-for="customer in customers" :key="customer.id" class="customer-list-item">
        <div>
          <strong>{{ customer.name }}</strong> (区域码: {{ customer.area_code }})
          <p>地址: {{ customer.shipping_address }}</p>
        </div>
        <div class="customer-actions">
          <button @click="startEditCustomer(customer)" class="edit-button" style="margin-right: 8px;">编辑</button>
          <button @click="deleteCustomer(customer.id)" class="delete-button">删除</button>
        </div>
      </li>
    </ul>
    <p v-else-if="!isLoading && !fetchError">暂无客户数据。</p>
  </div>
</template>

<script>
import axios from 'axios';

// Use window.location.hostname to dynamically set the API host
// const API_URL = `http://${window.location.hostname}:8001/api/v1`; // Old hardcoded URL
const API_URL = '/api/v1'; // Use relative path to leverage vue.config.js proxy

export default {
  name: 'CustomerManagement',
  data() {
    return {
      customers: [],
      currentCustomer: { // Renamed from newCustomer for clarity, used for both add and edit
        id: null, // To store ID when editing
        area_code: '',
        name: '',
        shipping_address: ''
      },
      isEditing: false, // Flag to indicate if we are in edit mode
      searchQuery: '', 
      isLoading: false,
      fetchError: null,
      formError: null, // Combined error message for add/edit form
      searchTimeout: null,
    };
  },
  computed: {
    formTitle() {
      return this.isEditing ? '编辑客户信息' : '添加新客户';
    },
    submitButtonText() {
      return this.isEditing ? '更新客户' : '添加客户';
    }
  },
  methods: {
    resetForm() {
      this.currentCustomer.id = null;
      this.currentCustomer.area_code = '';
      this.currentCustomer.name = '';
      this.currentCustomer.shipping_address = '';
      this.isEditing = false;
      this.formError = null;
    },
    async fetchCustomers() {
      this.isLoading = true;
      this.fetchError = null;
      let url = `${API_URL}/customers/`;
      if (this.searchQuery && this.searchQuery.trim() !== '') {
        url += `?search=${encodeURIComponent(this.searchQuery.trim())}`;
      }
      try {
        const response = await axios.get(url);
        this.customers = response.data;
      } catch (error) {
        console.error('获取客户列表失败:', error);
        this.fetchError = '无法加载客户列表。请检查网络连接或稍后再试。';
        if (error.response) {
          console.error('错误详情:', error.response.data);
        }
      } finally {
        this.isLoading = false;
      }
    },
    startEditCustomer(customer) {
      this.isEditing = true;
      // Deep copy customer data to avoid modifying the original object in the list directly
      this.currentCustomer = { ...customer }; 
      this.formError = null;
      window.scrollTo(0, 0); // Scroll to top to make the form visible
    },
    cancelEdit() {
      this.resetForm();
    },
    async handleSubmitCustomer() {
      this.formError = null;
      if (!this.currentCustomer.area_code || !this.currentCustomer.name || !this.currentCustomer.shipping_address) {
        this.formError = '所有字段均为必填项。';
        return;
      }

      try {
        if (this.isEditing) {
          // Update existing customer
          const response = await axios.put(`${API_URL}/customers/${this.currentCustomer.id}/`, this.currentCustomer);
          if (response.status === 200) {
            alert('客户信息更新成功！');
            this.fetchCustomers();
            this.resetForm();
          }
        } else {
          // Add new customer
          const response = await axios.post(`${API_URL}/customers/`, this.currentCustomer);
          if (response.status === 201) {
            alert('客户添加成功！');
            this.fetchCustomers();
            this.resetForm(); // Reset form for next entry
          }
        }
      } catch (error) {
        console.error(this.isEditing ? '更新客户失败:' : '添加客户失败:', error);
        this.formError = (this.isEditing ? '更新' : '添加') + '客户失败。';
        if (error.response && error.response.data) {
          let messages = [];
          // Handle DRF error response structure (often an object with field names as keys)
          if (typeof error.response.data === 'object' && error.response.data !== null) {
            for (const key in error.response.data) {
              if (Array.isArray(error.response.data[key])) {
                messages.push(`${key}: ${error.response.data[key].join(', ')}`);
              } else {
                messages.push(`${key}: ${error.response.data[key]}`);
              }
            }
          } else if (typeof error.response.data === 'string') {
             messages.push(error.response.data);
          }
          if (messages.length > 0) {
            this.formError += ' ' + messages.join('; ');
          } else {
            this.formError += ' 请检查提交的数据。';
          }
        }
      }
    },
    async deleteCustomer(customerId) {
      if (!confirm('确定要删除这位客户吗？此操作无法撤销。')) {
        return;
      }
      try {
        const response = await axios.delete(`${API_URL}/customers/${customerId}/`);
        if (response.status === 204) { // 204 No Content 表示成功删除
          alert('客户删除成功！');
          this.fetchCustomers(); // 重新获取客户列表
        } else {
          // 理论上 axios 应该在非 2xx 时抛出错误，但以防万一
          alert('删除客户失败：服务器返回非预期状态。');
        }
      } catch (error) {
        console.error('删除客户失败:', error);
        let message = '删除客户失败。';
        if (error.response && error.response.data) {
          // 尝试从后端获取更详细的错误信息（如果存在）
          const errorData = error.response.data;
          if (typeof errorData === 'string') {
            message += ` ${errorData}`;
          } else if (errorData.detail) {
            message += ` ${errorData.detail}`;
          } else {
            // 通用错误处理
            message += ' 请检查网络连接或稍后再试。';
          }
        } else if (error.request) {
          message += ' 服务器无响应，请检查网络连接。';
        } else {
          message += ' 发生未知错误。';
        }
        alert(message);
      }
    },
    handleSearchInput() {
      // 防抖处理：用户停止输入一段时间后再执行搜索
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(() => {
        this.fetchCustomers();
      }, 300); // 300毫秒延迟
    }
  },
  mounted() {
    this.fetchCustomers(); // 组件加载时获取客户列表
  }
  // watch: { // 另一种实现搜索的方式（如果选择直接观察 searchQuery）
  //   searchQuery(newVal, oldVal) {
  //     if (newVal !== oldVal) {
  //        this.handleSearchInput();
  //     }
  //   }
  // }
};
</script>

<style scoped>
.search-bar {
  margin-bottom: 20px;
  display: flex;
  justify-content: center; /* 水平居中搜索框 */
}

.search-bar input[type="text"] {
  width: 60%; /* 可以根据需要调整宽度 */
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
  font-size: 1em; /* 确保字体大小合适 */
}

.customer-list-item {
  display: flex;
  justify-content: space-between; /* Pushes info to left, actions to right */
  align-items: center; /* Vertically centers both info block and actions block relative to each other */
  /* margin-bottom: 10px; // Let the parent ul/li styles handle this if needed, or ensure it's from .customer-list li */
}

.customer-list-item > div:first-child { /* Target the div containing name and address */
  flex-grow: 1; /* Allow the info div to take up available space */
  /* Text within this div will align left by default */
}

.customer-actions {
  display: flex;
  align-items: center; /* Vertically align buttons within this actions container */
  margin-left: 15px; /* Space between info and actions */
  flex-shrink: 0; /* Prevent the button container from shrinking */
}

.edit-button, .delete-button {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  /* Removed margin-left from individual delete-button, handled by margin-right on edit-button or gap on parent */
}

.edit-button {
  background-color: #ffc107; /* Example: Yellow for edit */
  color: #212529;
  margin-right: 8px; /* Space between edit and delete buttons */
}

.edit-button:hover {
  background-color: #e0a800;
}

.delete-button {
  background-color: #dc3545;
  color: white;
}

.delete-button:hover {
  background-color: #c82333;
}

.customer-management {
  font-family: sans-serif;
  max-width: 800px;
  margin: 20px auto;
  padding: 20px;
  border: 1px solid #eee;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

h2, h3 {
  color: #333;
  text-align: center;
}

.customer-form {
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 6px;
}

.customer-form div {
  margin-bottom: 15px;
}

.customer-form label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.customer-form input[type="text"],
.customer-form textarea {
  width: calc(100% - 22px); /* 减去 padding 和 border */
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.customer-form button {
  background-color: #007bff;
  color: white;
  padding: 10px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.customer-form button:hover {
  background-color: #0056b3;
}

.customer-list {
  list-style-type: none;
  padding: 0;
}

.customer-list li {
  background-color: #fff;
  border: 1px solid #ddd;
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 4px;
}

.customer-list strong {
  font-size: 1.1em;
  color: #0056b3;
}

.customer-list p {
  margin: 5px 0 0;
  color: #555;
}

.loading-message {
  text-align: center;
  padding: 20px;
  color: #555;
}

.error-message {
  color: red;
  margin-top: 10px;
  text-align: center;
}

</style>
