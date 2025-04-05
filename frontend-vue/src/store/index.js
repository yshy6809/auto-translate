import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    projects: [],
    currentProject: null,
    currentFile: null,
    originalSegments: [],
    translatedSegments: [],
    loading: false
  },
  mutations: {
    SET_PROJECTS(state, projects) {
      state.projects = projects
    },
    SET_CURRENT_PROJECT(state, project) {
      state.currentProject = project
    },
    SET_CURRENT_FILE(state, file) {
      state.currentFile = file;
      if (file) {
        state.originalSegments = file.originalSegments;
        state.translatedSegments = file.translatedSegments;
      } else {
        state.originalSegments = [];
        state.translatedSegments = [];
      }
    },
    UPDATE_TRANSLATED_SEGMENT(state, { index, text }) {
      Vue.set(state.translatedSegments, index, text);
    },
    SET_LOADING(state, loading) {
      state.loading = loading;
    }
  },
  actions: {
    // 项目相关操作
    async fetchProjects({ commit }) {
      commit('SET_LOADING', true);
      try {
        const response = await axios.get('/api/projects');
        commit('SET_PROJECTS', response.data);
        return response.data;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async createProject({ commit, dispatch }, { name, description }) {
      commit('SET_LOADING', true);
      try {
        const response = await axios.post('/api/projects', { name, description });
        await dispatch('fetchProjects');
        return response.data;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async fetchProject({ commit }, projectId) {
      commit('SET_LOADING', true);
      try {
        const response = await axios.get(`/api/projects/${projectId}`);
        commit('SET_CURRENT_PROJECT', response.data);
        return response.data;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async deleteProject({ commit, dispatch }, projectId) {
      commit('SET_LOADING', true);
      try {
        await axios.delete(`/api/projects/${projectId}`);
        commit('SET_CURRENT_PROJECT', null);
        await dispatch('fetchProjects');
      } finally {
        commit('SET_LOADING', false);
      }
    },

    // 文件相关操作
    async uploadFile({ commit, dispatch }, { projectId, formData }) {
      commit('SET_LOADING', true);
      try {
        const response = await axios.post(`/api/projects/${projectId}/files`, formData);
        await dispatch('fetchProject', projectId);
        return response.data;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async fetchFile({ commit }, { projectId, fileId }) {
      commit('SET_LOADING', true);
      try {
        const response = await axios.get(`/api/projects/${projectId}/files/${fileId}`);
        commit('SET_CURRENT_FILE', response.data);
        return response.data;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async deleteFile({ commit, dispatch, state }, { projectId, fileId }) {
      commit('SET_LOADING', true);
      try {
        await axios.delete(`/api/projects/${projectId}/files/${fileId}`);
        if (state.currentFile && state.currentFile.id === fileId) {
          commit('SET_CURRENT_FILE', null);
        }
        await dispatch('fetchProject', projectId);
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async saveTranslation({ commit, state, dispatch }, { projectId, fileId }) {
      commit('SET_LOADING', true);
      try {
        const response = await axios.put(`/api/projects/${projectId}/files/${fileId}`, {
          translatedSegments: state.translatedSegments
        });
        await dispatch('fetchProject', projectId);
        return response.data;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async downloadTranslatedFile({ commit }, { projectId, fileId }) {
      commit('SET_LOADING', true);
      try {
        const response = await axios.get(`/api/projects/${projectId}/files/${fileId}/download`, {
          responseType: 'blob'
        });
        
        // 从响应头中获取文件名
        const contentDisposition = response.headers['content-disposition'];
        let filename = 'translated.txt';
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename="(.+)"/);
          if (filenameMatch.length === 2) {
            filename = filenameMatch[1];
          }
        }
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        return true;
      } catch (error) {
        console.error("Download file error:", error.response || error); // Log detailed error
        // Re-throw the error so the component's catch block can handle UI feedback
        throw error; 
      } finally {
        commit('SET_LOADING', false);
      }
    },
    updateTranslatedSegment({ commit }, { index, text }) {
      commit('UPDATE_TRANSLATED_SEGMENT', { index, text });
    }
  },
  getters: {
    projectsCount: state => state.projects.length,
    getProjectById: state => id => state.projects.find(project => project.id === id),
    getCompletionRate: state => {
      if (!state.originalSegments.length) return 0;
      const completed = state.translatedSegments.filter(s => s.trim() !== '').length;
      return Math.round((completed / state.originalSegments.length) * 100);
    },
    isTranslationComplete: state => {
      if (!state.originalSegments.length) return false;
      return state.translatedSegments.every(s => s.trim() !== '');
    }
  }
})
