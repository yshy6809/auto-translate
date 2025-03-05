<template>
  <div class="translation">
    <b-overlay :show="$store.state.loading" rounded>
      <div v-if="currentFile && currentProject">
        <!-- Enhanced breadcrumb with icons -->
        <nav aria-label="breadcrumb" class="mb-3">
          <b-breadcrumb class="bg-transparent p-0">
            <b-breadcrumb-item to="/projects">
              <b-icon icon="house-door-fill" class="mr-1"></b-icon>
              项目列表
            </b-breadcrumb-item>
            <b-breadcrumb-item :to="`/projects/${projectId}`">
              <b-icon icon="folder-fill" class="mr-1"></b-icon>
              {{ currentProject.name }}
            </b-breadcrumb-item>
            <b-breadcrumb-item active>
              <b-icon icon="file-text-fill" class="mr-1"></b-icon>
              {{ currentFile.fileName }}
            </b-breadcrumb-item>
          </b-breadcrumb>
        </nav>
        
        <!-- Improved header with file info and stats -->
        <b-card no-body class="header-card mb-4">
          <div class="file-header">
            <!-- File info section -->
            <div class="file-info p-4">
              <div class="d-flex align-items-center mb-2">
                <h1 class="file-title mb-0">{{ currentFile.fileName }}</h1>
                <b-badge 
                  v-if="completionRate === 100" 
                  variant="success" 
                  class="ml-3"
                >
                  已完成
                </b-badge>
              </div>
              <p class="file-meta">
                <b-icon icon="calendar3" class="mr-1"></b-icon>
                上传于: {{ formatDate(currentFile.uploadDate) }}
              </p>
            </div>
            
            <!-- Stats section -->
            <div class="file-stats p-4">
              <div class="stats-grid">
                <div class="stat-item">
                  <div class="stat-icon">
                    <b-icon icon="file-text" font-scale="1.5"></b-icon>
                  </div>
                  <div class="stat-label">总段落数</div>
                  <div class="stat-value">{{ originalSegments.length }}</div>
                </div>
                
                <div class="stat-item">
                  <div class="stat-icon">
                    <b-icon icon="check-circle" font-scale="1.5"></b-icon>
                  </div>
                  <div class="stat-label">已完成</div>
                  <div class="stat-value">{{ completedSegmentsCount }}</div>
                </div>
                
                <div class="stat-item">
                  <div class="stat-icon">
                    <b-icon icon="bar-chart-line" font-scale="1.5"></b-icon>
                  </div>
                  <div class="stat-label">完成率</div>
                  <div class="stat-value">{{ completionRate }}%</div>
                </div>
              </div>
              
              <b-progress 
                :value="completionRate" 
                :max="100" 
                class="mt-3 progress-bar-custom"
                height="12px"
              >
                <b-progress-bar :value="completionRate">
                  <span class="progress-label">{{ completionRate }}%</span>
                </b-progress-bar>
              </b-progress>
            </div>
          </div>
        </b-card>
        
        <!-- Improved controls card with better layout -->
        <b-card no-body class="controls-card mb-4">
          <b-card-header class="bg-primary text-white">
            <h3 class="mb-0">
              <b-icon icon="gear-fill" class="mr-2"></b-icon>
              翻译控制
            </h3>
          </b-card-header>
          <b-card-body>
            <!-- Search and filter controls -->
            <b-row class="mb-3">
              <b-col lg="6" md="6" sm="12" class="mb-3 mb-md-0">
                <b-input-group>
                  <b-input-group-prepend>
                    <span class="input-group-text bg-white">
                      <b-icon icon="search"></b-icon>
                    </span>
                  </b-input-group-prepend>
                  <b-form-input 
                    v-model="searchText" 
                    placeholder="搜索原文或译文..." 
                    @input="filterItems"
                  ></b-form-input>
                </b-input-group>
              </b-col>
              <b-col lg="6" md="6" sm="12">
                <b-input-group>
                  <b-input-group-prepend>
                    <span class="input-group-text bg-white">
                      <b-icon icon="funnel"></b-icon>
                    </span>
                  </b-input-group-prepend>
                  <b-form-select 
                    v-model="statusFilter" 
                    :options="statusOptions" 
                    @change="filterItems"
                  ></b-form-select>
                </b-input-group>
              </b-col>
            </b-row>
            
            <!-- Action buttons and filter info -->
            <div class="d-flex flex-wrap justify-content-between align-items-center">
              <div class="action-buttons mb-2 mb-md-0">
                <b-button 
                  variant="primary" 
                  class="action-btn save-btn mr-2"
                  @click="saveTranslation"
                >
                  <b-icon icon="save" class="mr-2"></b-icon>
                  保存翻译进度
                </b-button>
                <b-button 
                  variant="success" 
                  class="action-btn download-btn" 
                  :disabled="!isTranslationComplete" 
                  @click="downloadTranslatedFile"
                >
                  <b-icon icon="download" class="mr-2"></b-icon>
                  下载翻译文件
                </b-button>
              </div>
              <div class="filter-info text-muted">
                <span v-if="filteredItems.length !== originalSegments.length">
                  <b-icon icon="filter" class="mr-1"></b-icon>
                  显示 {{ filteredItems.length }} / {{ originalSegments.length }} 个段落
                </span>
              </div>
            </div>
          </b-card-body>
        </b-card>
        
        <!-- Empty state for when there are no matching items -->
        <div v-if="filteredItems.length === 0" class="text-center py-5 empty-state mb-4">
          <b-icon icon="search" font-scale="4" class="text-muted mb-3"></b-icon>
          <h4 class="text-muted">没有匹配的段落</h4>
          <p class="text-muted">请尝试调整搜索条件或清除过滤器</p>
        </div>
        
        <!-- Translation items with side-by-side layout -->
        <transition-group name="fade" tag="div" class="translation-list">
          <div 
            v-for="index in filteredItems" 
            :key="index" 
            class="translation-item mb-4" 
            :class="{ 'completed': isSegmentCompleted(index) }"
          >
            <b-card no-body>
              <div class="translation-grid">
                <!-- Original text (left side) -->
                <div class="original-container">
                  <div class="original-header">原文</div>
                  <div class="original-text">
                    {{ originalSegments[index] }}
                  </div>
                </div>
                
                <!-- Translation (right side) -->
                <div class="translation-container">
                  <div class="translation-header">译文</div>
                  <div class="translation-text-container">
                    <b-form-textarea
                      v-model="translatedSegments[index]"
                      rows="5"
                      max-rows="10"
                      placeholder="在此输入翻译..."
                      @input="updateTranslation(index, $event)"
                      class="translation-textarea"
                    ></b-form-textarea>
                  </div>
                </div>
              </div>
              
              <!-- Footer with status and navigation -->
              <div class="item-footer">
                <span :class="isSegmentCompleted(index) ? 'status-completed' : 'status-pending'">
                  <b-icon :icon="isSegmentCompleted(index) ? 'check-circle-fill' : 'clock'" class="mr-1"></b-icon>
                  {{ isSegmentCompleted(index) ? '已完成' : '待翻译' }}
                </span>
                <span class="segment-counter">
                  <b-icon icon="files" class="mr-1"></b-icon>
                  段落 {{ index + 1 }} / {{ originalSegments.length }}
                </span>
              </div>
            </b-card>
          </div>
        </transition-group>
        
        <!-- Save button at the bottom -->
        <div class="d-flex justify-content-center py-4" v-if="filteredItems.length > 0">
          <b-button variant="primary" size="lg" class="save-btn-bottom" @click="saveTranslation">
            <b-icon icon="save" class="mr-2"></b-icon>
            保存翻译进度
          </b-button>
        </div>
      </div>
      
      <!-- Error state -->
      <div v-else class="text-center py-5 error-state">
        <b-icon icon="exclamation-circle" font-scale="4" variant="danger" class="mb-3"></b-icon>
        <b-alert show variant="danger" class="d-inline-block">文件不存在或加载失败</b-alert>
        <div class="mt-3">
          <b-button :to="`/projects/${projectId}`" variant="primary" size="lg">
            <b-icon icon="arrow-left" class="mr-2"></b-icon>
            返回项目
          </b-button>
        </div>
      </div>
    </b-overlay>
  </div>
