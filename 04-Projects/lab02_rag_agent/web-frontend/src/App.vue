<template>
  <div class="min-h-screen w-screen bg-gradient-to-b from-[#f0f4f9] via-[#f4f7fc] to-[#e8effe] text-slate-800 font-sans flex flex-col justify-between overflow-x-hidden selection:bg-blue-200">
    
    <!-- =================================================================== -->
    <!-- 1. 顶部 Header (Gemini 简约星徽与模式) -->
    <!-- =================================================================== -->
    <header class="h-16 px-6 flex items-center justify-between border-b border-slate-200/60 bg-white/60 backdrop-blur-md sticky top-0 z-20">
      <div class="flex items-center space-x-3">
        <!-- Gemini 风格四色 Spark 图标 -->
        <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-400 via-rose-400 to-indigo-500 flex items-center justify-center shadow-sm">
          <span class="text-white font-bold text-sm">✦</span>
        </div>
        <div class="flex items-center space-x-2">
          <span class="font-bold text-slate-800 text-lg tracking-tight">HavenResearch</span>
          <span class="bg-blue-100 text-blue-700 text-[10px] font-semibold px-2 py-0.5 rounded-full border border-blue-200">Pro 1.5</span>
        </div>
      </div>

      <!-- 右上角数据源模式选择 -->
      <div class="flex items-center space-x-2 text-xs">
        <span class="text-slate-500 font-medium">研究智库模式:</span>
        <select v-model="reportSource" class="bg-white border border-slate-200 rounded-full px-3.5 py-1.5 text-xs text-slate-700 font-medium shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 cursor-pointer">
          <option value="hybrid">🌐 混合双引擎 (Web + Qdrant 知识库)</option>
          <option value="local">💾 纯本地知识库 (107本电子书 + Markdown)</option>
          <option value="web">🌐 纯全网实时检索 (Tavily AI Search)</option>
        </select>
      </div>
    </header>

    <!-- =================================================================== -->
    <!-- 2. 中央内容区域 (Gemini 首页 Hero 与对话流) -->
    <!-- =================================================================== -->
    <main class="flex-1 max-w-4xl w-full mx-auto px-4 py-8 flex flex-col justify-between">
      
      <!-- 初始 Hero 欢迎大字 (未开始对话时显示) -->
      <div v-if="messages.length === 0" class="flex-1 flex flex-col items-center justify-center my-auto text-center">
        <h1 class="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900 mb-8 tracking-tight">
          海文，需要我帮你做点什么？
        </h1>

        <!-- 浮动快捷建议胶囊按钮 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl w-full mb-10">
          <button @click="quickStart('2026年企业级 AI Agent 架构设计与技术选型')" 
                  class="p-4 bg-white/80 hover:bg-white border border-slate-200/80 hover:border-blue-300 rounded-2xl text-left text-xs text-slate-700 shadow-sm hover:shadow-md transition group">
            <div class="font-semibold text-slate-800 mb-1 flex items-center space-x-1.5">
              <span>💡 2026 AI Agent 架构设计</span>
              <span class="group-hover:translate-x-1 transition text-blue-500">→</span>
            </div>
            <div class="text-slate-400 text-[11px] truncate">探索自主控制流、ReAct 循环与多智能体协作...</div>
          </button>
          
          <button @click="quickStart('RAG 检索增强生成的双路混合检索与重排序优化')" 
                  class="p-4 bg-white/80 hover:bg-white border border-slate-200/80 hover:border-blue-300 rounded-2xl text-left text-xs text-slate-700 shadow-sm hover:shadow-md transition group">
            <div class="font-semibold text-slate-800 mb-1 flex items-center space-x-1.5">
              <span>💡 RAG 混合检索与重排序</span>
              <span class="group-hover:translate-x-1 transition text-blue-500">→</span>
            </div>
            <div class="text-slate-400 text-[11px] truncate">BM25 + 向量召回与 BGE Cross-Encoder 精排...</div>
          </button>
        </div>
      </div>

      <!-- 对话消息列表 (已开始对话时显示) -->
      <div v-else class="flex-1 space-y-6 pb-28">
        <div v-for="(msg, idx) in messages" :key="idx" class="space-y-3">
          
          <!-- 用户提问 (右侧靠齐，柔和灰蓝气泡) -->
          <div v-if="msg.role === 'user'" class="flex justify-end">
            <div class="bg-[#e3eefc] text-slate-800 rounded-3xl px-5 py-3.5 max-w-2xl text-sm leading-relaxed shadow-sm font-medium">
              {{ msg.content }}
            </div>
          </div>

          <!-- Agent 回答 (Gemini 风格左侧极简，带有彩色 Spark 徽章) -->
          <div v-else class="flex items-start space-x-4">
            <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-400 via-rose-400 to-indigo-500 flex items-center justify-center text-white text-xs font-bold shadow-md flex-shrink-0 mt-1">
              ✦
            </div>
            
            <div class="flex-1 space-y-3">
              <!-- Persona 动态专家勋章 -->
              <div v-if="msg.agent_persona" class="inline-flex items-center space-x-1.5 bg-blue-50 border border-blue-200/80 px-3 py-1 rounded-full text-xs text-blue-700 font-semibold shadow-2xs">
                <span>🎭 调用的专家 Persona:</span>
                <span class="text-slate-900">{{ msg.agent_persona }}</span>
              </div>

              <!-- 折叠推理观察步骤 (Thinking Accordion) -->
              <div v-if="msg.steps && msg.steps.length > 0" class="bg-white/90 border border-slate-200 rounded-2xl p-4 text-xs space-y-1.5 shadow-sm font-mono">
                <div class="font-bold text-blue-600 flex items-center justify-between border-b border-slate-100 pb-2 mb-1.5">
                  <span>⚡ Agent 自主推理观察步骤 ({{ msg.steps.length }})</span>
                  <span v-if="msg.isStreaming" class="text-amber-500 animate-pulse font-sans">● 执行中...</span>
                </div>
                <div v-for="(step, sIdx) in msg.steps" :key="sIdx" class="text-slate-600 flex items-center space-x-2">
                  <span class="text-blue-500 font-bold">›</span>
                  <span>{{ step }}</span>
                </div>
              </div>

              <!-- Markdown 报告正文 (纯白卡片，优雅排版) -->
              <div class="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-md prose prose-slate max-w-none text-xs leading-relaxed"
                   v-html="renderMarkdown(msg.content)">
              </div>

              <!-- Footer 元数据勋章 -->
              <div v-if="msg.cost_summary" class="flex flex-wrap items-center gap-3 text-[11px] text-slate-500 pt-1">
                <span class="bg-white px-3 py-1 rounded-full border border-slate-200 shadow-2xs">💰 Token 消耗: {{ msg.cost_summary.total_tokens }} (费: ${{ msg.cost_summary.total_cost_usd }})</span>
                <span v-if="msg.sources" class="bg-white px-3 py-1 rounded-full border border-slate-200 shadow-2xs">📚 引用精排干货: {{ msg.sources.length }} 条</span>
              </div>
            </div>
          </div>

        </div>
      </div>

    </main>

    <!-- =================================================================== -->
    <!-- 3. Gemini 经典悬浮居中 Pill 输入框 (底部 Sticky) -->
    <!-- =================================================================== -->
    <footer class="fixed bottom-6 left-0 right-0 max-w-3xl mx-auto px-4 z-30">
      <div class="bg-white/90 backdrop-blur-xl border border-slate-200/90 rounded-full p-2.5 shadow-2xl shadow-blue-500/10 flex items-center space-x-3 hover:border-blue-300 transition-all">
        <!-- 附件加号按钮 -->
        <button class="w-9 h-9 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-500 transition text-lg font-light flex-shrink-0">
          ＋
        </button>

        <!-- 文本输入框 -->
        <input v-model="inputQuery" 
               @keydown.enter="sendQuery" 
               type="text" 
               placeholder="问问 HavenResearch..." 
               class="flex-1 bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none px-2 font-medium" />

        <!-- 右侧经典 Gemini 按钮组 -->
        <div class="flex items-center space-x-2 flex-shrink-0 pr-1">
          <!-- 模式 Pill Badge -->
          <div class="hidden sm:flex items-center space-x-1 px-3 py-1 bg-slate-100 rounded-full text-xs font-semibold text-slate-600">
            <span>Pro</span>
            <span class="text-blue-600 font-bold">✦</span>
          </div>

          <!-- 发送按钮 -->
          <button @click="sendQuery" 
                  :disabled="isGenerating" 
                  class="w-10 h-10 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-40 text-white flex items-center justify-center transition shadow-md flex-shrink-0">
            <span v-if="isGenerating" class="animate-spin text-sm">↻</span>
            <span v-else class="text-sm font-bold">✦</span>
          </button>
        </div>
      </div>
      <div class="text-[10px] text-center text-slate-400 mt-2">HavenResearch Pro 可能会提供不准确的信息，请验证重要结论。</div>
    </footer>

  </div>
