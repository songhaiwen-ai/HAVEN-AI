<template>
  <el-container class="h-screen w-screen bg-[#f8fafc] text-slate-800 font-sans overflow-hidden selection:bg-blue-100">
    
    <!-- =================================================================== -->
    <!-- 1. 左侧 Element Plus 侧边栏 (280px 宽，调大字号与间距) -->
    <!-- =================================================================== -->
    <el-aside :width="isSidebarCollapsed ? '64px' : '280px'" class="bg-[#f1f5f9] border-r border-slate-200/80 flex flex-col justify-between transition-all duration-300 relative z-20">
      
      <div class="p-4 space-y-5">
        
        <!-- Header Logo & 折叠按钮 -->
        <div class="flex items-center justify-between">
          <div v-if="!isSidebarCollapsed" class="flex items-center space-x-2.5">
            <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold text-sm flex items-center justify-center shadow-xs">
              H
            </div>
            <span class="font-bold text-slate-800 text-lg tracking-tight">HavenResearch</span>
          </div>

          <el-button @click="isSidebarCollapsed = !isSidebarCollapsed" 
                     circle 
                     size="small" 
                     class="!bg-transparent hover:!bg-slate-200/60 !border-none text-slate-500">
            <el-icon :size="18"><Fold v-if="!isSidebarCollapsed" /><Expand v-else /></el-icon>
          </el-button>
        </div>

        <!-- 发起新对话按钮 -->
        <div class="pt-1">
          <el-button @click="startNewChat" 
                     type="primary" 
                     plain 
                     size="large" 
                     class="w-full !rounded-xl !h-12 !text-sm !font-bold shadow-2xs hover:shadow-xs flex items-center justify-start px-4">
            <el-icon :size="18" class="mr-2 text-blue-600"><Plus /></el-icon>
            <span v-if="!isSidebarCollapsed">发起新对话</span>
          </el-button>
        </div>

        <!-- 历史对话 Header & 动态会话列表 -->
        <div v-if="!isSidebarCollapsed" class="pt-3 border-t border-slate-200/60">
          <div class="text-xs font-bold text-slate-400 px-2 mb-2.5 uppercase tracking-wider">最近历史对话</div>
          
          <el-scrollbar max-height="calc(100vh - 280px)">
            <div class="space-y-1 pr-1">
              <div v-for="session in historySessions" 
                   :key="session.session_id"
                   @click="loadSession(session.session_id)"
                   :class="[
                     'px-3.5 py-3 rounded-xl text-sm transition-all duration-200 flex items-center justify-between cursor-pointer group',
                     currentSessionId === session.session_id ? 'bg-white text-blue-600 font-semibold shadow-2xs' : 'text-slate-600 hover:bg-slate-200/60 hover:text-slate-900'
                   ]">
                <span class="truncate leading-normal">{{ session.title || '新对话' }}</span>
                <el-icon @click.stop="deleteSession(session.session_id)" class="opacity-0 group-hover:opacity-100 hover:text-rose-600 transition text-sm"><Delete /></el-icon>
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
      <div class="p-3.5 border-t border-slate-200/80 bg-[#f1f5f9] relative">
        <el-dropdown trigger="click" class="w-full" @command="handleUserMenuCommand">
          <div class="flex items-center justify-between w-full p-2.5 rounded-xl hover:bg-slate-200/70 cursor-pointer transition-all">
            <div class="flex items-center space-x-3 overflow-hidden">
              <el-avatar v-if="currentUser" :size="36" class="!bg-blue-600 !text-white !font-bold !text-sm flex-shrink-0 shadow-2xs">
                {{ currentUser.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <el-avatar v-else :size="36" class="!bg-slate-400 !text-white flex-shrink-0 shadow-2xs">
                <el-icon :size="18"><User /></el-icon>
              </el-avatar>

              <div v-if="!isSidebarCollapsed" class="overflow-hidden text-left">
                <div class="text-sm font-semibold text-slate-800 truncate">
                  {{ currentUser ? currentUser.username : '未登录' }}
                </div>
                <div class="text-xs text-slate-400 font-medium">
                  {{ currentUser ? '已验证用户' : '点击登录/注册' }}
                </div>
              </div>
            </div>
            <el-icon v-if="!isSidebarCollapsed" class="text-slate-400 text-sm"><Setting /></el-icon>
          </div>

          <template #dropdown>
            <el-dropdown-menu class="!rounded-xl !p-2 !w-48 shadow-xl">
              <template v-if="currentUser">
                <div class="px-3 py-2 border-b border-slate-100 mb-1">
                  <div class="font-bold text-sm text-slate-800">{{ currentUser.username }}</div>
                  <div class="text-xs text-slate-400">已登录账号</div>
                </div>
                <el-dropdown-item command="logout" class="!text-rose-600 !font-semibold !rounded-lg !text-xs">
                  <el-icon class="mr-1.5"><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </template>

              <template v-else>
                <el-dropdown-item command="login" class="!rounded-lg !font-medium !text-xs">
                  <el-icon class="mr-1.5"><User /></el-icon>
                  账号登录
                </el-dropdown-item>
                <el-dropdown-item command="register" class="!rounded-lg !font-medium !text-xs">
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
        
        <!-- 顶部功能栏 (Fixed height flex-shrink-0, 调高至 h-16) -->
        <header class="h-16 border-b border-slate-200/70 bg-white/80 backdrop-blur-md px-6 flex items-center justify-between z-10 flex-shrink-0">
          <div class="flex items-center space-x-3">
            <span class="font-bold text-slate-800 text-base tracking-tight">HavenResearch</span>
          </div>

          <div class="flex items-center space-x-3">
            <!-- 切换 Artifacts 右侧画板按键 -->
            <el-button v-if="artifact.content" 
                       @click="toggleArtifactCanvas"
                       size="default" 
                       :type="showArtifactCanvas ? 'primary' : 'default'" 
                       class="!rounded-xl !text-xs !font-semibold">
              <el-icon class="mr-1.5"><Document /></el-icon>
              {{ showArtifactCanvas ? '隐藏文档画板' : '查看文档画板 (' + artifact.version + ')' }}
            </el-button>
          </div>
        </header>

        <!-- 对话消息列表 (全宽自流式排版 max-w-7xl px-4 md:px-10，彻底消灭左右两侧大面积空白) -->
        <el-main @scroll="handleScroll" class="flex-1 overflow-y-auto py-6 px-4 md:px-10 space-y-6 w-full max-w-7xl mx-auto pb-8" id="messages-container">
          
          <!-- 欢迎/空白页 (调大字号与视觉卡片) -->
          <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-center my-auto py-16 space-y-6">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-sky-400 text-white flex items-center justify-center text-3xl font-bold shadow-lg shadow-blue-500/20">
              ✦
            </div>
            <div class="space-y-3">
              <h2 class="text-2xl md:text-3xl font-extrabold text-slate-800 tracking-tight">智能研究 & 协同文档编辑助手</h2>
              <p class="text-sm md:text-base text-slate-500 max-w-lg mx-auto leading-relaxed">支持多轮长对话背景记忆、智能意图分流与长文档 Artifacts 画布协同修改。</p>
            </div>

            <!-- 快捷启动 Prompt 胶囊 -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl text-left pt-4">
              <div @click="quickStart('我们团队是做智慧农业 SaaS 的，主要面向水稻种植')" class="p-4.5 bg-white border border-slate-200/80 hover:border-blue-400 rounded-2xl cursor-pointer shadow-2xs hover:shadow-xs transition-all">
                <div class="font-bold text-sm text-slate-800">🌱 1. 补充项目背景</div>
                <div class="text-xs text-slate-400 mt-1.5">告知助手项目背景，暂不生成文档</div>
              </div>
              <div @click="quickStart('结合上述背景，帮我设计一份系统架构方案文档')" class="p-4.5 bg-white border border-slate-200/80 hover:border-blue-400 rounded-2xl cursor-pointer shadow-2xs hover:shadow-xs transition-all">
                <div class="font-bold text-sm text-slate-800">📝 2. 生成全量架构文档</div>
                <div class="text-xs text-slate-400 mt-1.5">基于已知背景，创建 v1.0 文档画布</div>
              </div>
            </div>
          </div>

          <!-- 对话消息渲染 (调大消息气泡与 Markdown 文本) -->
          <div v-for="(msg, idx) in messages" :key="msg.id || ('msg-' + idx)" :id="'msg-' + idx" class="space-y-3">
            
            <!-- 用户消息 (text-sm md:text-base 调大字体与最大宽度) -->
            <div v-if="msg.role === 'user'" class="flex justify-end">
              <div class="bg-blue-600 text-white px-5 py-3.5 rounded-2xl rounded-tr-xs max-w-3xl md:max-w-4xl text-sm md:text-base font-normal shadow-xs leading-relaxed">
                {{ msg.content }}
              </div>
            </div>

            <!-- 助手消息 (text-sm md:text-base 调大字体与全宽适应) -->
            <div v-else class="flex items-start space-x-3.5">
              <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center text-sm font-bold shadow-xs flex-shrink-0 mt-0.5">
                ✦
              </div>

              <div class="flex-1 bg-white border border-slate-200/80 rounded-2xl p-5 md:p-7 shadow-2xs text-sm md:text-base space-y-4 overflow-hidden">
                
                <!-- 意图与 Agent 步骤标识 -->
                <div v-if="msg.agent_persona || msg.intent" class="flex items-center justify-between border-b border-slate-100 pb-2.5 mb-2.5">
                  <div class="text-xs font-bold text-blue-600 flex items-center space-x-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-blue-600 animate-pulse"></span>
                    <span>{{ msg.agent_persona || 'Agent 已响应' }}</span>
                  </div>
                  <el-tag v-if="msg.intent" size="small" effect="plain" class="!rounded-md !text-xs !font-medium">
                    {{ getShortIntentLabel(msg.intent) }}
                  </el-tag>
                </div>

                <!-- Markdown 内容 (prose-base 调大 Markdown 字体) -->
                <div class="prose prose-slate prose-base max-w-none text-slate-800 leading-relaxed overflow-x-auto text-sm md:text-base" v-html="renderMarkdown(msg.content)"></div>

                <!-- 资料来源 (Sources) -->
                <div v-if="msg.sources && msg.sources.length > 0" class="pt-3 border-t border-slate-100">
                  <div class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">参考引用的参考来源 ({{ msg.sources.length }})</div>
                  <div class="flex flex-wrap gap-2">
                    <a v-for="(src, sIdx) in msg.sources" 
                       :key="sIdx" 
                       :href="src.url" 
                       target="_blank" 
                       class="inline-flex items-center space-x-1 bg-slate-50 hover:bg-blue-50 border border-slate-200/80 hover:border-blue-300 text-slate-600 hover:text-blue-600 px-3 py-1.5 rounded-lg text-xs transition-all">
                      <span class="truncate max-w-xs">{{ src.title || src.url }}</span>
                      <el-icon class="text-xs"><TopRight /></el-icon>
                    </a>
                  </div>
                </div>

              </div>
            </div>

          </div>

        </el-main>

        <!-- 底部胶囊输入框 (使用 max-w-7xl px-4 md:px-10 展开对齐) -->
        <footer class="flex-shrink-0 bg-[#f8fafc]/95 border-t border-slate-200/60 py-4 px-4 md:px-10 z-30">
          <div class="w-full max-w-7xl mx-auto">
            <div class="bg-white border border-slate-200/90 rounded-2xl p-3 shadow-lg shadow-blue-500/5 flex items-end space-x-3 hover:border-blue-300 transition-all">
              <textarea 
                v-model="inputQuery" 
                @keydown="handleKeydown"
                @compositionstart="handleCompositionStart"
                @compositionend="handleCompositionEnd"
                rows="1"
                placeholder="输入背景、追问或修改指令 (Shift + Enter 换行，Enter 发送)..." 
                class="flex-1 bg-transparent px-3 text-sm md:text-base text-slate-800 placeholder-slate-400 focus:outline-none resize-none max-h-36 min-h-[36px] py-1.5 leading-relaxed font-normal"
              ></textarea>

              <!-- 未在生成时：显示发送按钮 (增大尺寸) -->
              <el-button 
                v-if="!isGenerating"
                @click="sendQuery" 
                type="primary" 
                circle 
                class="!w-10 !h-10 !rounded-full shadow-xs flex-shrink-0 mb-0.5">
                <el-icon :size="18"><Promotion /></el-icon>
              </el-button>

              <!-- 正在流式生成中：显示红色中断/停止按钮 (增大尺寸) -->
              <el-button 
                v-else
                @click="stopGeneration" 
                type="danger" 
                circle 
                title="点击停止输出"
                class="!w-10 !h-10 !rounded-full shadow-xs flex-shrink-0 mb-0.5 !bg-rose-500 !border-rose-500 hover:!bg-rose-600 transition-transform active:scale-95">
                <div class="w-4 h-4 bg-white rounded-xs"></div>
              </el-button>
            </div>
            <div class="text-xs text-center text-slate-400 mt-2">HavenResearch 支持多轮背景记忆、局部文档修订与随时停止生成</div>
          </div>
        </footer>

      </div>

      <!-- 2.2 右侧: Artifacts 文档画布面板 (Canvas Side - 调大字号) -->
      <div v-if="showArtifactCanvas && artifact.content" 
           class="w-full md:w-[550px] lg:w-[680px] border-l border-slate-200/90 bg-white flex flex-col h-full shadow-2xl z-20 transition-all duration-300">
        
        <!-- Artifacts 画布 Header -->
        <div class="h-16 border-b border-slate-200/80 px-6 flex items-center justify-between bg-slate-50/80">
          <div class="flex items-center space-x-2.5 overflow-hidden">
            <el-tag size="default" type="success" effect="dark" class="!font-bold !rounded-md">{{ artifact.version }}</el-tag>
            <span class="font-bold text-slate-800 text-sm md:text-base truncate">{{ artifact.title || '当前研究文档' }}</span>
          </div>

          <div class="flex items-center space-x-2">
            <el-button @click="copyArtifactMarkdown" size="default" circle plain class="!border-slate-200">
              <el-icon :size="16"><DocumentCopy /></el-icon>
            </el-button>
            <el-button @click="closeArtifactCanvas" size="default" circle plain class="!border-slate-200">
              <el-icon :size="16"><Close /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- 背景记忆胶囊 -->
        <div v-if="artifact.background_context" class="bg-amber-50/80 border-b border-amber-200/60 px-6 py-2.5 text-xs text-amber-800 flex items-center space-x-2">
          <span class="font-bold">🧠 记忆背景:</span>
          <span class="truncate flex-1 font-medium">{{ artifact.background_context }}</span>
        </div>

        <!-- Artifact Markdown 大文档查看区 (调大字号与内边距) -->
        <div class="flex-1 overflow-y-auto p-6 md:p-8 prose prose-slate max-w-none text-sm md:text-base leading-relaxed text-slate-800" v-html="renderMarkdown(artifact.content)"></div>

      </div>

    </el-container>

    <!-- 3. Auth 登录 / 注册 Modal 弹窗 -->
    <el-dialog v-model="showAuthModal" width="460px" :show-close="false" custom-class="!rounded-3xl">
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
          // 刷新页面后自动恢复最近一条会话及其右侧 Artifacts 文档画布
          if (historySessions.value.length > 0) {
            await loadSession(historySessions.value[0].session_id)
          }
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
      if (!sessionId) return
      currentSessionId.value = sessionId
      messages.value = [] // 1. 先清空，触发 Vue3 响应式节点重新挂载
      
      try {
        const res = await chatApi.getMessages(sessionId)
        if (res.data && res.data.length > 0) {
          messages.value = res.data.map(m => ({
            id: m.id,
            role: m.role,
            content: m.content,
            sources: m.sources || [],
            agent_persona: m.role === 'assistant' ? 'Agent 已响应' : ''
          }))
        } else {
          messages.value = []
        }

        // 2. 加载当前会话的 Artifact 画布
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

        // 3. 延时等待 DOM 重排渲染完成后平滑置底视区
        isUserScrolledUp.value = false
        nextTick(() => {
          setTimeout(() => {
            const container = document.getElementById("messages-container")
            if (container) {
              container.scrollTo({
                top: container.scrollHeight,
                behavior: 'smooth'
              })
            }
          }, 80)
        })
      } catch (e) {
        console.error("加载历史会话失败:", e)
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

    const activeEventSource = ref(null)
    const isComposing = ref(false)

    function handleCompositionStart() {
      isComposing.value = true
    }

    function handleCompositionEnd() {
      setTimeout(() => {
        isComposing.value = false
      }, 10)
    }

    function handleKeydown(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        if (!isComposing.value && !e.isComposing && e.keyCode !== 229) {
          e.preventDefault()
          sendQuery()
        }
      }
    }

    function stopGeneration() {
      if (activeEventSource.value) {
        activeEventSource.value.close()
        activeEventSource.value = null
      }
      isGenerating.value = false

      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg && lastMsg.role === 'assistant') {
        if (!lastMsg.content) {
          lastMsg.content = "*(响应已被用户中断)*"
        } else if (!lastMsg.content.includes("已手动中断输出")) {
          lastMsg.content += "\n\n*(已手动中断输出)*"
        }
      }
      ElMessage.info("已停止推流输出")
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

      userManuallyClosedCanvas.value = false
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

      const token = localStorage.getItem('haven_token') || ''
      const url = `/api/v1/chat/stream?session_id=${sessionId}&query=${encodeURIComponent(query)}&report_source=hybrid&token=${encodeURIComponent(token)}`
      const eventSource = new EventSource(url)
      activeEventSource.value = eventSource

      const lastIdx = messages.value.length - 1
      let currentIntent = ""

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const targetMsg = messages.value[lastIdx]
          
          if (data.type === "intent_meta") {
            currentIntent = data.intent
            if (targetMsg) targetMsg.intent = data.intent
            if (currentIntent === "EDIT_DOC" || currentIntent === "GENERATE_DOC") {
              artifact.value.content = ""
              if (!userManuallyClosedCanvas.value) {
                showArtifactCanvas.value = true
              }
            } else if (data.has_document && !artifact.value.content) {
              if (!userManuallyClosedCanvas.value) {
                showArtifactCanvas.value = true
              }
            }
          } else if (data.type === "persona") {
            if (targetMsg) targetMsg.agent_persona = data.content
          } else if (data.type === "chunk") {
            if (currentIntent === "EDIT_DOC" || currentIntent === "GENERATE_DOC") {
              artifact.value.content += data.content
              if (!userManuallyClosedCanvas.value) {
                showArtifactCanvas.value = true
              }
              if (targetMsg) {
                targetMsg.content = "✦ 正在右侧画布实时增量生成与修订文档中..."
              }
            } else {
              // 普通对话答疑：在左侧对话卡片正常展示打字机效果
              if (targetMsg) targetMsg.content += data.content
            }
          } else if (data.type === "complete") {
            if (currentIntent === "EDIT_DOC" || currentIntent === "GENERATE_DOC") {
              if (data.document) {
                artifact.value.content = data.document
              }
              if (data.version) {
                artifact.value.version = data.version
              }
              showArtifactCanvas.value = true
              if (targetMsg) {
                const verStr = artifact.value.version || 'v1.1'
                targetMsg.content = currentIntent === 'EDIT_DOC'
                  ? `已成功在右侧画布为您完成文档修订 (${verStr})！您可以在右侧画布查看全量最新内容或继续提出修订指令。`
                  : `已成功在右侧画布为您生成全量技术研究文档 (${verStr})！您可以在右侧画布查阅或提出修订指令。`
              }
            } else {
              if (targetMsg) targetMsg.sources = data.sources || []
            }
            isGenerating.value = false
            activeEventSource.value = null
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
        activeEventSource.value = null
        eventSource.close()
      }
    }

    function renderMarkdown(content) {
      if (!content) return "<span class='typing-cursor text-blue-600 font-semibold'>正在推流分析中...</span>"
      
      let text = content.trim()
      // 如果全量文档被错误包裹在最外层的代码块如 ```markdown ... ``` 中，剥离最外层代码块标签
      if (text.startsWith("```")) {
        const lines = text.split("\n")
        if (lines.length > 2 && (lines[0].startsWith("```markdown") || lines[0].startsWith("```md") || lines[0].startsWith("```"))) {
          if (lines[lines.length - 1].trim() === "```") {
            text = lines.slice(1, -1).join("\n").trim()
          } else {
            text = lines.slice(1).join("\n").trim()
          }
        }
      }
      return marked.parse(text)
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
        setTimeout(() => {
          const container = document.getElementById("messages-container")
          const userEl = document.getElementById(`msg-${idx}`)
          if (container && userEl) {
            const targetTop = Math.max(0, userEl.offsetTop - 16)
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
        }, 60)
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
      toggleArtifactCanvas,
      closeArtifactCanvas,
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
      stopGeneration,
      handleKeydown,
      handleCompositionStart,
      handleCompositionEnd,
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

/* 优化 Markdown Prose 字体排版与可读性 */
.prose {
  font-size: 0.95rem;
  line-height: 1.75;
  color: #1e293b;
}

.prose h1 {
  font-size: 1.5rem;
  font-weight: 800;
  color: #0f172a;
  margin-top: 1.25rem;
  margin-bottom: 0.75rem;
}

.prose h2 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin-top: 1.15rem;
  margin-bottom: 0.6rem;
}

.prose h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #334155;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.prose p {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
}

.prose ul, .prose ol {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  padding-left: 1.25rem;
}

.prose li {
  margin-top: 0.25rem;
  margin-bottom: 0.25rem;
}

.prose table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.25rem 0;
  font-size: 0.9rem;
}

.prose th, .prose td {
  border: 1px solid #e2e8f0;
  padding: 0.75rem 1rem;
}

.prose th {
  background-color: #f8fafc;
  font-weight: 600;
}

.prose pre {
  background-color: #f8fafc;
  color: #1e293b;
  border: 1px solid #e2e8f0;
  padding: 1rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  overflow-x: auto;
  margin: 1rem 0;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
}

.prose pre code {
  color: #0f172a;
  background-color: transparent;
}
</style>
