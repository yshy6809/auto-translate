<template>
  <div class="project-detail">
    <b-overlay :show="$store.state.loading" rounded>
      <div v-if="project">
        <!-- Enhanced breadcrumb with better styling -->
        <nav aria-label="breadcrumb" class="mb-3">
          <b-breadcrumb class="bg-transparent p-0">
            <b-breadcrumb-item to="/projects">
              <b-icon icon="house-door-fill" class="mr-1"></b-icon>
              项目列表
            </b-breadcrumb-item>
            <b-breadcrumb-item active>{{ project.name }}</b-breadcrumb-item>
          </b-breadcrumb>
        </nav>

        <!-- Project header with improved layout -->
        <b-card no-body class="project-header-card mb-4">
          <b-card-body class="p-0">
            <div class="project-header">
              <div class="p-4">
                <div class="d-flex align-items-center mb-2">
                  <h1 class="project-title mb-0 mr-2">{{ project.name }}</h1>
                  <b-badge 
                    v-if="project.completionRate === 100"
                    variant="success" 
                    class="align-self-start mt-2"
                  >已完成</b-badge>
                </div>
                <p class="text-muted small mb-2">
                  <b-icon icon="calendar3" class="mr-1"></b-icon>
                  创建于: {{ formatDate(project.creationDate) }} | 
                  <b-icon icon="clock-history" class="mr-1"></b-icon>
                  最后更新: {{ formatDate(project.lastModified) }}
                </p>
                <p class="project-description mt-3">{{ project.description || '无描述' }}</p>
              </div>
              
              <!-- Project stats sidebar with better styling -->
              <div class="project-stats p-4">
                <h4 class="stats-title">项目概况</h4>
                <div class="completion-stat mt-3 mb-4">
                  <div class="d-flex justify-content-between mb-2">
                    <span class="stat-label">完成率</span>
                    <span class="stat-value">{{ project.completionRate }}%</span>
                  </div>
                  <b-progress 
                    :value="project.completionRate" 
                    :max="100" 
                    class="mb-2 progress-bar-custom"
                    height="12px"
                  ></b-progress>
                </div>
                
                <div class="file-stat">
                  <div class="d-flex justify-content-between">
                    <span class="stat-label">文件数</span>
                    <span class="stat-value">{{ project.files.length }}</span>
                  </div>
                </div>
              </div>
            </div>
          </b-card-body>
        </b-card>
        
        <!-- Improved file upload card -->
        <b-card no-body class="upload-card mb-4">
          <b-card-header class="bg-primary text-white py-3">
            <h3 class="mb-0">
              <b-icon icon="cloud-upload-fill" class="mr-2"></b-icon>
              上传文件
            </h3>
          </b-card-header>
          <b-card-body>
            <b-form @submit.prevent="uploadFile" class="mb-0">
              <div class="upload-zone">
                <b-form-file
                  v-model="fileToUpload"
                  accept=".txt"
                  placeholder="选择或拖放文件到这里..."
                  drop-placeholder="拖放文件到这里..."
                  required
                  class="custom-file-input"
                ></b-form-file>
              </div>
              <div class="mt-3 text-center">
                <b-button 
                  type="submit" 
                  variant="primary" 
                  size="lg"
                  class="px-4 upload-btn"
                  :disabled="!fileToUpload"
                >
                  <b-icon icon="upload" class="mr-2"></b-icon>
                  上传文件
                </b-button>
              </div>
            </b-form>
          </b-card-body>
        </b-card>

        <!-- Improved file list section -->
        <div class="mb-2 d-flex justify-content-between align-items-center">
          <h3 class="section-title">
            <b-icon icon="files" class="mr-2"></b-icon>
            文件列表
          </h3>
          <span class="text-muted">共 {{ project.files.length }} 个文件</span>
        </div>
        
        <!-- Enhanced empty state -->
        <div v-if="!project.files.length" class="text-center py-5 empty-state">
          <b-icon icon="file-earmark-text" font-scale="4" class="text-muted mb-3"></b-icon>
          <h4 class="text-muted">该项目暂无文件</h4>
          <p class="text-muted">请使用上方"上传文件"功能添加文件</p>
        </div>
        
        <!-- Improved table styling -->
        <b-card v-else no-body class="files-table-card">
          <b-table 
            :items="project.files"
            :fields="fields"
            hover
            responsive
            bordered
            class="mb-0 files-table"
            tbody-class="files-tbody"
          >
            <template #cell(fileName)="data">
              <div class="file-name">
                <b-icon icon="file-text" class="mr-2 text-primary"></b-icon>
                {{ data.item.fileName }}
              </div>
            </template>
            
            <template #cell(uploadDate)="data">
              <div class="upload-date">
                <b-icon icon="calendar-date" class="mr-2"></b-icon>
                {{ formatDate(data.item.uploadDate) }}
              </div>
            </template>
            
            <template #cell(completionRate)="data">
              <div class="completion-wrapper">
                <b-progress 
                  :value="data.item.completionRate" 
                  :max="100" 
                  class="progress-bar-custom"
                  height="10px"
                >
                  <b-progress-bar :value="data.item.completionRate">
                    <span class="progress-label">{{ data.item.completionRate }}%</span>
                  </b-progress-bar>
                </b-progress>
              </div>
            </template>
            
            <template #cell(actions)="data">
              <div class="action-buttons">
                <b-button 
                  variant="primary" 
                  size="sm" 
                  class="action-btn mr-2" 
                  @click="goToTranslation(data.item.id)"
                >
                  <b-icon icon="translate" class="mr-1"></b-icon>
                  翻译
                </b-button>
                <b-button 
                  variant="outline-danger" 
                  size="sm" 
                  class="action-btn"
                  @click="confirmDeleteFile(data.item.id, data.item.fileName)"
                >
                  <b-icon icon="trash" class="mr-1"></b-icon>
                  删除
                </b-button>
              </div>
            </template>
            
            <!-- Custom header styling -->
            <template #head(fileName)>
              <div class="th-inner">
                <b-icon icon="file-earmark" class="mr-1"></b-icon>
                文件名
              </div>
            </template>
            
            <template #head(uploadDate)>
              <div class="th-inner">
                <b-icon icon="calendar" class="mr-1"></b-icon>
                上传时间
              </div>
            </template>
            
            <template #head(completionRate)>
              <div class="th-inner">
                <b-icon icon="bar-chart-line" class="mr-1"></b-icon>
                完成率
              </div>
            </template>
            
            <template #head(actions)>
              <div class="th-inner">
                <b-icon icon="gear" class="mr-1"></b-icon>
                操作
              </div>
            </template>
          </b-table>
        </b-card>
      </div>
      
      <!-- Improved error state -->
      <div v-else class="text-center py-5 error-state">
        <b-icon icon="exclamation-circle" font-scale="4" variant="danger" class="mb-3"></b-icon>
        <b-alert show variant="danger" class="d-inline-block">项目不存在或加载失败</b-alert>
        <div class="mt-3">
          <b-button to="/projects" variant="primary" size="lg">
            <b-icon icon="arrow-left" class="mr-2"></b-icon>
            返回项目列表
          </b-button>
        </div>
      </div>
    </b-overlay>
    
    <!-- Enhanced delete confirmation modal -->
    <b-modal 
      id="delete-file-modal" 
      centered
      title="确认删除" 
      header-bg-variant="danger"
      header-text-variant="white"
      ok-title="删除" 
      ok-variant="danger"
      cancel-title="取消"
      @ok="deleteFile"
    >
      <div class="d-flex align-items-center">
        <b-icon icon="exclamation-triangle-fill" variant="danger" font-scale="2" class="mr-3"></b-icon>
        <p class="mb-0">确定要删除文件"<strong>{{ fileToDelete.name }}</strong>"吗？<br>此操作<strong>无法撤销</strong>。</p>
      </div>
    </b-modal>
  </div>