</template>

<script>
import { ref, nextTick } from 'vue'

export default {
  name: 'App',
  setup() {
    const inputQuery = ref("")
    const reportSource = ref("hybrid")
    const messages = ref([])
    const isGenerating = ref(false)

    function quickStart(topic) {
      inputQuery.value = topic
      sendQuery()
    }

    async function sendQuery() {
      const query = inputQuery.value.trim()
      if (!query || isGenerating.value) return

      // 记录用户消息
      messages.value.push({ role: "user", content: query })
      inputQuery.value = ""
      isGenerating.value = true

      // 准备 Agent 助手消息占位
      const assistantMsg = {
        role: "assistant",
        agent_persona: "",
        steps: [],
        content: "",
        isStreaming: true
      }
      messages.value.push(assistantMsg)
      scrollToBottom()

      // 发起 SSE 打字机流式推流请求
      const sessionId = "demo_session_" + Date.now()
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
      if (!content) return "<span class='typing-cursor text-blue-600 font-semibold'>正在与 DeepSeek API 深度通信并合成技术报告...</span>"
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
      quickStart,
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

/* Gemini 风格 Markdown 表格排版 */
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
  font-size: 0.75rem;
}
.prose th, .prose td {
  border: 1px solid #e2e8f0;
  padding: 0.5rem 0.75rem;
}
.prose th {
  background-color: #f8fafc;
  color: #0f172a;
}
</style>