</template>

<script>
import { mapState, mapGetters } from 'vuex'

export default {
  name: 'Translation',
  props: {
    projectId: {
      type: String,
      required: true
    },
    fileId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      searchText: '',
      statusFilter: 'all',
      statusOptions: [
        { value: 'all', text: '所有状态' },
        { value: 'completed', text: '已完成' },
        { value: 'pending', text: '待翻译' }
      ],
      filteredItems: []
    }
  },
  computed: {
    ...mapState({
      currentProject: state => state.currentProject,
      currentFile: state => state.currentFile,
      originalSegments: state => state.originalSegments,
      translatedSegments: state => state.translatedSegments
    }),
    ...mapGetters([
      'getCompletionRate',
      'isTranslationComplete'
    ]),
    completionRate() {
      return this.getCompletionRate;
    },
    completedSegmentsCount() {
      return this.translatedSegments.filter(s => s.trim() !== '').length;
    }
  },
  created() {
    this.fetchProjectAndFile();
  },
  methods: {
    async fetchProjectAndFile() {
      try {
        await this.$store.dispatch('fetchProject', this.projectId);
        await this.$store.dispatch('fetchFile', {
          projectId: this.projectId,
          fileId: this.fileId
        });
        this.initFilteredItems();
      } catch (error) {
        this.$emit('show-error', error.response?.data?.error || '获取文件内容失败');
        this.$router.push(`/projects/${this.projectId}`);
      }
    },
    initFilteredItems() {
      this.filteredItems = Array.from({ length: this.originalSegments.length }, (_, i) => i);
      this.filterItems();
    },
    filterItems() {
      const searchText = this.searchText.toLowerCase();
      const statusFilter = this.statusFilter;
      
      this.filteredItems = Array.from({ length: this.originalSegments.length }, (_, i) => i).filter(index => {
        const originalText = this.originalSegments[index].toLowerCase();
        const translationText = this.translatedSegments[index].toLowerCase();
        const isCompleted = this.isSegmentCompleted(index);
        
        const matchesSearch = searchText === '' || 
                             originalText.includes(searchText) || 
                             translationText.includes(searchText);
        
        const matchesStatus = statusFilter === 'all' || 
                             (statusFilter === 'completed' && isCompleted) || 
                             (statusFilter === 'pending' && !isCompleted);
        
        return matchesSearch && matchesStatus;
      });
    },
    updateTranslation(index, text) {
      this.$store.dispatch('updateTranslatedSegment', { index, text });
    },
    isSegmentCompleted(index) {
      return this.translatedSegments[index]?.trim() !== '';
    },
    async saveTranslation() {
      try {
        await this.$store.dispatch('saveTranslation', {
          projectId: this.projectId,
          fileId: this.fileId
        });
        this.$emit('show-success', '翻译进度已保存');
      } catch (error) {
        this.$emit('show-error', error.response?.data?.error || '保存翻译进度失败');
      }
    },
    async downloadTranslatedFile() {
      try {
        await this.$store.dispatch('downloadTranslatedFile', {
          projectId: this.projectId,
          fileId: this.fileId
        });
        this.$emit('show-success', '文件下载成功');
      } catch (error) {
        this.$emit('show-error', error.response?.data?.error || '下载文件失败');
      }
    },
    formatDate(dateString) {
      return new Date(dateString).toLocaleString();
    }
  }
}
</script>

