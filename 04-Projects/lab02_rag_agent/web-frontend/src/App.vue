<template>
  <el-container class="h-screen w-screen bg-[#f8fafc] text-slate-800 font-sans overflow-hidden selection:bg-blue-100">
    
    <!-- =================================================================== -->
    <!-- 1. 左侧 Element Plus 侧边栏 (260px 宽) -->
    <!-- =================================================================== -->
    <el-aside :width="isSidebarCollapsed ? '64px' : '260px'" class="bg-[#f1f5f9] border-r border-slate-200/80 flex flex-col justify-between transition-all duration-300 relative z-20">
      
      <div class="p-4 space-y-4">
        
        <!-- Header Logo & 折叠按钮 -->
        <div class="flex items-center justify-between">
          <div v-if="!isSidebarCollapsed" class="flex items-center space-x-2">
            <div class="w-7 h-7 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold text-xs flex items-center justify-center shadow-xs">
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

      <!-- 侧边栏左下方: 用户 Profile 胶囊 -->
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
                <el-dropdown-item command="login" class="!rounded-lg !font-medium">
                  <el-icon class="mr-1.5"><User /></el-icon>
                  账号登录
                </el-dropdown-item>
                <el-dropdown-item command="register" class="!rounded-lg !font-medium">
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
    <!-- 2. 主区域 (支持双栏 / Artifact Canvas 面板) -->
    <!-- =================================================================== -->
    <el-container class="flex-1 flex flex-row overflow-hidden relative">
      
      <!-- 2.1 左/中: 对话视窗 -->
      <div class="flex-1 flex flex-col h-full bg-[#f8fafc] relative overflow-hidden">
        
        <!-- 顶部功能栏 -->
        <header class="h-14 border-b border-slate-200/70 bg-white/80 backdrop-blur-md px-6 flex items-center justify-between z-10">
          <div class="flex items-center space-x-3">
            <span class="font-bold text-slate-800 text-sm tracking-tight">HavenResearch</span>
          </div>

          <div class="flex items-center space-x-3">
            <!-- 切换 Artifacts 右侧画板按键 -->
            <el-button v-if="artifact.content" 
                       @click="showArtifactCanvas = !showArtifactCanvas"
                       size="small" 
                       :type="showArtifactCanvas ? 'primary' : 'default'" 
                       class="!rounded-lg !text-xs">
              <el-icon class="mr-1"><Document /></el-icon>
              {{ showArtifactCanvas ? '隐藏文档画板' : '查看文档画板 (' + artifact.version + ')' }}
            </el-button>
          </div>
        </header>

        <!-- 对话消息列表 (pb-64 预留 256px 足够底距，监听 @scroll 避让用户手动上滑) -->
        <el-main @scroll="handleScroll" class="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 max-w-4xl mx-auto w-full pb-64" id="messages-container">
          
          <!-- 欢迎/空白页 -->
          <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-center my-auto py-16 space-y-6">
            <div class="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-sky-400 text-white flex items-center justify-center text-2xl font-bold shadow-lg shadow-blue-500/20">
              ✦
            </div>
            <div class="space-y-2">
              <h2 class="text-xl font-bold text-slate-800 tracking-tight">智能研究 & 协同文档编辑助手</h2>
              <p class="text-xs text-slate-500 max-w-md">支持多轮长对话背景记忆、智能意图分流与长文档 Artifacts 画布协同修改。</p>
            </div>

            <!-- 快捷启动 Prompt 胶囊 -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-xl text-left pt-4">
              <div @click="quickStart('我们团队是做智慧农业 SaaS 的，主要面向水稻种植')" class="p-3.5 bg-white border border-slate-200/80 hover:border-blue-400 rounded-2xl cursor-pointer shadow-2xs hover:shadow-xs transition-all">
                <div class="font-semibold text-xs text-slate-800">🌱 1. 补充项目背景</div>
                <div class="text-[11px] text-slate-400 mt-1">告知助手项目背景，暂不生成文档</div>
              </div>
              <div @click="quickStart('结合上述背景，帮我设计一份系统架构方案文档')" class="p-3.5 bg-white border border-slate-200/80 hover:border-blue-400 rounded-2xl cursor-pointer shadow-2xs hover:shadow-xs transition-all">
                <div class="font-semibold text-xs text-slate-800">📝 2. 生成全量架构文档</div>
                <div class="text-[11px] text-slate-400 mt-1">基于已知背景，创建 v1.0 文档画布</div>
              </div>
            </div>
          </div>

          <!-- 对话消息渲染 -->
          <div v-for="(msg, idx) in messages" :key="idx" :id="'msg-' + idx" class="space-y-3">
            
            <!-- 用户消息 -->
            <div v-if="msg.role === 'user'" class="flex justify-end">
              <div class="bg-blue-600 text-white px-4 py-3 rounded-2xl rounded-tr-xs max-w-2xl text-xs font-normal shadow-xs leading-relaxed">
                {{ msg.content }}
              </div>
            </div>

            <!-- 助手消息 -->
            <div v-else class="flex items-start space-x-3">
              <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center text-xs font-bold shadow-xs flex-shrink-0 mt-0.5">
                ✦
              </div>

              <div class="flex-1 bg-white border border-slate-200/80 rounded-2xl p-4 md:p-5 shadow-2xs text-xs space-y-3 overflow-hidden">
                
                <!-- 意图与 Agent 步骤标识 -->
                <div v-if="msg.agent_persona || msg.intent" class="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
                  <div class="text-[11px] font-semibold text-blue-600 flex items-center space-x-1.5">
                    <span class="w-2 h-2 rounded-full bg-blue-600 animate-pulse"></span>
                    <span>{{ msg.agent_persona || 'Agent 已响应' }}</span>
                  </div>
                  <el-tag v-if="msg.intent" size="small" effect="plain" class="!rounded-md !text-[10px]">
                    {{ getShortIntentLabel(msg.intent) }}
                  </el-tag>
                </div>

                <!-- Markdown 内容 -->
                <div class="prose prose-slate max-w-none text-slate-700 leading-relaxed overflow-x-auto" v-html="renderMarkdown(msg.content)"></div>

                <!-- 资料来源 (Sources) -->
                <div v-if="msg.sources && msg.sources.length > 0" class="pt-3 border-t border-slate-100">
                  <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">参考引用的参考来源 ({{ msg.sources.length }})</div>
                  <div class="flex flex-wrap gap-2">
                    <a v-for="(src, sIdx) in msg.sources" 
                       :key="sIdx" 
                       :href="src.url" 
                       target="_blank" 
                       class="inline-flex items-center space-x-1 bg-slate-50 hover:bg-blue-50 border border-slate-200/80 hover:border-blue-300 text-slate-600 hover:text-blue-600 px-2.5 py-1 rounded-lg text-[11px] transition-all">
                      <span class="truncate max-w-xs">{{ src.title || src.url }}</span>
                      <el-icon class="text-[10px]"><TopRight /></el-icon>
                    </a>
                  </div>
                </div>

              </div>
            </div>

          </div>

        </el-main>

        <!-- 底部胶囊输入框 (Gemini 风格 Dock) -->
        <footer class="absolute bottom-6 left-0 right-0 max-w-3xl mx-auto px-4 z-30">
          <div class="bg-white/95 backdrop-blur-xl border border-slate-200/90 rounded-full p-2.5 shadow-2xl shadow-blue-500/10 flex items-center space-x-3 hover:border-blue-300 transition-all">
            <input 
              v-model="inputQuery" 
              @keydown.enter="sendQuery"
              type="text" 
              placeholder="输入背景、追问或修改指令 (如: '把第三章补充模型对比')..." 
              class="flex-1 bg-transparent px-3 text-xs text-slate-800 placeholder-slate-400 focus:outline-none"
            />
            <el-button 
              @click="sendQuery" 
              :loading="isGenerating"
              type="primary" 
              circle 
              class="!w-9 !h-9 !rounded-full shadow-xs">
              <el-icon v-if="!isGenerating"><Promotion /></el-icon>
            </el-button>
          </div>
          <div class="text-[10px] text-center text-slate-400 mt-2">HavenResearch Pro 支持多轮背景记忆与局部文档修订</div>
        </footer>

      </div>

      <!-- 2.2 右侧: Artifacts 文档画布面板 (Canvas Side) -->
      <div v-if="showArtifactCanvas && artifact.content" 
           class="w-full md:w-[500px] lg:w-[600px] border-l border-slate-200/90 bg-white flex flex-col h-full shadow-2xl z-20 transition-all duration-300">
        
        <!-- Artifacts 画布 Header -->
        <div class="h-14 border-b border-slate-200/80 px-5 flex items-center justify-between bg-slate-50/80">
          <div class="flex items-center space-x-2 overflow-hidden">
            <el-tag size="small" type="success" effect="dark" class="!font-bold !rounded-md">{{ artifact.version }}</el-tag>
            <span class="font-bold text-slate-800 text-xs truncate">{{ artifact.title || '当前研究文档' }}</span>
          </div>

          <div class="flex items-center space-x-2">
            <el-button @click="copyArtifactMarkdown" size="small" circle plain class="!border-slate-200">
              <el-icon :size="14"><DocumentCopy /></el-icon>
            </el-button>
            <el-button @click="showArtifactCanvas = false" size="small" circle plain class="!border-slate-200">
              <el-icon :size="14"><Close /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- 背景记忆胶囊 -->
        <div v-if="artifact.background_context" class="bg-amber-50/80 border-b border-amber-200/60 px-5 py-2 text-[11px] text-amber-800 flex items-center space-x-1.5">
          <span class="font-bold">🧠 记忆背景:</span>
          <span class="truncate flex-1">{{ artifact.background_context }}</span>
        </div>

        <!-- Artifact Markdown 大文档查看区 -->
        <div class="flex-1 overflow-y-auto p-6 prose prose-slate max-w-none text-xs leading-relaxed" v-html="renderMarkdown(artifact.content)"></div>

      </div>

    </el-container>

    <!-- 3. Auth 登录 / 注册 Modal 弹窗 -->
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

    // Artifacts 画布状态
    const showArtifactCanvas = ref(false)
    const artifact = ref({
      version: "v1.0",
      title: "文档画布",
      background_context: "",
      content: ""
    })

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
        ElMessage.error(e.response?.data?.detail || "认证失败")
      }
    }

    function logout() {
      token.value = ""
      currentUser.value = null
      historySessions.value = []
      messages.value = []
      artifact.value.content = ""
      localStorage.removeItem("haven_token")
      ElMessage.info("已退出登录")
    }

    function startNewChat() {
      messages.value = []
      artifact.value.content = ""
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

        // 加载当前会话的 Artifact 画布
        try {
          const artRes = await chatApi.getArtifact(sessionId)
          if (artRes.data && artRes.data.current_document) {
            artifact.value.content = artRes.data.current_document
            artifact.value.version = artRes.data.document_version || "v1.0"
            artifact.value.title = artRes.data.title || "技术研究文档"
            artifact.value.background_context = artRes.data.background_context || ""
            showArtifactCanvas.value = true
          } else {
            artifact.value.content = ""
          }
        } catch (e) {
          artifact.value.content = ""
        }

        scrollToBottom()
      } catch (e) {
        messages.value = []
      }
    }

    async function deleteSession(sessionId) {
      try {
        await chatApi.deleteSession(sessionId)
        ElMessage.success("会话已删除")
        await fetchSessions()
        if (currentSessionId.value === sessionId) {
          startNewChat()
        }
      } catch (e) {}
    }

    function quickStart(topic) {
      inputQuery.value = topic
      sendQuery()
    }

    function getShortIntentLabel(intent) {
      const map = {
        "CHAT_ONLY": "💬 简短答疑",
        "GENERATE_DOC": "📝 创建文档",
        "EDIT_DOC": "✏️ 局部修饰",
        "RESEARCH_QNA": "🔍 深度搜索"
      }
      return map[intent] || "✦ Agent"
    }

    async function sendQuery() {
      const query = inputQuery.value.trim()
      if (!query || isGenerating.value) return

      const userIdx = messages.value.length
      messages.value.push({ role: "user", content: query })
      inputQuery.value = ""
      isGenerating.value = true

      const assistantMsg = {
        role: "assistant",
        agent_persona: "正在智能识别意图...",
        intent: "",
        content: "",
        sources: []
      }
      messages.value.push(assistantMsg)
      scrollToUserQuestion(userIdx)

      const sessionId = currentSessionId.value || ("session_" + Date.now())
      currentSessionId.value = sessionId

      const url = `/api/v1/chat/stream?session_id=${sessionId}&query=${encodeURIComponent(query)}&report_source=${reportSource.value}`
      const eventSource = new EventSource(url)

      const lastIdx = messages.value.length - 1
      let currentIntent = ""

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const targetMsg = messages.value[lastIdx]
          
          if (data.type === "intent_meta") {
            currentIntent = data.intent
            if (targetMsg) targetMsg.intent = data.intent
            if (data.has_document && !artifact.value.content) {
              showArtifactCanvas.value = true
            }
          } else if (data.type === "persona") {
            if (targetMsg) targetMsg.agent_persona = data.content
          } else if (data.type === "chunk") {
            if (targetMsg) targetMsg.content += data.content
            if (currentIntent === "EDIT_DOC" || currentIntent === "GENERATE_DOC") {
              artifact.value.content = targetMsg ? targetMsg.content : ""
              showArtifactCanvas.value = true
            }
          } else if (data.type === "complete") {
            if (targetMsg) targetMsg.sources = data.sources || []
            if (data.version) {
              artifact.value.version = data.version
            }
            if (data.document) {
              artifact.value.content = data.document
              showArtifactCanvas.value = true
            }
            isGenerating.value = false
            fetchSessions()
            eventSource.close()
          }
          autoScrollStream()
        } catch (e) {
          console.error("SSE JSON error:", e)
        }
      }

      eventSource.onerror = () => {
        isGenerating.value = false
        eventSource.close()
      }
    }

    function renderMarkdown(content) {
      if (!content) return "<span class='typing-cursor text-blue-600 font-semibold'>正在推流分析中...</span>"
      return marked.parse(content)
    }

    function copyArtifactMarkdown() {
      if (!artifact.value.content) return
      navigator.clipboard.writeText(artifact.value.content)
      ElMessage.success("已复制文档 Markdown 到剪贴板！")
    }

    const isUserScrolledUp = ref(false)

    function handleScroll(e) {
      const container = e.target
      if (!container) return
      const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight
      // 如果距离底部超过 120px，认定用户在手动向上翻阅历史，暂停自动强行拉回底部
      if (distanceFromBottom > 120) {
        isUserScrolledUp.value = true
      } else {
        isUserScrolledUp.value = false
      }
    }

    function scrollToUserQuestion(idx) {
      isUserScrolledUp.value = false // 发送新问题时强制重置上滑状态
      nextTick(() => {
        const container = document.getElementById("messages-container")
        const userEl = document.getElementById(`msg-${idx}`)
        if (container && userEl) {
          const targetTop = Math.max(0, userEl.offsetTop - 30)
          container.scrollTo({
            top: targetTop,
            behavior: 'smooth'
          })
        } else if (container) {
          container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
          })
        }
      })
    }

    function autoScrollStream() {
      // 仅当用户未手动向上滚动查看历史记录时，随流式吐字实时平滑置底
      if (!isUserScrolledUp.value) {
        nextTick(() => {
          const container = document.getElementById("messages-container")
          if (container) {
            container.scrollTo({
              top: container.scrollHeight,
              behavior: 'smooth'
            })
          }
        })
      }
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
      showArtifactCanvas,
      artifact,
      openAuthModal,
      handleUserMenuCommand,
      handleAuthSubmit,
      logout,
      startNewChat,
      loadSession,
      deleteSession,
      quickStart,
      getShortIntentLabel,
      sendQuery,
      renderMarkdown,
      copyArtifactMarkdown,
      handleScroll
    }
  }
}
</script>

<style>
.typing-cursor::after {
  content: '▋';
  animation: blink 1s infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.prose h1, .prose h2, .prose h3 {
  color: #1e293b;
  font-weight: 700;
  margin-top: 1rem;
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
}
</style>
