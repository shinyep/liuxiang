<template>
  <div id="app">
    <header>
      <h1>成品追溯与客户管理系统</h1>
      <nav class="view-selector">
        <button @click="currentView = 'shipment'" :class="{ active: currentView === 'shipment' }">成品流向系统</button>
        <button @click="currentView = 'customer'" :class="{ active: currentView === 'customer' }">客户信息系统</button>
        <button @click="currentView = 'statistics'" :class="{ active: currentView === 'statistics' }">统计数据</button>
      </nav>
    </header>
    <main>
      <ShipmentTracking v-if="currentView === 'shipment'" @shipment-data-updated="handleShipmentDataUpdate" />
      <CustomerManagement v-if="currentView === 'customer'" />
      <StatisticsDashboard v-if="currentView === 'statistics'" :key="statisticsComponentKey" />
    </main>
  </div>
</template>

<script>
import ShipmentTracking from './components/ShipmentTracking.vue';
import CustomerManagement from './components/CustomerManagement.vue';
import StatisticsDashboard from './components/StatisticsDashboard.vue';

export default {
  name: 'App',
  components: {
    ShipmentTracking,
    CustomerManagement,
    StatisticsDashboard
  },
  data() {
    return {
      currentView: 'shipment', // 默认视图
      statisticsComponentKey: 0
    };
  },
  methods: {
    handleShipmentDataUpdate() {
      // Increment the key to force re-mounting of the StatisticsDashboard component
      this.statisticsComponentKey += 1;
      console.log('Shipment data updated, statistics key is now:', this.statisticsComponentKey);
    }
  }
};
</script>

<style>
/* Basic App styling */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin-top: 0px;
}

header {
  background-color: #42b983;
  padding: 20px;
  color: white;
  text-align: center;
  margin-bottom: 20px;
}

header h1 {
  margin: 0 0 15px 0; /* Increased bottom margin for spacing */
  font-size: 1.8em;
}

.view-selector { /* Styles for the nav container */
  display: flex;
  justify-content: center;
  gap: 30px; /* Space between nav items */
}

.view-selector button { /* Common style for nav items */
  background-color: transparent;
  border: none; /* Remove button border */
  color: white;
  padding: 8px 0; /* Vertical padding, no horizontal for underline to span text */
  margin: 0; 
  cursor: pointer;
  font-size: 1.1em; /* Slightly larger font for nav items */
  text-decoration: none; 
  position: relative; /* For ::after pseudo-element for underline */
  transition: color 0.3s;
  outline: none; /* Remove default focus outline */
}

.view-selector button::after { /* Underline effect */
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%; /* Start underline from center */
  transform: translateX(-50%); /* Adjust to truly center */
  width: 0; /* Start with no width */
  height: 2px;
  background-color: white;
  transition: width 0.3s ease-in-out;
}

.view-selector button:hover::after,
.view-selector button.active::after {
  width: 100%; /* Expand underline to full width on hover and active */
}

.view-selector button.active {
  font-weight: bold; /* Active item is bold */
}

.view-selector button:hover:not(.active) {
  opacity: 0.8; /* Slight opacity change on hover for non-active items */
}

main {
  padding: 0 20px;
}

body {
  margin: 0;
  padding: 0;
  background-color: #f4f4f4;
}
</style>
