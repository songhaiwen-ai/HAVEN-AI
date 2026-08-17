<template>
  <div class="w-full max-w-md mx-auto bg-white/95 border border-slate-200/90 rounded-3xl p-8 shadow-2xl space-y-6 relative overflow-hidden transition-all duration-300">
    
    <!-- 头部 Brand Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-2.5">
        <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-400 via-rose-400 to-indigo-500 flex items-center justify-center shadow-xs">
          <span class="text-white font-bold text-sm">✦</span>
        </div>
        <h2 class="font-bold text-slate-800 text-lg tracking-tight">
          {{ isRegister ? '创建 HavenResearch 账号' : '登录 HavenResearch' }}
        </h2>
      </div>
      <button v-if="closeable" @click="$emit('close')" class="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-700 transition">
        ✕
      </button>
    </div>

    <!-- 登录 / 注册 Tab 切换 -->
    <div class="flex bg-slate-100 p-1 rounded-2xl text-xs font-semibold">
      <button @click="switchTab(false)" 
              :class="['flex-1 py-2.5 rounded-xl transition-all duration-200', !isRegister ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800']">
        账号登录
      </button>
      <button @click="switchTab(true)" 
              :class="['flex-1 py-2.5 rounded-xl transition-all duration-200', isRegister ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800']">
        注册新用户
      </button>
    </div>

    <!-- 表单表单区域 -->
    <form @submit.prevent="handleSubmit" class="space-y-4 text-xs">
      
      <!-- 1. 用户名输入框 (Username Input) -->
      <div>
        <div class="flex justify-between items-center mb-1.5">
          <label class="block text-slate-600 font-medium">用户名</label>
          <span v-if="usernameTouched && !isUsernameValid" class="text-rose-500 text-[11px] animate-pulse">
            {{ usernameErrorMessage }}
          </span>
          <span v-else-if="usernameTouched && isUsernameValid" class="text-emerald-600 text-[11px] font-semibold">
            ✓ 格式符合规范
          </span>
        </div>
        <div class="relative">
          <input v-model="username" 
                 @blur="usernameTouched = true"
                 type="text" 
                 placeholder="4-20 位字母数字，以字母/数字开头" 
                 :class="[
                   'w-full bg-slate-50 border rounded-2xl p-3 text-slate-800 placeholder-slate-400 focus:outline-none transition-all duration-200',
                   usernameTouched ? (isUsernameValid ? 'border-emerald-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100' : 'border-rose-300 focus:border-rose-500 focus:ring-2 focus:ring-rose-100') : 'border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100'
                 ]" />
        </div>
      </div>

      <!-- 2. 密码输入框 (Password Input + Eye Toggle) -->
      <div>
        <div class="flex justify-between items-center mb-1.5">
          <label class="block text-slate-600 font-medium">密码</label>
          <span v-if="password" class="text-[11px] font-semibold" :style="{ color: strengthColor }">
            密码强度: {{ strengthText }}
          </span>
        </div>
        <div class="relative">
          <input v-model="password" 
                 @blur="passwordTouched = true"
                 :type="showPassword ? 'text' : 'password'" 
                 placeholder="请输入密码" 
                 :class="[
                   'w-full bg-slate-50 border rounded-2xl p-3 pr-10 text-slate-800 placeholder-slate-400 focus:outline-none transition-all duration-200',
                   passwordTouched ? (isPasswordValid ? 'border-emerald-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100' : 'border-rose-300 focus:border-rose-500 focus:ring-2 focus:ring-rose-100') : 'border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100'
                 ]" />
          
          <!-- 显示/隐藏小眼睛图标 Toggle Icon -->
          <button type="button" 
                  @click="showPassword = !showPassword" 
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition text-sm">
            <span v-if="showPassword">👁️</span>
            <span v-else>🙈</span>
          </button>
        </div>
      </div>

      <!-- 3. 三段式密码强度指示器 (Password Strength Bar) -->
      <div v-if="password" class="space-y-1.5 pt-1">
        <div class="flex space-x-1.5 h-1.5 w-full bg-slate-100 rounded-full overflow-hidden p-0.5">
          <div :class="['h-full rounded-full transition-all duration-300 flex-1', strengthScore >= 1 ? strengthBgClass : 'bg-slate-200']"></div>
          <div :class="['h-full rounded-full transition-all duration-300 flex-1', strengthScore >= 3 ? strengthBgClass : 'bg-slate-200']"></div>
          <div :class="['h-full rounded-full transition-all duration-300 flex-1', strengthScore >= 4 ? strengthBgClass : 'bg-slate-200']"></div>
        </div>
      </div>

      <!-- 4. 实时校验状态列表 (Validation Checklist) -->
      <div v-if="isRegister || password" class="bg-slate-50 border border-slate-200/80 rounded-2xl p-3.5 space-y-2 text-[11px] transition-all">
        <div class="font-semibold text-slate-600 mb-1">实时密码安全规则 checklist:</div>
        
        <div class="flex items-center space-x-2 transition-colors duration-200" :class="rulesPassed.length ? 'text-emerald-600 font-medium' : 'text-slate-400'">
          <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px]" :class="rulesPassed.length ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200 text-slate-500'">
            {{ rulesPassed.length ? '✓' : '○' }}
          </span>
          <span>至少 8 个字符 (当前: {{ password.length }})</span>
        </div>

        <div class="flex items-center space-x-2 transition-colors duration-200" :class="rulesPassed.case ? 'text-emerald-600 font-medium' : 'text-slate-400'">
          <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px]" :class="rulesPassed.case ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200 text-slate-500'">
            {{ rulesPassed.case ? '✓' : '○' }}
          </span>
          <span>包含至少一个大写字母和一个小写字母</span>
        </div>

        <div class="flex items-center space-x-2 transition-colors duration-200" :class="rulesPassed.number ? 'text-emerald-600 font-medium' : 'text-slate-400'">
          <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px]" :class="rulesPassed.number ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200 text-slate-500'">
            {{ rulesPassed.number ? '✓' : '○' }}
          </span>
          <span>包含至少一个数字 (0-9)</span>
        </div>

        <div class="flex items-center space-x-2 transition-colors duration-200" :class="rulesPassed.special ? 'text-emerald-600 font-medium' : 'text-slate-400'">
          <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px]" :class="rulesPassed.special ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200 text-slate-500'">
            {{ rulesPassed.special ? '✓' : '○' }}
          </span>
          <span>包含至少一个特殊符号 (如 @$!%*?& 等)</span>
        </div>
      </div>

      <!-- 全局错误 Banner -->
      <div v-if="errorMsg" class="text-xs text-rose-600 bg-rose-50 border border-rose-200/80 p-3 rounded-2xl font-medium flex items-center space-x-2 animate-shake">
        <span>⚠️</span>
        <span>{{ errorMsg }}</span>
      </div>

      <!-- 5. 提交按钮 (Submit Button) -->
      <button type="submit" 
              :disabled="!isFormValid || loading" 
              :class="[
                'w-full py-3 rounded-2xl text-xs font-semibold transition-all duration-200 shadow-md flex items-center justify-center space-x-1.5',
                isFormValid && !loading ? 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white cursor-pointer hover:shadow-lg' : 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
              ]">
        <span v-if="loading" class="animate-spin text-sm">↻</span>
        <span>{{ isRegister ? '确认注册并进入系统' : '立即登录 HavenResearch' }}</span>
      </button>

    </form>

    <!-- 6. 底部辅助链接 (Footer Link) -->
    <div class="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
      <span v-if="isRegister">
        已有账号？
        <button @click="switchTab(false)" class="text-blue-600 font-semibold hover:underline cursor-pointer">
          直接登录
        </button>
      </span>
      <span v-else>
        还没有账号？
        <button @click="switchTab(true)" class="text-blue-600 font-semibold hover:underline cursor-pointer">
          去注册
        </button>
      </span>
    </div>

  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'AuthForm',
  props: {
    closeable: {
      type: Boolean,
      default: false
    },
    defaultRegister: {
      type: Boolean,
      default: false
    }
  },
  emits: ['submit', 'close'],
  setup(props, { emit }) {
    const isRegister = ref(props.defaultRegister)
    const username = ref("")
    const password = ref("")
    const showPassword = ref(false)
    const usernameTouched = ref(false)
    const passwordTouched = ref(false)
    const loading = ref(false)
    const errorMsg = ref("")

    // -------------------------------------------------------------------------
    // 校验规则 (正则表达式)
    // -------------------------------------------------------------------------
    // 用户名：长度 4-20，仅允许大小写字母、数字、下划线与连字符，且必须以字母或数字开头
    const USERNAME_REGEX = /^[a-zA-Z0-9][a-zA-Z0-9_-]{3,19}$/

    const isUsernameValid = computed(() => {
      return USERNAME_REGEX.test(username.value)
    })

    const usernameErrorMessage = computed(() => {
      if (!username.value) return "用户名不能为空"
      if (username.value.length < 4 || username.value.length > 20) return "长度需为 4 到 20 个字符"
      if (/^[^a-zA-Z0-9]/.test(username.value)) return "必须以字母或数字开头"
      return "只允许包含字母、数字、_ 与 -"
    })

    // 密码 4 大规则实时 Checklist
    const rulesPassed = computed(() => {
      const val = password.value
      return {
        length: val.length >= 8,
        case: /[a-z]/.test(val) && /[A-Z]/.test(val),
        number: /[0-9]/.test(val),
        special: /[@$!%*?&#^()_+\-=\[\]{};':"\\|,.<>\/?]/.test(val)
      }
    })

    const isPasswordValid = computed(() => {
      const r = rulesPassed.value
      return r.length && r.case && r.number && r.special
    })

    // 密码强度计算逻辑
    const strengthScore = computed(() => {
      const r = rulesPassed.value
      let score = 0
      if (r.length) score++
      if (r.case) score++
      if (r.number) score++
      if (r.special) score++
      return score
    })

    const strengthText = computed(() => {
      const score = strengthScore.value
      if (score <= 2) return "弱"
      if (score === 3) return "中"
      return "强"
    })

    const strengthColor = computed(() => {
      const score = strengthScore.value
      if (score <= 2) return "#ef4444" // 弱 = 红色
      if (score === 3) return "#f59e0b" // 中 = 黄色
      return "#10b981"                 // 强 = 绿色
    })

    const strengthBgClass = computed(() => {
      const score = strengthScore.value
      if (score <= 2) return "bg-rose-500"
      if (score === 3) return "bg-amber-500"
      return "bg-emerald-500"
    })

    // 表单提交按钮置灰禁用判断
    const isFormValid = computed(() => {
      return isUsernameValid.value && isPasswordValid.value
    })

    function switchTab(registerMode) {
      isRegister.value = registerMode
      errorMsg.value = ""
    }

    function handleSubmit() {
      if (!isFormValid.value || loading.value) return
      errorMsg.value = ""
      emit('submit', {
        isRegister: isRegister.value,
        username: username.value,
        password: password.value
      })
    }

    return {
      isRegister,
      username,
      password,
      showPassword,
      usernameTouched,
      passwordTouched,
      loading,
      errorMsg,
      isUsernameValid,
      usernameErrorMessage,
      rulesPassed,
      isPasswordValid,
      strengthScore,
      strengthText,
      strengthColor,
      strengthBgClass,
      isFormValid,
      switchTab,
      handleSubmit
    }
  }
}
</script>

<style scoped>
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-4px); }
  40%, 80% { transform: translateX(4px); }
}
.animate-shake {
  animation: shake 0.3s ease-in-out;
}
</style>