</template>

<script>
export default {
  name: 'ProjectDetail',
  props: {
    id: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      fileToUpload: null,
      fileToDelete: {
        id: null,
        name: ''
      },
      fields: [
        { key: 'fileName', label: '文件名', class: 'file-name-col' },
        { key: 'uploadDate', label: '上传时间', class: 'upload-date-col' },
        { key: 'completionRate', label: '完成率', class: 'completion-col' },
        { key: 'actions', label: '操作', class: 'actions-col' }
      ]
    }
  },
  computed: {
    project() {
      return this.$store.state.currentProject;
    }
  },
  created() {
    this.fetchProject();
  },
  methods: {
    async fetchProject() {
      try {
        await this.$store.dispatch('fetchProject', this.id);
        
        if (!this.project) {
          this.$emit('show-error', '找不到该项目');
          this.$router.push('/projects');
        }
      } catch (error) {
        this.$emit('show-error', error.response?.data?.error || '获取项目详情失败');
        this.$router.push('/projects');
      }
    },
    async uploadFile() {
      if (!this.fileToUpload) return;
      
      try {
        const formData = new FormData();
        formData.append('file', this.fileToUpload);
        
        await this.$store.dispatch('uploadFile', {
          projectId: this.id,
          formData
        });
        
        this.$emit('show-success', '文件上传成功');
        this.fileToUpload = null;
      } catch (error) {
        this.$emit('show-error', error.response?.data?.error || '上传文件失败');
      }
    },
    goToTranslation(fileId) {
      this.$router.push(`/translation/${this.id}/${fileId}`);
    },
    confirmDeleteFile(id, name) {
      this.fileToDelete = { id, name };
      this.$bvModal.show('delete-file-modal');
    },
    async deleteFile() {
      try {
        await this.$store.dispatch('deleteFile', {
          projectId: this.id,
          fileId: this.fileToDelete.id
        });
        this.$emit('show-success', '文件删除成功');
      } catch (error) {
        this.$emit('show-error', error.response?.data?.error || '删除文件失败');
      }
    },
    formatDate(dateString) {
      return new Date(dateString).toLocaleString();
    }
  }
}
</script>

