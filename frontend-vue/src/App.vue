<template>
  <div id="app">
    <b-navbar toggleable="lg" type="dark" variant="primary">
      <b-navbar-brand href="#">翻译工作平台</b-navbar-brand>

      <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>

      <b-collapse id="nav-collapse" is-nav>
        <b-navbar-nav>
          <b-nav-item to="/" exact>首页</b-nav-item>
          <b-nav-item to="/projects">项目管理</b-nav-item>
        </b-navbar-nav>
      </b-collapse>
    </b-navbar>

    <b-container class="py-3">
      <b-alert
        :show="!!errorMessage"
        dismissible
        variant="danger"
        @dismissed="errorMessage = ''"
      >
        {{ errorMessage }}
      </b-alert>

      <b-alert
        :show="!!successMessage"
        dismissible
        variant="success"
        @dismissed="successMessage = ''"
      >
        {{ successMessage }}
      </b-alert>

      <router-view 
        @show-error="showError" 
        @show-success="showSuccess"
      />
    </b-container>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      errorMessage: '',
      successMessage: ''
    }
  },
  methods: {
    showError(message) {
      this.errorMessage = message;
      setTimeout(() => {
        this.errorMessage = '';
      }, 5000);
    },
    showSuccess(message) {
      this.successMessage = message;
      setTimeout(() => {
        this.successMessage = '';
      }, 3000);
    }
  }
}
</script>

<style>
html, body {
  height: 100%;
}

#app {
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #333;
  min-height: 100%;
  background-color: #f5f7fa;
}

.navbar {
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
}

.container {
  padding-top: 1.5rem;
  padding-bottom: 2rem;
}

.loading-overlay {
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.7);
  z-index: 1000;
}

.card {
  margin-bottom: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  border: none;
  border-radius: 0.5rem;
  overflow: hidden;
}

.card-header {
  background-color: rgba(0, 0, 0, 0.03);
  border-bottom: 1px solid rgba(0, 0, 0, 0.125);
  padding: 0.75rem 1.25rem;
}

.card-body {
  padding: 1.5rem;
}

.btn {
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  transition: all 0.2s;
}

.btn-primary {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.btn-primary:hover {
  background-color: #0b5ed7;
  border-color: #0a58ca;
}

.alert {
  border: none;
  border-radius: 0.5rem;
  margin-bottom: 1.5rem;
}

.status-completed {
  color: #28a745;
}

.status-pending {
  color: #ffc107;
}

.translation-item {
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  padding: 15px;
  margin-bottom: 15px;
  transition: all 0.3s ease;
}

.translation-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
}

.translation-item.completed {
  border-left: 5px solid #28a745;
}

.original-text {
  margin-bottom: 10px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 5px;
}

.breadcrumb {
  background-color: transparent;
  padding: 0.5rem 0;
  margin-bottom: 1.5rem;
}

.jumbotron {
  background-color: #f8f9fa;
  border-radius: 0.5rem;
  padding: 2rem;
  margin-bottom: 2rem;
}

/* Custom animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.fade-in {
  animation: fadeIn 0.5s ease-in;
}
</style>