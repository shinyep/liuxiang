<template>
  <div class="statistics-dashboard">
    <div class="controls-bar">
      <div class="filter-group year-selector">
        <label for="year-filter-stats">选择年份:</label>
        <select id="year-filter-stats" v-model="selectedYear">
          <option v-for="yearValue in availableYears" :key="yearValue" :value="yearValue">
            {{ yearValue }}
          </option>
        </select>
      </div>
      <div class="filter-group month-selector">
        <label for="month-filter-stats">选择月份:</label>
        <select id="month-filter-stats" v-model="selectedMonth">
          <option v-for="monthOption in availableMonths" :key="monthOption.value" :value="monthOption.value">
            {{ monthOption.text }}
          </option>
        </select>
      </div>
    </div>

    <!-- <div class="stats-section">
      <h2>车次统计数据 ({{ selectedYear }}年{{ selectedMonth === 0 ? '全年' : selectedMonth.toString().padStart(2, '0') + '月' }})</h2>
      <div v-if="loading" class="loading">正在加载车次数据...</div>
      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="!loading && !error && groupedStatistics.length === 0" class="no-data">
        {{ selectedYear }}年暂无车次统计数据。
      </div>
      <div v-for="group in groupedStatistics" :key="group.year" class="year-group">
        <table class="statistics-table">
          <thead>
            <tr>
              <th>发货时间</th>
              <th>区域码</th>
              <th>客户信息</th>
              <th>品项</th>
              <th>数量</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(stat, index) in group.stats" :key="index">
              <td>{{ stat.shipment_date }}</td>
              <td>{{ stat.customer_area_code }}</td>
              <td>{{ stat.customer_name }}</td>
              <td>{{ stat.item_name }}</td>
              <td>{{ stat.total_quantity }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div> -->

    <div class="stats-section material-stats-section">
      <h2>物料出库统计 ({{ selectedYear }}年{{ selectedMonth === 0 ? '全年' : selectedMonth.toString().padStart(2, '0') + '月' }})</h2>
      <div v-if="materialLoading" class="loading">正在加载物料出库数据...</div>
      <div v-if="materialError" class="error">{{ materialError }}</div>
      <div v-if="!materialLoading && !materialError && materialStatistics.length === 0" class="no-data">
        {{ selectedYear }}年暂无物料出库统计数据。
      </div>
      <table v-if="!materialLoading && !materialError && materialStatistics.length > 0" class="statistics-table">
        <thead>
          <tr>
            <th>物料编号</th>
            <th>物料描述</th>
            <th>总出库数量</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(mStat, index) in materialStatistics" :key="index">
            <td>{{ mStat.material_number }}</td>
            <td>{{ mStat.material_description }}</td>
            <td>{{ mStat.total_shipped_quantity }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="stats-section customer-stats-section">
      <h2>客户出库统计 ({{ selectedYear }}年{{ selectedMonth === 0 ? '全年' : selectedMonth.toString().padStart(2, '0') + '月' }})</h2>
      <div v-if="customerLoading" class="loading">正在加载客户出库数据...</div>
      <div v-if="customerError" class="error">{{ customerError }}</div>
      <div v-if="!customerLoading && !customerError && customerStatistics.length === 0" class="no-data">
        {{ selectedYear }}年暂无客户出库统计数据。
      </div>
      <table v-if="!customerLoading && !customerError && customerStatistics.length > 0" class="statistics-table">
        <thead>
          <tr>
            <th>区域码</th>
            <th>客户名称</th>
            <th>送货地址</th>
            <th>物料编号</th>
            <th>物料描述</th>
            <th>数量</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(cStat, index) in customerStatistics" :key="index">
            <td>{{ cStat.area_code }}</td>
            <td>{{ cStat.customer_name }}</td>
            <td>{{ cStat.shipping_address }}</td>
            <td>{{ cStat.material_number }}</td>
            <td>{{ cStat.material_description }}</td>
            <td>{{ cStat.quantity }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'StatisticsDashboard',
  data() {
    return {
      statistics: [], // Raw statistics from API for trip statistics
      loading: true,
      error: null,
      materialStatistics: [], // Raw statistics from API for material shipments
      materialLoading: true,
      materialError: null,
      customerStatistics: [],
      customerLoading: true,
      customerError: null,
      selectedYear: new Date().getFullYear(), // Default to current year for filtering
      selectedMonth: new Date().getMonth() + 1, // Default to current month (1-12)
      // availableYears will be populated by computed property
    };
  },
  computed: {
    availableMonths() {
      const months = [{ value: 0, text: '全年' }];
      for (let i = 1; i <= 12; i++) {
        months.push({ value: i, text: `${i.toString().padStart(2, '0')}月` });
      }
      return months;
    },
    availableYears() {
      const years = new Set();
      if (this.statistics && this.statistics.length > 0) {
        this.statistics.forEach(stat => {
          if (stat.shipment_date) {
            const year = new Date(stat.shipment_date).getFullYear();
            if (!isNaN(year)) {
              years.add(year);
            }
          }
        });
      }
      // Ensure current selectedYear is in the list, especially on initial load or if data is empty for that year
      if (!isNaN(this.selectedYear) && !years.has(this.selectedYear)) {
        years.add(this.selectedYear);
      }
      if (years.size === 0) { // Fallback if no data and selectedYear wasn't added
          years.add(new Date().getFullYear());
      }
      return Array.from(years).sort((a, b) => b - a); // Sort descending
    },
    groupedStatistics() {
      if (!this.statistics || this.statistics.length === 0) {
        return [];
      }
      const groups = {};
      this.statistics.forEach(stat => {
        if (stat.shipment_date) {
          const year = new Date(stat.shipment_date).getFullYear();
          // Only group stats that match the selectedYear
          if (year === this.selectedYear) {
            if (!groups[year]) {
              // We are only showing one year at a time based on selectedYear,
              // so the top-level group key is less critical here.
              groups[year] = { year: year, stats: [] };
            }
            groups[year].stats.push(stat);
          }
        }
        // Not handling "未知年份" for groupedStatistics as it's now filtered by selectedYear.
        // If selectedYear could be "未知年份", that would need different logic.
      });
      // The output will effectively be an array with one group (for the selectedYear)
      // or an empty array if no stats for that year.
      return Object.values(groups); // No need to sort by year as there's only one
    }
  },
  watch: {
    selectedYear(newYear, oldYear) {
      if (newYear !== oldYear) {
        // When year changes, fetch data for the new year and current month
        this.fetchAllDataForYearMonth(newYear, this.selectedMonth);
      }
    },
    selectedMonth(newMonth, oldMonth) {
      if (newMonth !== oldMonth) {
        // When month changes, fetch data for the current year and new month
        this.fetchAllDataForYearMonth(this.selectedYear, newMonth);
      }
    }
  },
  created() {
    this.fetchAllDataForYearMonth(this.selectedYear, this.selectedMonth);
  },
  methods: {
    async fetchAllDataForYearMonth(year, month) {
      this.loading = true; // For trip statistics
      this.error = null;
      this.materialLoading = true; // For material statistics
      this.materialError = null;
      this.customerLoading = true;
      this.customerError = null;

      try {
        // Fetch trip statistics (still annually for now, or adjust if monthly needed)
        // For now, trip statistics remain annually filtered by selectedYear in groupedStatistics.
        // If trip statistics also need to be fetched monthly, this API call would need a month param.
        const tripStatsUrl = `/api/v1/shipment-statistics/`; // Potentially add ?year=${year} if API supports
        const statsPromise = axios.get(tripStatsUrl);
        
        // Fetch material statistics for the given year and month
        let materialStatsUrl = `/api/v1/statistics/material-shipments/?year=${year}`;
        if (month && month !== 0) { // month = 0 means 'All Months'
          materialStatsUrl += `&month=${month}`;
        }
        const materialStatsPromise = axios.get(materialStatsUrl);

        // Fetch customer statistics
        let customerStatsUrl = `/api/v1/statistics/customer-shipments/?year=${year}`;
        if (month && month !== 0) {
          customerStatsUrl += `&month=${month}`;
        }
        const customerStatsPromise = axios.get(customerStatsUrl);


        const [statsResponse, materialStatsResponse, customerStatsResponse] = await Promise.all([statsPromise, materialStatsPromise, customerStatsPromise]);
        
        this.statistics = statsResponse.data;
        this.materialStatistics = materialStatsResponse.data;
        this.customerStatistics = customerStatsResponse.data;

      } catch (err) {
        console.error('获取统计数据失败:', err);
        if (err.config && err.config.url.includes('customer-shipments')) {
            this.customerError = `无法加载客户出库统计数据。(${err.message})`;
        } else if (err.config && err.config.url.includes('material-shipments')) {
            this.materialError = `无法加载物料出库统计数据。(${err.message})`;
        } else {
            this.error = `无法加载车次统计数据。(${err.message})`;
        }
      } finally {
        this.loading = false;
        this.materialLoading = false;
        this.customerLoading = false;
      }
    },
  },
};
</script>

<style scoped>
.statistics-dashboard {
  padding: 20px;
  background-color: #f9f9f9; /* Light gray background for the whole page */
}

.controls-bar {
  background-color: #fff;
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  justify-content: center; /* Center the filter groups */
  gap: 30px; /* Add some space between year and month selectors */
}

.filter-group {
  display: flex;
  align-items: center;
}

.filter-group label {
  margin-right: 10px;
  font-weight: bold;
  color: #555;
}

.filter-group select {
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #ddd;
  font-size: 1em;
}

.stats-section {
  background-color: #fff;
  padding: 20px;
  margin-bottom: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}


.statistics-dashboard h2 {
  text-align: center;
  color: #333;
  margin-bottom: 25px;
  font-size: 1.8em;
}

.loading, .error, .no-data {
  text-align: center;
  padding: 20px;
  font-size: 1.1em;
  color: #555;
}

.error {
  color: #e74c3c; /* Red color for errors */
}

.statistics-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.statistics-table th,
.statistics-table td {
  border: 1px solid #ddd;
  padding: 12px 15px;
  text-align: left;
  font-size: 0.95em;
}

.statistics-table th {
  background-color: #42b983; /* Green header like the app's theme */
  color: white;
  font-weight: bold;
}

.statistics-table tbody tr:nth-child(even) {
  background-color: #f9f9f9; /* Zebra striping for rows */
}

.statistics-table tbody tr:hover {
  background-color: #f1f1f1; /* Highlight on hover */
}
</style>
