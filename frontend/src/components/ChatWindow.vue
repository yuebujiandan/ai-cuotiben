<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import type { ChatMessage } from '@/types'
import { chatApi } from '@/api/chat'
import { questionApi } from '@/api/questions'
import RichText from '@/components/RichText.vue'

const props = defineProps<{
  conversationId?: number
  initialQuestion?: string
  /** 从错题卡片跳转携带的题目上下文（与 conversationId 相互独立，不再把会话 ID 当题目 ID 用） */
  questionContext?: string
}>()
const emit = defineEmits<{ (e: 'conversation-change', id: number): void }>()

const messages = ref<ChatMessage[]>([])
const input = ref('')
const sending = ref(false)
const bodyRef = ref<HTMLElement | null>(null)

// 3 级讲解：key = 消息索引，value = 各级状态 {loading, content}
type LevelState = { loading: boolean; content: string; error?: string }
const explainState = ref<Record<number, Partial<Record<'hint' | 'approach' | 'solution', LevelState>>>>({})
// 引用到错题本：key = 消息索引
const citeOpen = ref<Record<number, boolean>>({})
const citeForm = ref<{ subject: string; knowledge_point: string }>({ subject: '数学', knowledge_point: '' })
const citeSaving = ref(false)
const citeMsg = ref('')

const quickQuestions = [
  '二次函数的对称轴怎么求？',
  '这道题为什么错了？帮我分析错因',
  '推荐几道二次函数的同类题'
]

const explainLabels: Record<'hint' | 'approach' | 'solution', string> = {
  hint: '💡 提示',
  approach: '🧭 思路',
  solution: '📖 详解'
}

async function loadHistory(id?: number) {
  if (!id) {
    messages.value = []
    return
  }
  try {
    messages.value = await chatApi.history(id)
  } catch {
    messages.value = []
  }
  explainState.value = {}
  citeOpen.value = {}
  scrollBottom()
}

async function send(text?: string) {
  const q = (text ?? input.value).trim()
  if (!q || sending.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: q })
  sending.value = true
  scrollBottom()
  try {
    const convId = await chatApi.sendStream(
      q,
      props.questionContext || '',
      (partial) => {
        const last = messages.value[messages.value.length - 1]
        if (last && last.role === 'assistant') last.content = partial
        else messages.value.push({ role: 'assistant', content: partial })
        scrollBottom()
      },
      props.conversationId
    )
    // 新建会话时后端回传会话 ID，通知父组件刷新列表并高亮
    if (convId && convId !== props.conversationId) {
      emit('conversation-change', convId)
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: (e as Error).message || 'AI 暂时无法响应，请稍后再试。' })
  } finally {
    sending.value = false
    scrollBottom()
  }
}

// ===== 3 级讲解 =====
async function loadExplain(msgIndex: number, question: string, level: 'hint' | 'approach' | 'solution') {
  if (explainState.value[msgIndex]?.[level]?.content) return  // 已加载过
  explainState.value[msgIndex] = {
    ...(explainState.value[msgIndex] || {}),
    [level]: { loading: true, content: '' }
  }
  try {
    const res = await chatApi.explain(question, level)
    explainState.value[msgIndex] = {
      ...(explainState.value[msgIndex] || {}),
      [level]: { loading: false, content: res.content }
    }
    scrollBottom()
  } catch (e) {
    explainState.value[msgIndex] = {
      ...(explainState.value[msgIndex] || {}),
      [level]: { loading: false, content: '', error: (e as Error).message || '生成失败' }
    }
  }
}

// ===== 引用到错题本 =====
function openCite(msgIndex: number, question: string) {
  citeMsg.value = question.slice(0, 200)
  citeForm.value = { subject: '数学', knowledge_point: '' }
  citeOpen.value = { [msgIndex]: true }
}

async function submitCite(msgIndex: number) {
  citeSaving.value = true
  try {
    await questionApi.create({
      content: citeMsg.value,
      subject: citeForm.value.subject,
      knowledge_point: citeForm.value.knowledge_point || undefined,
      source: 'AI 对话引用'
    })
    citeOpen.value = { ...citeOpen.value, [msgIndex]: false }
    alert('已引用到错题本')
  } catch (e) {
    alert((e as Error).message || '引用失败')
  } finally {
    citeSaving.value = false
  }
}

function scrollBottom() {
  requestAnimationFrame(() => {
    if (bodyRef.value) bodyRef.value.scrollTop = bodyRef.value.scrollHeight
  })
}

// 切换 / 新建会话时重新加载对应历史（或清空）
watch(
  () => props.conversationId,
  (id) => loadHistory(id)
)

onMounted(() => {
  loadHistory(props.conversationId)
  if (props.initialQuestion) {
    setTimeout(() => send(props.initialQuestion), 300)
  }
})
</script>