<style scoped>
/* Header styling */
.header-card {
  overflow: hidden;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
}

.file-header {
  display: flex;
  flex-direction: row;
}

.file-info {
  flex: 1;
}

.file-title {
  font-weight: 700;
  color: #333;
  font-size: 1.8rem;
  border-bottom: 3px solid #007bff;
  padding-bottom: 0.5rem;
  display: inline-block;
}

.file-meta {
  color: #6c757d;
  margin-top: 0.5rem;
}

.file-stats {
  min-width: 300px;
  background-color: #f8f9fa;
  border-left: 1px solid #dee2e6;
}

.stats-grid {
  display: flex;
  justify-content: space-between;
  text-align: center;
}

.stat-item {
  flex: 1;
  padding: 0 10px;
}

.stat-icon {
  color: #007bff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  color: #6c757d;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
}

/* Controls card styling */
.controls-card {
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
}

.action-btn {
  min-width: 140px;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.save-btn-bottom {
  min-width: 180px;
  padding: 0.75rem 1.5rem;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.save-btn-bottom:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
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

/* Translation items styling */
.translation-item {
  transition: all 0.3s ease;
  border-left: 5px solid #e9ecef;
  border-radius: 0.25rem;
  overflow: hidden;
}

.translation-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
}

.translation-item.completed {
  border-left-color: #28a745;
}

/* Side-by-side layout */
.translation-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-bottom: 1px solid #dee2e6;
}

.original-container, .translation-container {
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.original-container {
  border-right: 1px solid #dee2e6;
}

.original-header, .translation-header {
  padding: 10px 15px;
  font-weight: 600;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  color: #495057;
}

.original-text {
  padding: 15px;
  background-color: #f8f9fa;
  height: 100%;
  min-height: 150px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 1rem;
  line-height: 1.5;
  overflow-y: auto;
}

.translation-text-container {
  padding: 15px;
  height: 100%;
}

.translation-textarea {
  border: none;
  height: 100%;
  min-height: 150px;
  background-color: #fff;
  resize: none;
  font-size: 1rem;
  line-height: 1.5;
}

.translation-textarea:focus {
  box-shadow: none;
}

.item-footer {
  display: flex;
  justify-content: space-between;
  padding: 10px 15px;
  color: #6c757d;
  background-color: #fff;
}

.status-completed {
  color: #28a745;
  font-weight: 600;
}

.status-pending {
  color: #ffc107;
  font-weight: 600;
}

.segment-counter {
  font-size: 0.9rem;
}

/* Empty state styling */
.empty-state {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.05);
}

/* Error state styling */
.error-state {
  padding: 3rem 1rem;
  border-radius: 8px;
  background-color: #f8f9fa;
}

/* Animation */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}

/* Responsive adjustments */
@media (max-width: 991.98px) {
  .file-header {
    flex-direction: column;
  }
  
  .file-stats {
    border-left: none;
    border-top: 1px solid #dee2e6;
  }
  
  .action-buttons {
    margin-bottom: 1rem;
  }
}

@media (max-width: 767.98px) {
  .translation-grid {
    grid-template-columns: 1fr;
  }
  
  .original-container {
    border-right: none;
    border-bottom: 1px solid #dee2e6;
  }
  
  .action-buttons {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }
  
  .action-btn {
    margin-bottom: 0.5rem;
    width: 100%;
  }
  
  .save-btn {
    margin-right: 0 !important;
  }
}
</style>