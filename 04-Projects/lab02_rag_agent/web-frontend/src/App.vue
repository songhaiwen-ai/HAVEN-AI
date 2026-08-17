<template>
  <el-container class="h-screen w-screen bg-[#f8fafc] text-slate-800 font-sans overflow-hidden selection:bg-blue-100">
    
    <!-- =================================================================== -->
    <!-- 1. 左侧 Element Plus 侧边栏 (260px 宽，极简高级控制台) -->
    <!-- =================================================================== -->
    <el-aside :width="isSidebarCollapsed ? '64px' : '260px'" class="bg-[#f1f5f9] border-r border-slate-200/80 flex flex-col justify-between transition-all duration-300 relative z-20">
      
      <div class="p-4 space-y-4">
        
        <!-- Header Logo & 折叠按钮 -->
        <div class="flex items-center justify-between">
          <div v-if="!isSidebarCollapsed" class="flex items-center space-x-2">
            <div class="w-7 h-7 rounded-lg bg-blue-600 text-white font-bold text-xs flex items-center justify-center shadow-xs">
              H
            </div>
            <span class="font-bold text-slate-800 text-base tracking-tight">HavenResearch</span>
          </div>

          <el-button @click="isSidebarCollapsed = !isSidebarCollapsed" 
                     circle 
                     size="small" 
                     class="!bg-transparent hover:!bg-slate-200/60 !border-none text-slate-500">
            <el-icon :size="16"><Fold v-if="!isSidebarCollapsed" /><Expand v-else /></el-icon>
          </el-button>
        </div>

        <!-- 发起新对话按钮 -->
        <div class="pt-1">
          <el-button @click="startNewChat" 
                     type="primary" 
                     plain 
                     size="large" 
                     class="w-full !rounded-xl !h-11 !text-xs !font-semibold shadow-2xs hover:shadow-xs flex items-center justify-start px-3">
            <el-icon :size="16" class="mr-2 text-blue-600"><Plus /></el-icon>
            <span v-if="!isSidebarCollapsed">发起新对话</span>
          </el-button>
        </div>

        <!-- 历史对话 Header & 动态会话列表 -->
        <div v-if="!isSidebarCollapsed" class="pt-3 border-t border-slate-200/60">
          <div class="text-[11px] font-bold text-slate-400 px-2 mb-2 uppercase tracking-wider">最近历史对话</div>
          
          <el-scrollbar max-height="calc(100vh - 270px)">
            <div class="space-y-1 pr-1">
              <div v-for="session in historySessions" 
                   :key="session.session_id"
                   @click="loadSession(session.session_id)"
                   :class="[
                     'px-3 py-2.5 rounded-xl text-xs transition-all duration-200 flex items-center justify-between cursor-pointer group',
                     currentSessionId === session.session_id ? 'bg-white text-blue-600 font-semibold shadow-2xs' : 'text-slate-600 hover:bg-slate-200/60 hover:text-slate-900'
                   ]">
                <span class="truncate leading-normal">{{ session.title || '新对话' }}</span>
                <el-icon @click.stop="deleteSession(session.session_id)" class="opacity-0 group-hover:opacity-100 hover:text-rose-600 transition text-xs"><Delete /></el-icon>
              </div>

              <!-- 提示 -->
              <div v-if="historySessions.length === 0" class="text-xs text-slate-400 px-3 py-4 italic text-center">
                {{ currentUser ? '暂无历史对话记录' : '未登录 (登录后开启云端同步)' }}
              </div>
            </div>
          </el-scrollbar>
        </div>

      </div>

      <!-- 侧边栏左下方: 用户 Profile 胶囊 (逻辑彻底纠正：未登录显式提示) -->
      <div class="p-3 border-t border-slate-200/80 bg-[#f1f5f9] relative">
        <el-dropdown trigger="click" class="w-full" @command="handleUserMenuCommand">
          <div class="flex items-center justify-between w-full p-2.5 rounded-xl hover:bg-slate-200/70 cursor-pointer transition-all">
            <div class="flex items-center space-x-2.5 overflow-hidden">
              <el-avatar v-if="currentUser" :size="32" class="!bg-blue-600 !text-white !font-bold !text-xs flex-shrink-0 shadow-2xs">
                {{ currentUser.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <el-avatar v-else :size="32" class="!bg-slate-400 !text-white flex-shrink-0 shadow-2xs">
                <el-icon :size="16"><User /></el-icon>
              </el-avatar>

              <div v-if="!isSidebarCollapsed" class="overflow-hidden text-left">
                <div class="text-xs font-semibold text-slate-800 truncate">
                  {{ currentUser ? currentUser.username : '未登录' }}
                </div>
                <div class="text-[11px] text-slate-400 font-medium">
                  {{ currentUser ? '已验证用户' : '点击登录/注册' }}
                </div>
              </div>
            </div>
            <el-icon v-if="!isSidebarCollapsed" class="text-slate-400 text-xs"><Setting /></el-icon>
          </div>

          <template #dropdown>
            <el-dropdown-menu class="!rounded-xl !p-1.5 !w-44 shadow-xl">
              <template v-if="currentUser">
                <div class="px-3 py-2 border-b border-slate-100 mb-1">
                  <div class="font-bold text-xs text-slate-800">{{ currentUser.username }}</div>
                  <div class="text-[10px] text-slate-400">已登录账号</div>
                </div>
                <el-dropdown-item command="logout" class="!text-rose-600 !font-semibold !rounded-lg">
                  <el-icon class="mr-1.5"><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </template>

              <template v-else>
                <el-dropdown-item command="login" class="!text-blue-600 !font-semibold !rounded-lg">
                  <el-icon class="mr-1.5"><User /></el-icon>
                  账号登录
                </el-dropdown-item>
                <el-dropdown-item command="register" class="!text-slate-700 !font-semibold !rounded-lg">
                  <el-icon class="mr-1.5"><Plus /></el-icon>
                  注册新账号
                </el-dropdown-item>
              </template>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

    </el-aside>

    <!-- =================================================================== -->
    <!-- 2. 右侧主视图区 (真正垂直水平精确居中 + 舒适现代视觉) -->
    <!-- =================================================================== -->
    <el-main class="flex-1 flex flex-col justify-between relative !bg-white !p-0 overflow-y-auto">
      
      <!-- 顶部轻量 Header (数据源模式选择) -->
      <div class="h-16 px-8 flex items-center justify-between border-b border-slate-100 bg-white/80 backdrop-blur-sm sticky top-0 z-20">
        <div class="flex items-center space-x-2 text-xs font-semibold text-slate-500">
          <span>HavenResearch Agent Pro 1.5</span>
        </div>
        <div class="flex items-center space-x-3">
          <span class="text-xs text-slate-400 font-medium">知识库数据源:</span>
          <el-select v-model="reportSource" size="small" class="!w-60">
            <el-option value="hybrid" label="🌐 混合双引擎 (Web + Qdrant 知识库)" />
            <el-option value="local" label="💾 纯本地知识库 (107本电子书)" />
            <el-option value="web" label="🌐 纯全网实时检索 (Tavily AI)" />
          </el-select>
        </div>
      </div>

      <!-- 中央 Hero 欢迎大字 (逻辑彻底纠正：未登录不盲显姓名) -->
      <div v-if="messages.length === 0" class="flex-1 flex flex-col items-center justify-center my-auto text-center px-4 -mt-16">
        <div class="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 font-bold text-xl flex items-center justify-center shadow-xs mb-6 mx-auto">
          ✦
        </div>
        <h1 class="text-3xl md:text-4xl font-semibold text-slate-900 mb-3 tracking-tight">
          {{ currentUser ? `欢迎回来，${currentUser.username}` : 'HavenResearch，需要我做点什么？' }}
        </h1>
        <p class="text-sm text-slate-400 max-w-md font-normal">
          深度技术问答、AI 架构设计、行业研报分析与长文档全自动合成
        </p>
      </div>

      <!-- 对话消息列表 -->
      <div v-else class="flex-1 max-w-3xl w-full mx-auto px-6 py-8 space-y-8 pb-36">
        <div v-for="(msg, idx) in messages" :key="idx" class="space-y-4">
          
          <!-- 用户提问 -->
          <div v-if="msg.role === 'user'" class="flex justify-end">
            <div class="bg-blue-600 text-white rounded-2xl px-5 py-3.5 max-w-xl text-sm leading-relaxed font-medium shadow-2xs">
              {{ msg.content }}
            </div>
          </div>

          <!-- Agent 回答 -->
          <div v-else class="flex items-start space-x-4">
            <div class="w-8 h-8 rounded-xl bg-blue-600 text-white font-bold text-xs flex items-center justify-center shadow-xs flex-shrink-0 mt-1">
              H
            </div>
            
            <div class="flex-1 space-y-4">
              <div v-if="msg.agent_persona" class="inline-flex items-center space-x-2 bg-slate-100 border border-slate-200/80 px-3 py-1 rounded-full text-xs text-slate-700 font-semibold">
                <span>专家角色:</span>
                <span class="text-slate-900 font-bold">{{ msg.agent_persona }}</span>
              </div>

              <div v-if="msg.steps && msg.steps.length > 0" class="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs space-y-2 font-mono">
                <div class="font-bold text-slate-700 flex items-center justify-between border-b border-slate-200 pb-2 mb-1">
                  <span>Agent 自主推理步骤 ({{ msg.steps.length }})</span>
                  <span v-if="msg.isStreaming" class="text-blue-600 animate-pulse font-sans">● 推理中...</span>
                </div>
                <div v-for="(step, sIdx) in msg.steps" :key="sIdx" class="text-slate-600 flex items-center space-x-2">
                  <span class="text-blue-600 font-bold">›</span>
                  <span>{{ step }}</span>
                </div>
              </div>

              <!-- 报告长文档渲染 (清晰可读 15px) -->
              <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm prose prose-slate max-w-none text-sm leading-relaxed text-slate-800"
                   v-html="renderMarkdown(msg.content)">
              </div>

              <div v-if="msg.cost_summary" class="flex flex-wrap items-center gap-3 text-xs text-slate-500 pt-1">
                <el-tag type="info" round size="small">💰 Token 消耗: {{ msg.cost_summary.total_tokens }} (${{ msg.cost_summary.total_cost_usd }})</el-tag>
                <el-tag v-if="msg.sources" type="success" round size="small">📚 引用精排干货: {{ msg.sources.length }} 条</el-tag>
              </div>
            </div>
          </div>

        </div>
      </div>

      <!-- 3. 极简浮动 Pill 输入框 -->
      <div class="fixed bottom-8 left-1/2 -translate-x-1/2 max-w-2xl w-full px-4 z-20">
        <div class="bg-white border border-slate-200 rounded-2xl p-2 shadow-xl shadow-slate-200/50 flex items-center space-x-2 transition-all focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-100">
          
          <input v-model="inputQuery" 
                 @keydown.enter="sendQuery" 
                 type="text" 
                 placeholder="输入技术课题发起深度研究..." 
                 class="flex-1 bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none px-3 font-medium" />

          <el-button @click="sendQuery" 
                     :disabled="isGenerating" 
                     type="primary" 
                     size="default" 
                     class="!rounded-xl !px-5 !font-semibold shadow-2xs">
            <el-icon v-if="isGenerating" class="animate-spin mr-1"><Loading /></el-icon>
            <span>发送</span>
          </el-button>
        </div>
      </div>

    </el-main>

    <!-- 4. 现代化 AuthForm 登录 / 注册 Modal 弹窗 -->
    <el-dialog v-model="showAuthModal" width="440px" :show-close="false" custom-class="!rounded-3xl">
      <AuthForm 
        :closeable="true" 
        :default-register="isRegisterTab" 
        @close="showAuthModal = false"
        @submit="handleAuthSubmit"
      />
    </el-dialog>

  </el-container>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { authApi, chatApi } from './api'
import AuthForm from './components/AuthForm.vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'App',
  components: {
    AuthForm
  },
  setup() {
    const inputQuery = ref("")
    const reportSource = ref("hybrid")
    const messages = ref([])
    const isGenerating = ref(false)
    const isSidebarCollapsed = ref(false)

    // Auth & Session States
    const showAuthModal = ref(false)
    const isRegisterTab = ref(false)
    const currentUser = ref(null)
    const currentSessionId = ref("")
    const historySessions = ref([])
    const token = ref(localStorage.getItem("haven_token") || "")

    onMounted(async () => {
      if (token.value) {
        try {
          const res = await authApi.getMe()
          currentUser.value = res.data
          await fetchSessions()
        } catch (e) {
          logout()
        }
      }
    })

    async function fetchSessions() {
      try {
        const res = await chatApi.getSessions()
        historySessions.value = res.data
      } catch (e) {
        historySessions.value = []
      }
    }

    function openAuthModal(registerMode = false) {
      isRegisterTab.value = registerMode
      showAuthModal.value = true
    }

    function handleUserMenuCommand(command) {
      if (command === 'logout') logout()
      else if (command === 'login') openAuthModal(false)
      else if (command === 'register') openAuthModal(true)
    }

    async function handleAuthSubmit({ isRegister, username, password }) {
      try {
        const fn = isRegister ? authApi.register : authApi.login
        const res = await fn(username, password)
        token.value = res.data.token
        currentUser.value = res.data.user
        localStorage.setItem("haven_token", res.data.token)
        showAuthModal.value = false
        ElMessage.success(isRegister ? "注册并登录成功！" : "登录成功！")
        await fetchSessions()
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || "认证失败，请检查账号或密码")
      }
    }

    async function logout() {
      try {
        await authApi.logout()
      } catch (e) {}
      token.value = ""
      currentUser.value = null
      historySessions.value = []
      messages.value = []
      localStorage.removeItem("haven_token")
      ElMessage.info("已退出登录")
    }

    function startNewChat() {
      messages.value = []
      currentSessionId.value = "session_" + Date.now()
    }

    async function loadSession(sessionId) {
      currentSessionId.value = sessionId
      try {
        const res = await chatApi.getMessages(sessionId)
        messages.value = res.data.map(m => ({
          role: m.role,
          content: m.content,
          sources: m.sources
        }))
        scrollToBottom()
      } catch (e) {
        messages.value = []
      }
    }

    async function deleteSession(sessionId) {
      try {
        await chatApi.deleteSession(sessionId)
        ElMessage.success("会话已成功删除")
        await fetchSessions()
        if (currentSessionId.value === sessionId) {
          startNewChat()
        }
      } catch (e) {}
    }

    async function sendQuery() {
      const query = inputQuery.value.trim()
      if (!query || isGenerating.value) return

      messages.value.push({ role: "user", content: query })
      inputQuery.value = ""
      isGenerating.value = true

      const assistantMsg = {
        role: "assistant",
        agent_persona: "",
        steps: [],
        content: "",
        isStreaming: true
      }
      messages.value.push(assistantMsg)
      scrollToBottom()

      const sessionId = currentSessionId.value || ("session_" + Date.now())
      const url = `/api/v1/chat/stream?session_id=${sessionId}&query=${encodeURIComponent(query)}&report_source=${reportSource.value}`
      const eventSource = new EventSource(url)

      eventSource.onmessage = function(e) {
        try {
          const data = JSON.parse(e.data)
          if (data.type === "step") {
            assistantMsg.steps.push(data.message)
          } else if (data.type === "persona") {
            assistantMsg.agent_persona = data.persona
          } else if (data.type === "chunk") {
            assistantMsg.content += data.content
          } else if (data.type === "complete") {
            assistantMsg.isStreaming = false
            assistantMsg.cost_summary = data.cost_summary
            assistantMsg.sources = data.sources
            isGenerating.value = false
            fetchSessions()
            eventSource.close()
          }
          scrollToBottom()
        } catch (err) {}
      }

      eventSource.onerror = function() {
        assistantMsg.isStreaming = false
        isGenerating.value = false
        eventSource.close()
      }
    }

    function renderMarkdown(content) {
      if (!content) return "<span class='typing-cursor text-blue-600 font-semibold'>正在与 DeepSeek API 深度通信...</span>"
      return marked.parse(content)
    }

    function scrollToBottom() {
      nextTick(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
      })
    }

    return {
      inputQuery,
      reportSource,
      messages,
      isGenerating,
      isSidebarCollapsed,
      showAuthModal,
      isRegisterTab,
      currentUser,
      currentSessionId,
      historySessions,
      openAuthModal,
      handleUserMenuCommand,
      handleAuthSubmit,
      logout,
      startNewChat,
      loadSession,
      deleteSession,
      sendQuery,
      renderMarkdown
    }
  }
}
</script>

<style>
.typing-cursor::after {
  content: '▋';
  animation: blink 1s infinite;
  color: #2563eb;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.prose h1, .prose h2, .prose h3 {
  color: #1e293b;
  font-weight: 700;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}
.prose table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  font-size: 0.875rem;
}
.prose th, .prose td {
  border: 1px solid #e2e8f0;
  padding: 0.75rem 1rem;
}
.prose th {
  background-color: #f8fafc;
  color: #0f172a;
}
</style>
