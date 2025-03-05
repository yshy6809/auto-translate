<template>
  <div class="home">
    <!-- More compact jumbotron with better spacing -->
    <b-jumbotron 
      class="home-jumbotron py-4 mb-4"
      header="翻译工作平台" 
      lead="高效管理您的翻译项目"
    >
      <p>这是一个简单而强大的翻译管理工具，帮助您组织和跟踪多个翻译项目的进度。</p>
      <b-button variant="primary" size="lg" to="/projects" class="mt-2">开始使用</b-button>
    </b-jumbotron>

    <!-- Feature cards section with improved layout -->
    <h2 class="text-center mb-4">主要功能</h2>
    <b-row>
      <b-col lg="4" md="4" sm="12" class="mb-4">
        <b-card 
          class="text-center h-100 feature-card" 
          bg-variant="light" 
          border-variant="light"
        >
          <div class="icon-wrapper mb-3">
            <b-icon icon="folder-plus" font-scale="3"></b-icon>
          </div>
          <h3 class="card-title h4">创建项目</h3>
          <b-card-text>
            创建和管理不同的翻译项目，每个项目可以包含多个文件。
          </b-card-text>
        </b-card>
      </b-col>
      
      <b-col lg="4" md="4" sm="12" class="mb-4">
        <b-card 
          class="text-center h-100 feature-card" 
          bg-variant="light" 
          border-variant="light"
        >
          <div class="icon-wrapper mb-3">
            <b-icon icon="cloud-upload" font-scale="3"></b-icon>
          </div>
          <h3 class="card-title h4">上传文件</h3>
          <b-card-text>
            上传待翻译的文本文件，系统会自动分段以便翻译。
          </b-card-text>
        </b-card>
      </b-col>
      
      <b-col lg="4" md="4" sm="12" class="mb-4">
        <b-card 
          class="text-center h-100 feature-card" 
          bg-variant="light" 
          border-variant="light"
        >
          <div class="icon-wrapper mb-3">
            <b-icon icon="bar-chart-line" font-scale="3"></b-icon>
          </div>
          <h3 class="card-title h4">翻译进度</h3>
          <b-card-text>
            跟踪每个项目和文件的翻译进度，方便管理工作任务。
          </b-card-text>
        </b-card>
      </b-col>
    </b-row>

    <!-- Added workflow section for better user guidance -->
    <b-card class="mt-5 mb-3 workflow-card">
      <h2 class="text-center mb-4">如何使用</h2>
      <b-card-text>
        <b-row align-v="center" class="workflow-step">
          <b-col md="2" class="text-center">
            <div class="step-number">1</div>
          </b-col>
          <b-col md="10">
            <h4>创建翻译项目</h4>
            <p>为您的翻译工作创建一个新项目，添加描述以便于管理。</p>
          </b-col>
        </b-row>
        
        <b-row align-v="center" class="workflow-step">
          <b-col md="2" class="text-center">
            <div class="step-number">2</div>
          </b-col>
          <b-col md="10">
            <h4>上传文件</h4>
            <p>上传需要翻译的文本文件，系统会自动将内容分段。</p>
          </b-col>
        </b-row>
        
        <b-row align-v="center" class="workflow-step">
          <b-col md="2" class="text-center">
            <div class="step-number">3</div>
          </b-col>
          <b-col md="10">
            <h4>翻译内容</h4>
            <p>逐段翻译文件内容，随时保存进度。</p>
          </b-col>
        </b-row>
        
        <b-row align-v="center" class="workflow-step">
          <b-col md="2" class="text-center">
            <div class="step-number">4</div>
          </b-col>
          <b-col md="10">
            <h4>下载翻译结果</h4>
            <p>完成翻译后，下载已翻译的文件。</p>
          </b-col>
        </b-row>
      </b-card-text>
      
      <div class="text-center mt-4">
        <b-button variant="primary" size="lg" to="/projects">立即开始</b-button>
      </div>
    </b-card>
  </div>
</template>

<script>
export default {
  name: 'Home'
}
</script>

<style scoped>
.home-jumbotron {
  background-color: #f8f9fa;
  border-radius: 0.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.icon-wrapper {
  height: 70px;
  width: 70px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(13, 110, 253, 0.1);
  border-radius: 50%;
  color: #0d6efd;
}

.feature-card {
  transition: all 0.3s ease;
  border: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
}

.workflow-card {
  border: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  background-color: #f8f9fa;
}

.workflow-step {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.workflow-step:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  margin: 0 auto;
  background-color: #0d6efd;
  color: white;
  font-size: 1.5rem;
  font-weight: bold;
  border-radius: 50%;
}

@media (max-width: 768px) {
  .workflow-step {
    text-align: center;
  }
  
  .step-number {
    margin-bottom: 1rem;
  }
}
</style>