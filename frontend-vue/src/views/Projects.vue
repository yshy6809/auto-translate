<template>
  <div class="projects">
    <h1 class="page-title mb-4">项目管理</h1>
    
    <b-overlay :show="$store.state.loading" rounded>
      <!-- Improved Project Creation Card -->
      <b-card no-body class="mb-4 create-project-card">
        <b-card-header class="bg-primary text-white">
          <h3 class="mb-0">创建新项目</h3>
        </b-card-header>
        <b-card-body>
          <b-form @submit.prevent="createProject">
            <!-- Changed to vertical layout -->
            <b-form-group label="项目名称" label-for="project-name" class="mb-4">
              <b-form-input
                id="project-name"
                v-model="newProject.name"
                required
                placeholder="输入项目名称"
                class="form-control-lg"
              ></b-form-input>
            </b-form-group>
            
            <b-form-group label="项目描述" label-for="project-description" class="mb-4">
              <b-form-textarea
                id="project-description"
                v-model="newProject.description"
                placeholder="项目描述（可选）"
                rows="4"
                class="form-control-lg"
              ></b-form-textarea>
            </b-form-group>
            
            <div class="text-center mt-4">
              <b-button type="submit" variant="primary" size="lg" class="px-5 create-btn">
                <b-icon icon="plus-circle-fill" class="mr-2"></b-icon>
                创建项目
              </b-button>
            </div>
          </b-form>
        </b-card-body>
      </b-card>

      <!-- Project List Section with improved headers -->
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h2 class="section-title mb-0">项目列表</h2>
        <span class="text-muted">共 {{ projects.length }} 个项目</span>
      </div>
      
      <!-- Empty state with better styling -->
      <div v-if="!projects.length" class="text-center py-5 empty-state">
        <b-icon icon="folder" font-scale="4" class="text-muted mb-3"></b-icon>
        <h3 class="text-muted">暂无项目</h3>
        <p class="text-muted">点击上方"创建项目"按钮开始您的第一个翻译项目</p>
      </div>
      
      <!-- Improved project cards with better layout -->
      <transition-group name="project-list" tag="div" class="project-list">
        <b-card 
          v-for="project in projects" 
          :key="project.id" 
          class="mb-4 project-card"
          :class="{'high-completion': project.completionRate > 75, 
                   'medium-completion': project.completionRate >= 30 && project.completionRate <= 75,
                   'low-completion': project.completionRate < 30}"
        >
          <b-row align-v="center">
            <b-col lg="8" md="7" sm="12">
              <div class="d-flex align-items-center mb-2">
                <h3 class="mb-0">{{ project.name }}</h3>
                <b-badge 
                  v-if="project.completionRate === 100" 
                  variant="success" 
                  class="ml-2"
                >
                  已完成
                </b-badge>
              </div>
              
              <p class="text-muted small mb-2">
                <b-icon icon="calendar3" class="mr-1"></b-icon>
                创建于: {{ formatDate(project.creationDate) }} | 
                <b-icon icon="clock-history" class="mr-1"></b-icon>
                最后更新: {{ formatDate(project.lastModified) }}
              </p>
              
              <p class="project-description mb-3">
                {{ project.description || '无描述' }}
              </p>
              
              <div class="d-flex align-items-center mb-2">
                <span class="mr-2 completion-label">完成率:</span>
                <b-progress
                  :value="project.completionRate"
                  :max="100"
                  class="flex-grow-1 progress-bar-custom"
                  height="10px"
                >
                  <b-progress-bar :value="project.completionRate">
                    <span class="progress-label">{{ project.completionRate }}%</span>
                  </b-progress-bar>
                </b-progress>
              </div>
              
              <div class="file-count">
                <b-icon icon="file-text" class="mr-1"></b-icon>
                文件数: <b>{{ project.files.length }}</b>
              </div>
            </b-col>
            
            <b-col lg="4" md="5" sm="12" class="d-flex flex-column justify-content-center align-items-md-end align-items-sm-start mt-sm-3 mt-md-0">
              <div class="action-buttons">
                <b-button 
                  variant="primary" 
                  class="action-btn view-btn mr-3" 
                  @click="viewProject(project.id)"
                >
                  <b-icon icon="eye-fill" class="mr-2"></b-icon>
                  查看
                </b-button>
                <b-button 
                  variant="outline-danger" 
                  class="action-btn delete-btn" 
                  @click="confirmDeleteProject(project.id, project.name)"
                >
                  <b-icon icon="trash-fill" class="mr-2"></b-icon>
                  删除
                </b-button>
              </div>
            </b-col>
          </b-row>
        </b-card>
      </transition-group>
    </b-overlay>
    
    <!-- Improved Delete Confirmation Modal -->
    <b-modal 
      id="delete-project-modal" 
      centered
      title="确认删除" 
      header-bg-variant="danger"
      header-text-variant="white"
      ok-title="删除" 
      ok-variant="danger"
      cancel-title="取消"
      @ok="deleteProject"
    >
      <div class="d-flex align-items-center">
        <b-icon icon="exclamation-triangle-fill" variant="danger" font-scale="2" class="mr-3"></b-icon>
        <p class="mb-0">确定要删除项目"<strong>{{ projectToDelete.name }}</strong>"吗？<br>项目中的所有文件也将被删除，此操作<strong>无法撤销</strong>。</p>
      </div>
    </b-modal>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'Projects',
  data() {
    return {
      newProject: {
        name: '',
        description: ''
      },
      projectToDelete: {
        id: null,
        name: ''
      }
    }
  },
  computed: {
    ...mapState({
      projects: state => state.projects
    })
  },
  created() {
    this.fetchProjects();
  },
  methods: {
    async fetchProjects() {
      try {
        await this.$store.dispatch('fetchProjects');
      } catch (error) {
        this.$emit('show-error', error.response?.data?.error || '获取项目列表失败');
      }
    },
    async createProject() {
      try {
        const result = await this.$store.dispatch('createProject', {
          name: this.newProject.name,
          description: this.newProject.description
        });
        this.$emit('show-success', '项目创建成功');
        
        this.newProject.name = '';
        this.newProject.description = '';
        
        this.$router.push(`/projects/${result.id}`);
      } catch (error) {
        this.$emit('show-error', error.response?.data?.error || '创建项目失败');
      }
    },
    viewProject(projectId) {
      this.$router.push(`/projects/${projectId}`);
    },
    confirmDeleteProject(id, name) {
      this.projectToDelete = { id, name };
      this.$bvModal.show('delete-project-modal');
    },
    async deleteProject() {
      try {
        await this.$store.dispatch('deleteProject', this.projectToDelete.id);
        this.$emit('show-success', '项目删除成功');
      } catch (error) {
        this.$emit('show-error', error.response?.data?.error || '删除项目失败');
      }
    },
    formatDate(dateString) {
      return new Date(dateString).toLocaleString();
    }
  }
}
</script>

