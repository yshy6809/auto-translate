<template>
  <div class="translation">
    <b-overlay :show="$store.state.loading" rounded>
      <div v-if="currentFile && currentProject">
        <b-breadcrumb>
          <b-breadcrumb-item to="/projects">项目列表</b-breadcrumb-item>
          <b-breadcrumb-item :to="`/projects/${projectId}`">{{ currentProject.name }}</b-breadcrumb-item>
          <b-breadcrumb-item active>{{ currentFile.fileName }}</b-breadcrumb-item>
        </b-breadcrumb>
        
        <b-row class="mb-4">
          <b-col md="8">
            <h1>翻译文件：{{ currentFile.fileName }}</h1>
            <p>上传于: {{ formatDate(currentFile.uploadDate) }}</p>
          </b-col>
          <b-col md="4">
            <b-card>
              <b-row>
                <b-col cols="4" class="text-center">
                  <h5>总段落数</h5>
                  <div class="stat-number">{{ originalSegments.length }}</div>
                </b-col>
                <b-col cols="4" class="text-center">
                  <h5>已完成</h5>
                  <div class="stat-number">{{ completedSegmentsCount }}</div>
                </b-col>
                <b-col cols="4" class="text-center">
                  <h5>完成率</h5>
                  <div class="stat-number">{{ completionRate }}%</div>
                </b-col>
              </b-row>
              <b-progress 
                :value="completionRate" 
                :max="100" 
                class="mt-3"
                show-value
              ></b-progress>
            </b-card>
          </b-col>
        </b-row>
        
        <b-card class="mb-4">
          <b-row>
            <b-col sm="6">
              <b-form-group label="搜索内容">
                <b-form-input 
                  v-model="searchText" 
                  placeholder="搜索原文或译文..." 
                  @input="filterItems"
                ></b-form-input>
              </b-form-group>
            </b-col>
            <b-col sm="6">
              <b-form-group label="状态过滤">
                <b-form-select 
                  v-model="statusFilter" 
                  :options="statusOptions" 
                  @change="filterItems"
                ></b-form-select>
              </b-form-group>
            </b-col>
          </b-row>
          
          <div class="d-flex justify-content-between align-items-center mb-3">
            <div>
              <b-button variant="primary" @click="saveTranslation">保存翻译进度</b-button>
              <b-button 
                variant="success" 
                class="ml-2" 
                :disabled="!isTranslationComplete" 
                @click="downloadTranslatedFile"
              >
                下载翻译文件
              </b-button>
            </div>
            <div>
              <span v-if="filteredItems.length !== originalSegments.length">
                显示 {{ filteredItems.length }} / {{ originalSegments.length }} 个段落
              </span>
            </div>
          </div>
        </b-card>
        
        <div v-for="index in filteredItems" :key="index" class="translation-item mb-4" :class="{ 'completed': isSegmentCompleted(index) }">
          <b-card>
            <div class="original-text">{{ originalSegments[index] }}</div>
            <b-form-group label="翻译:">
              <b-form-textarea
                v-model="translatedSegments[index]"
                rows="3"
                max-rows="8"
                placeholder="在此输入翻译..."
                @input="updateTranslation(index, $event)"
              ></b-form-textarea>
            </b-form-group>
            <div class="d-flex justify-content-between">
              <span :class="isSegmentCompleted(index) ? 'status-completed' : 'status-pending'">
                {{ isSegmentCompleted(index) ? '已完成' : '待翻译' }}
              </span>
              <span>段落 {{ index + 1 }} / {{ originalSegments.length }}</span>
            </div>
          </b-card>
        </div>
        
        <div v-if="filteredItems.length === 0" class="text-center py-4">
          <b-alert show variant="info">没有匹配的段落</b-alert>
        </div>
        
        <div class="d-flex justify-content-center mt-4 mb-4">
          <b-button variant="primary" @click="saveTranslation">保存翻译进度</b-button>
        </div>
      </div>
      <div v-else>
        <b-alert show variant="danger">文件不存在或加载失败</b-alert>
        <b-button :to="`/projects/${projectId}`" variant="primary">返回项目</b-button>
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
.stat-number {
  font-size: 1.5rem;
  font-weight: bold;
}

.original-text {
  margin-bottom: 10px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 5px;
  font-size: 1.1rem;
}

.translation-item {
  transition: all 0.3s ease;
}

.translation-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.translation-item.completed {
  border-left: 5px solid #28a745;
}
</style>