<template>
  <div class="card-base flex h-full min-h-0 flex-col overflow-hidden">
    <div class="flex items-center justify-between border-b border-[#E3DCCF] px-5 py-3.5">
      <div class="flex items-center gap-2.5">
        <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-inkblue text-[13px] font-medium text-[#FFFDF8]">AI</div>
        <div>
          <h2 class="text-[15px] text-[#2B2B28]">Recall 学伴</h2>
          <div class="text-xs text-[#9A958A]">随时为你讲解错题</div>
        </div>
      </div>
      <span v-if="questionContext" class="rounded-pill bg-infobg px-3 py-1 text-xs text-inkblue">来自错题卡片</span>
      <span v-else-if="conversationId" class="rounded-pill bg-infobg px-3 py-1 text-xs text-inkblue">会话 #{{ conversationId }}</span>
    </div>

    <div ref="bodyRef" class="flex-1 overflow-y-auto px-5 py-5">
      <div class="mb-1 rounded-modal border border-dashed border-[#D8D2C2] bg-paper-fill px-4 py-3.5 text-center text-[13px] text-[#6B6659]">
        你好，我是 <b class="font-medium text-inkblue">Recall 学伴</b>，可以为你讲解错题、解答疑问、推荐同类题。
      </div>

      <div
        v-for="(m, i) in messages"
        :key="i"
        class="mb-3.5 max-w-[85%]"
        :class="m.role === 'user' ? 'ml-auto' : ''"
      >
        <div
          class="rounded-modal px-4 py-2.5 text-sm leading-7"
          :class="m.role === 'user' ? 'rounded-tr-btn bg-inkblue text-[#FFFDF8]' : 'rounded-tl-btn border border-[#E3DCCF] bg-paper-bg text-[#3A3A35]'"
        >
          <RichText :text="m.content" />
        </div>

        <!-- AI 消息操作：3级讲解 + 引用到错题本 -->
        <div v-if="m.role === 'assistant'" class="mt-1.5 flex flex-wrap items-center gap-1.5 px-1">
          <template v-for="level in (['hint', 'approach', 'solution'] as const)" :key="level">
            <button
              class="rounded-pill bg-infobg px-2.5 py-1 text-[11.5px] text-inkblue transition-colors hover:bg-inkblue hover:text-[#FFFDF8]"
              :disabled="explainState[i]?.[level]?.loading"
              @click="loadExplain(i, m.content, level)"
            >
              {{ explainState[i]?.[level]?.loading ? '生成中…' : explainLabels[level] }}
            </button>
            <div v-if="explainState[i]?.[level]?.content" class="w-full rounded-btn border-l-[3px] border-l-success bg-success-bg px-3 py-2 text-[12.5px] leading-6 text-[#3A3A35]">
              <RichText :text="explainState[i]![level]!.content" />
            </div>
            <p v-if="explainState[i]?.[level]?.error" class="w-full text-[11.5px] text-error">{{ explainState[i]![level]!.error }}</p>
          </template>
          <button
            class="rounded-pill border border-[#D8D2C2] px-2.5 py-1 text-[11.5px] text-[#6B6659] transition-colors hover:border-inkblue hover:text-inkblue"
            @click="openCite(i, m.content)"
          >
            📥 引用到错题本
          </button>
        </div>

        <!-- 引用表单 -->
        <div v-if="citeOpen[i]" class="mt-2 rounded-btn border border-[#E3DCCF] bg-paper-card p-3">
          <div class="mb-2 text-[12px] text-[#6B6659]">引用这道讲解为错题：</div>
          <textarea v-model="citeMsg" rows="3" class="input-base mb-2 w-full resize-none py-2 text-[12.5px]"></textarea>
          <div class="flex gap-2">
            <select v-model="citeForm.subject" class="input-base w-1/3 text-[12.5px]">
              <option>数学</option><option>物理</option><option>化学</option><option>英语</option><option>语文</option><option>生物</option>
            </select>
            <input v-model="citeForm.knowledge_point" type="text" placeholder="知识点（可选）" class="input-base flex-1 text-[12.5px]" />
          </div>
          <div class="mt-2 flex justify-end gap-2">
            <button class="btn btn-secondary btn-sm" @click="citeOpen = { ...citeOpen, [i]: false }">取消</button>
            <button class="btn btn-primary btn-sm" :disabled="citeSaving" @click="submitCite(i)">{{ citeSaving ? '引用中…' : '确认引用' }}</button>
          </div>
        </div>
      </div>

      <div v-if="sending" class="max-w-[78%] rounded-modal rounded-tl-btn border border-[#E3DCCF] bg-paper-bg px-4 py-2.5 text-sm text-[#9A958A]">
        正在思考<span class="inline-block w-1 animate-pulse">…</span>
      </div>
    </div>

    <div class="flex flex-wrap gap-2 px-5 pb-3">
      <button
        v-for="q in quickQuestions"
        :key="q"
        class="rounded-pill bg-infobg px-3.5 py-1.5 text-[12.5px] text-inkblue transition-colors hover:bg-inkblue hover:text-[#FFFDF8]"
        @click="send(q)"
      >
        {{ q }}
      </button>
    </div>

    <div class="flex items-end gap-2.5 border-t border-[#E3DCCF] bg-paper-fill px-5 py-3.5">
      <textarea
        v-model="input"
        rows="1"
        placeholder="输入你的问题… Enter 发送，Shift+Enter 换行"
        class="input-base max-h-[120px] min-h-[40px] flex-1 resize-none py-2.5"
        @keydown.enter.exact.prevent="send()"
      ></textarea>
      <button class="flex h-11 w-11 shrink-0 items-center justify-center rounded-btn bg-inkblue text-[#FFFDF8] transition-colors hover:bg-inkblue-hover active:scale-[0.92]" aria-label="发送" :disabled="sending" @click="send()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
  </div>
</template>