<style scoped>
.page-title {
  font-weight: 700;
  color: #333;
  margin-bottom: 1.5rem;
  border-bottom: 3px solid #007bff;
  padding-bottom: 0.5rem;
  display: inline-block;
}

.section-title {
  font-weight: 600;
  color: #495057;
}

.create-project-card {
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.create-project-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.create-btn {
  transition: all 0.2s ease;
  box-shadow: 0 2px 6px rgba(0, 123, 255, 0.3);
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.4);
}

.project-card {
  border-left: 5px solid #e9ecef;
  transition: all 0.3s ease;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.project-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
}

.project-card.high-completion {
  border-left-color: #28a745;
}

.project-card.medium-completion {
  border-left-color: #ffc107;
}

.project-card.low-completion {
  border-left-color: #dc3545;
}

.project-description {
  font-size: 1rem;
  color: #6c757d;
  min-height: 1.5rem;
}

.completion-label {
  font-weight: 600;
  min-width: 60px;
}

.progress-bar-custom {
  height: 12px !important;
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

.file-count {
  font-size: 0.9rem;
  color: #6c757d;
}

.action-buttons {
  display: flex;
  align-items: center;
}

.action-btn {
  min-width: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.view-btn:hover {
  background-color: #0069d9;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
}

.delete-btn:hover {
  background-color: #dc3545;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(220, 53, 69, 0.3);
}

.empty-state {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.05);
}

/* Transition animations for the project list */
.project-list-enter-active, .project-list-leave-active {
  transition: all 0.5s;
}

.project-list-enter, .project-list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}

/* Responsive adjustments */
@media (max-width: 767.98px) {
  .action-buttons {
    margin-top: 1rem;
    justify-content: flex-start;
  }
}
</style>