<style scoped>
/* Project header styling */
.project-header-card {
  overflow: hidden;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.project-header {
  display: flex;
  flex-direction: row;
}

.project-title {
  font-weight: 700;
  color: #333;
  font-size: 1.8rem;
  border-bottom: 3px solid #007bff;
  padding-bottom: 0.5rem;
  display: inline-block;
}

.project-description {
  font-size: 1rem;
  color: #6c757d;
  max-width: 800px;
}

.project-stats {
  min-width: 250px;
  background-color: #f8f9fa;
  border-left: 1px solid #dee2e6;
}

.stats-title {
  font-weight: 600;
  color: #495057;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #dee2e6;
}

.stat-label {
  font-weight: 600;
  color: #6c757d;
}

.stat-value {
  font-weight: 700;
  color: #495057;
}

/* Upload section styling */
.upload-card {
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.upload-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.upload-zone {
  padding: 20px;
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  background-color: #f8f9fa;
  transition: all 0.3s ease;
}

.upload-zone:hover {
  border-color: #007bff;
  background-color: rgba(13, 110, 253, 0.05);
}

.upload-btn {
  transition: all 0.2s ease;
  min-width: 140px;
}

.upload-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
}

/* File list section styling */
.section-title {
  font-weight: 700;
  color: #495057;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  display: inline-block;
}

.empty-state {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.05);
}

.files-table-card {
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.files-table {
  margin-bottom: 0;
}

.files-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  border-top: none;
}

.th-inner {
  font-weight: 600;
  color: #495057;
}

.file-name {
  font-weight: 500;
}

.file-name-col {
  width: 35%;
}

.upload-date-col {
  width: 20%;
}

.completion-col {
  width: 25%;
}

.actions-col {
  width: 20%;
  text-align: center;
}

/* Progress bar styling */
.progress-bar-custom {
  border-radius: 6px;
  overflow: hidden;
}

.progress-label {
  position: absolute;
  right: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  text-shadow: 0 0 2px rgba(0, 0, 0, 0.5);
}

/* Action buttons */
.action-buttons {
  display: flex;
  justify-content: center;
}

.action-btn {
  min-width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

/* Error state */
.error-state {
  padding: 3rem 1rem;
  border-radius: 8px;
  background-color: #f8f9fa;
}

/* Responsive adjustments */
@media (max-width: 991.98px) {
  .project-header {
    flex-direction: column;
  }
  
  .project-stats {
    border-left: none;
    border-top: 1px solid #dee2e6;
  }
}

@media (max-width: 767.98px) {
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .action-btn {
    margin-bottom: 0.5rem;
    margin-right: 0 !important;
  }
  
  .file-name-col, .upload-date-col, .completion-col, .actions-col {
    width: auto;
  }
}
</style>