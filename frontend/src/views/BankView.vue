<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { questionApi } from '@/api/questions'
import type { Question } from '@/types'
import CategorySidebar from '@/components/CategorySidebar.vue'
import DetailModal from '@/components/DetailModal.vue'
import ExportModal from '@/components/ExportModal.vue'
import QuestionCard from '@/components/QuestionCard.vue'
import UploadModal from '@/components/UploadModal.vue'

const router = useRouter()
const questions = ref<Question[]>([])
const loading = ref(true)
const category = ref('all')
const keyword = ref('')
const statusFilter = ref('all')
const showUpload = ref(false)

// 详情/编辑弹窗
const detailQ = ref<Question | null>(null)
const detailEdit = ref(false)

function openDetail(q: Question, edit = false) {
  detailQ.value = q
  detailEdit.value = edit
}

function onDetailUpdated(q: Question) {
  // 同步列表中的对应记录
  const idx = questions.value.findIndex((x) => x.id === q.id)
  if (idx >= 0) questions.value[idx] = q
  detailQ.value = q
}

function onDetailDeleted(id: number) {
  questions.value = questions.value.filter((x) => x.id !== id)
  detailQ.value = null
}

function onAskAi(q: Question) {
  detailQ.value = null
  router.push({ path: '/ai', query: { q: q.content, id: String(q.id) } })
}

const statusPills = [
  { value: 'all', label: '全部' },
  { value: 'red', label: '未掌握' },
  { value: 'amber', label: '待复习' },
  { value: 'green', label: '已掌握' }
]

async function load(showSkeleton = true) {
  // showSkeleton=false：轮询静默刷新——不切骨架屏、不整体替换数组，避免列表滚动位置丢失
  if (showSkeleton) loading.value = true
  try {
    const params: {
      category?: string
      status?: string
      keyword?: string
      notebook_id?: number
    } = {
      status: statusFilter.value === 'all' ? undefined : statusFilter.value,
      keyword: keyword.value || undefined
    }
    const cat = category.value
    if (cat.startsWith('notebook:')) {
      params.notebook_id = Number(cat.slice('notebook:'.length))
    } else if (cat.startsWith('subject:')) {
      params.category = cat.slice('subject:'.length)
    } else if (cat !== 'all') {
      params.category = cat
    }
    const list = await questionApi.list(params)
    mergeQuestions(list)
  } catch (e) {
    questions.value = []
    alert((e as Error).message)
  } finally {
    if (showSkeleton) loading.value = false
  }
}

/**
 * 增量合并列表：相同 id 的题目复用旧对象引用（Object.assign 原位更新字段），
 * 避免 v-for 因整体替换数组而卸载/重建 DOM 导致滚动位置丢失。
 */
function mergeQuestions(list: Question[]) {
  const byId = new Map(questions.value.map((q) => [q.id, q]))
  const merged = list.map((nq) => {
    const old = byId.get(nq.id)
    if (old) {
      Object.assign(old, nq) // 响应式更新字段，保持同一对象引用
      return old
    }
    return nq
  })
  questions.value = merged
}

// 当前选中的错题本 ID（用于新建题目时归属）
const activeNotebookId = ref<number | undefined>(undefined)
watch(
  category,
  (v) => {
    activeNotebookId.value = v.startsWith('notebook:')
      ? Number(v.slice('notebook:'.length))
      : undefined
  },
  { immediate: true }
)

// 侧边栏标题按选择令牌显示
const titleText = ref('全部错题')
watch(
  [category],
  (v) => {
    const cat = v[0]
    if (cat.startsWith('notebook:')) {
      const nb = notebooksCache.value.find((n) => `notebook:${n.id}` === cat)
      titleText.value = nb ? nb.name : '错题本'
    } else if (cat.startsWith('subject:')) {
      titleText.value = cat.slice('subject:'.length)
    } else if (cat === 'all') {
      titleText.value = '全部错题'
    } else {
      titleText.value = cat
    }
  },
  { immediate: true }
)

// 用于标题显示错题本名称
const notebooksCache = ref<{ id: number; name: string }[]>([])
questionApi.notebooks().then((list) => (notebooksCache.value = list)).catch(() => {})

watch([category, statusFilter], () => load())
watch(keyword, () => setTimeout(load, 300))

function remove(id: number) {
  if (!confirm('确定删除这道错题吗？')) return
  questionApi.remove(id).then(() => {
    questions.value = questions.value.filter((q) => q.id !== id)
  })
}

function analyze(q: Question) {
  router.push({ path: '/ai', query: { q: q.content, id: String(q.id) } })
}

function onCreated() {
  showUpload.value = false
  load()
}

// 轮询：若存在"AI 解析中…"的记录，每 10s 自动刷新，让解析结果自动浮现
// 最多轮询 12 次（2 分钟），避免后台任务失败时无限等待
let pollTimer: ReturnType<typeof setInterval> | null = null
let pollCount = 0
const POLL_MAX = 12 // 12 次 × 10s = 2 分钟

