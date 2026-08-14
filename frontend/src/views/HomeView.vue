<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { questionApi } from '@/api/questions'
import { dashboardApi } from '@/api/dashboard'
import type { Question } from '@/types'
import QuestionCard from '@/components/QuestionCard.vue'
import DetailModal from '@/components/DetailModal.vue'

const router = useRouter()
const stats = ref<{ total: number; mastered: number; reviewing: number; pending: number; mastery_rate: number } | null>(null)
const recent = ref<Question[]>([])
const loading = ref(true)

const detailQ = ref<Question | null>(null)
const detailEdit = ref(false)

function openDetail(q: Question) {
  detailQ.value = q
  detailEdit.value = false
}

async function reload() {
  loading.value = true
  try {
    const [s, list] = await Promise.all([dashboardApi.stats(), questionApi.list({})])
    stats.value = s
    recent.value = list.slice(0, 5)
  } catch {
    /* 静默 */
  } finally {
    loading.value = false
  }
}

onMounted(reload)
</script>

<template>
  <div>
    <div class="mb-5 flex items-baseline gap-3">
      <h2 class="text-xl">学习台</h2>
      <span class="text-[13px] text-[#9A958A]">今日复习任务与最近错题</span>
    </div>

    <!-- 概览四卡 -->
    <div class="mb-5 grid grid-cols-2 gap-3.5 lg:grid-cols-4">
      <div class="card-base p-4">
        <div class="mb-1.5 text-xs text-[#9A958A]">错题总数</div>
        <div class="text-[28px] font-medium tabular-nums leading-tight text-[#2B2B28]">{{ stats?.total ?? '-' }}</div>
      </div>
      <div class="card-base p-4">
        <div class="mb-1.5 text-xs text-[#9A958A]">已掌握</div>
        <div class="text-[28px] font-medium tabular-nums leading-tight text-success">{{ stats?.mastered ?? '-' }}</div>
      </div>
      <div class="card-base p-4">
        <div class="mb-1.5 text-xs text-[#9A958A]">待复习</div>
        <div class="text-[28px] font-medium tabular-nums leading-tight text-warn">{{ stats?.reviewing ?? '-' }}</div>
      </div>
      <div class="card-base p-4">
        <div class="mb-1.5 text-xs text-[#9A958A]">掌握率</div>
        <div class="text-[28px] font-medium tabular-nums leading-tight text-[#2B2B28]">{{ stats?.mastery_rate ?? '-' }}%</div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="mb-5 grid grid-cols-2 gap-3.5 lg:grid-cols-4">
      <button class="card-base p-4 text-left transition-all hover:shadow-paper" @click="router.push('/bank')">
        <div class="mb-1.5 text-[13px] font-medium text-inkblue">录入错题</div>
        <div class="text-[12px] text-[#9A958A]">拍照 / 截图 / 手动输入，AI 自动归类</div>
      </button>
      <button class="card-base p-4 text-left transition-all hover:shadow-paper" @click="router.push('/ai')">
        <div class="mb-1.5 text-[13px] font-medium text-inkblue">AI 答疑</div>
        <div class="text-[12px] text-[#9A958A]">随时提问，流式讲解错题</div>
      </button>
      <button class="card-base p-4 text-left transition-all hover:shadow-paper" @click="router.push('/bank')">
        <div class="mb-1.5 text-[13px] font-medium text-inkblue">复习计划</div>
        <div class="text-[12px] text-[#9A958A]">按掌握度安排复习（建设中）</div>
      </button>
      <button class="card-base p-4 text-left transition-all hover:shadow-paper" @click="router.push('/dashboard')">
        <div class="mb-1.5 text-[13px] font-medium text-inkblue">数据看板</div>
        <div class="text-[12px] text-[#9A958A]">学习趋势与薄弱点分析</div>
      </button>
    </div>

    <!-- 最近错题 -->
    <div class="mb-3 flex items-baseline justify-between">
      <h3 class="text-[15px]">最近错题</h3>
      <button class="text-[13px] text-inkblue hover:underline" @click="router.push('/bank')">查看全部 →</button>
    </div>

    <div v-if="loading" class="card-base animate-pulse p-4">
      <div class="h-4 w-1/3 rounded bg-paper-fill"></div>
    </div>
    <div v-else-if="recent.length === 0" class="card-base rounded-card border border-dashed p-10 text-center text-[#9A958A]">
      <p class="mb-4">还没有错题，先录入第一道吧</p>
      <button class="btn btn-primary" @click="router.push('/bank')">去录入错题</button>
    </div>
    <template v-else>
      <QuestionCard v-for="q in recent" :key="q.id" :question="q" @open="openDetail" />
    </template>
  </div>

  <DetailModal
    v-if="detailQ"
    :question="detailQ"
    :initial-edit="detailEdit"
    @close="detailQ = null"
    @updated="(q) => { detailQ = q }"
    @deleted="() => { detailQ = null; reload() }"
    @ask-ai="(q) => { detailQ = null; router.push({ path: '/ai', query: { q: q.content, id: String(q.id) } }) }"
  />
</template>