function startPolling() {
  if (pollTimer) return
  pollCount = 0
  pollTimer = setInterval(() => {
    pollCount++
    if (questions.value.some((q) => q.ai_analysis?.includes('AI 解析中'))) {
      load(false) // 静默刷新：不切骨架屏、增量合并，保持滚动位置
    }
    if (pollCount >= POLL_MAX) stopPolling()
  }, 10000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function exportPdf() {
  showExport.value = true
}

// 当前筛选参数（导出弹窗按筛选范围导出用）
function currentScopeParams() {
  const cat = category.value
  let subject: string | undefined
  let notebook_id: number | undefined
  if (cat.startsWith('notebook:')) notebook_id = Number(cat.slice('notebook:'.length))
  else if (cat.startsWith('subject:')) subject = cat.slice('subject:'.length)
  else if (cat !== 'all' && cat !== '收藏夹' && cat !== '复习计划') subject = cat
  return {
    subject,
    status: statusFilter.value === 'all' ? undefined : statusFilter.value,
    keyword: keyword.value || undefined,
    notebook_id
  }
}

const showExport = ref(false)
const mobileFilterOpen = ref(false)

function editQuestion(q: Question) {
  openDetail(q, true)
}

onMounted(() => {
  load()
  startPolling()
})
onUnmounted(stopPolling)
</script>

<template>
  <div class="grid grid-cols-1 items-start gap-6 lg:grid-cols-[216px_1fr]">
    <CategorySidebar v-model="category" />

    <div class="min-w-0">
      <div class="mb-5 flex flex-wrap items-center gap-2">
        <button
          class="btn btn-secondary btn-sm lg:hidden"
          aria-label="打开筛选"
          @click="mobileFilterOpen = true"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M7 12h10"/><path d="M10 18h4"/></svg>
          筛选
        </button>
        <div class="relative min-w-[180px] flex-1">
          <svg class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#9A958A]" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <circle cx="11" cy="11" r="7" /><line x1="21" y1="21" x2="16.5" y2="16.5" />
          </svg>
          <input v-model="keyword" type="text" placeholder="搜索错题、知识点…" aria-label="搜索错题" class="input-base w-full pl-9" />
        </div>
        <div class="flex gap-1">
          <button
            v-for="p in statusPills"
            :key="p.value"
            class="rounded-pill px-3.5 py-1.5 text-[13px] transition-colors"
            :class="statusFilter === p.value ? 'bg-inkblue text-[#FFFDF8]' : 'text-[#6B6659] hover:bg-infobg hover:text-inkblue'"
            @click="statusFilter = p.value"
          >
            {{ p.label }}
          </button>
        </div>
      </div>

      <div class="mb-4 flex flex-wrap items-center gap-2">
        <button class="btn btn-primary btn-sm" @click="router.push('/review')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="M8 11l4 4 4-4"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>
          开始复习
        </button>
        <button class="btn btn-secondary btn-sm" @click="exportPdf">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 3v12"/><path d="M8 11l4 4 4-4"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>
          导出
        </button>
        <button class="btn btn-secondary btn-sm" @click="showUpload = true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 7h11l3 3h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z"/><circle cx="12" cy="13" r="3"/></svg>
          录入错题
        </button>
      </div>

      <div class="mb-4 flex items-baseline justify-between">
        <h2 class="text-lg">{{ titleText }}</h2>
        <span class="text-[13px] text-[#9A958A]">共 {{ questions.length }} 题</span>
      </div>

      <div v-if="loading" class="space-y-4">
        <div v-for="i in 3" :key="i" class="card-base animate-pulse p-4">
          <div class="mb-2 h-4 w-1/3 rounded bg-paper-fill"></div>
          <div class="h-4 w-4/5 rounded bg-paper-fill"></div>
          <div class="mt-2 h-4 w-2/3 rounded bg-paper-fill"></div>
        </div>
      </div>

      <div v-else-if="questions.length === 0" class="card-base rounded-card border border-dashed p-12 text-center text-[#9A958A]">
        <p class="mb-4">没有符合条件的错题</p>
        <button class="btn btn-primary" @click="showUpload = true">录入一道错题</button>
      </div>

      <template v-else>
        <QuestionCard
          v-for="q in questions"
          :key="q.id"
          :question="q"
          @open="(qq) => openDetail(qq)"
          @analyze="analyze"
          @delete="remove"
          @edit="editQuestion"
        />
      </template>
    </div>
  </div>

  <UploadModal v-if="showUpload" :notebook-id="activeNotebookId" @close="showUpload = false" @created="onCreated" />
  <ExportModal
    v-if="showExport"
    :questions="questions"
    :scope-params="currentScopeParams()"
    @close="showExport = false"
  />
  <DetailModal
    v-if="detailQ"
    :question="detailQ"
    :initial-edit="detailEdit"
    @close="detailQ = null"
    @updated="onDetailUpdated"
    @deleted="onDetailDeleted"
    @ask-ai="onAskAi"
  />

  <!-- 移动端筛选抽屉（错题本/学科/智能） -->
  <div
    v-if="mobileFilterOpen"
    class="fixed inset-0 z-[90] bg-[#2B3A67]/30 lg:hidden"
    @click.self="mobileFilterOpen = false"
  >
    <div class="absolute inset-y-0 left-0 flex w-[280px] max-w-[85vw] flex-col bg-paper-card shadow-lg">
      <div class="flex items-center justify-between border-b border-[#E3DCCF] px-5 py-3.5">
        <span class="text-[15px] font-medium text-[#2B2B28]">筛选</span>
        <button class="flex h-9 w-9 items-center justify-center rounded-btn text-[#6B6659] hover:bg-infobg hover:text-inkblue" aria-label="关闭筛选" @click="mobileFilterOpen = false">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div class="flex-1 overflow-y-auto">
        <CategorySidebar v-model="category" mobile @update:model-value="mobileFilterOpen = false" />
      </div>
    </div>
  </div>
</template>
