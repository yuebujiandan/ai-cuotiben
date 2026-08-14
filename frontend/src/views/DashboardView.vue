<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { dashboardApi } from '@/api/dashboard'
import type { DashboardStats, DailyStat } from '@/types'

const stats = ref<DashboardStats | null>(null)
const daily = ref<DailyStat[]>([])
const loading = ref(true)

const kpis = ref<{ label: string; value: string; delta: string; tone: 'ok' | 'warn' }[]>([
  { label: '题目总数', value: '-', delta: '', tone: 'ok' },
  { label: '已掌握', value: '-', delta: '', tone: 'ok' },
  { label: '待复习', value: '-', delta: '', tone: 'warn' },
  { label: '连续学习', value: '-', delta: '', tone: 'ok' }
])

function computeKpis(s: DashboardStats) {
  kpis.value = [
    { label: '题目总数', value: String(s.total), delta: `掌握率 ${s.mastery_rate}%`, tone: 'ok' },
    { label: '已掌握', value: String(s.mastered), delta: '掌握率 ' + s.mastery_rate + '%', tone: 'ok' },
    { label: '待复习', value: String(s.reviewing), delta: `今日复习 ${s.review_today} 次`, tone: 'warn' },
    { label: '连续学习', value: String(s.streak_days ?? 0), delta: '连续复习天数', tone: 'ok' }
  ]
}

function maxBar() {
  return Math.max(...daily.value.map((d) => Math.max(d.total, d.review)), 1)
}

// 状态占比（三色环形图：绿=已掌握 / 琥珀=待复习 / 红=未掌握）
function donutGradient() {
  const s = stats.value
  if (!s) return 'conic-gradient(#F4F0E8 0 100%)'
  const total = Math.max(s.total, 1)
  const g = Math.round((s.mastered / total) * 100)
  const a = Math.round((s.reviewing / total) * 100)
  const pct = [g, a, Math.max(100 - g - a, 0)]
  let acc = 0
  const stops = pct.map((v, i) => {
    const from = acc
    acc += v
    const color = i === 0 ? '#3A7D5C' : i === 1 ? '#D9822B' : '#C0392B'
    return `${color} ${from}% ${acc}%`
  })
  return `conic-gradient(${stops.join(', ')})`
}

onMounted(async () => {
  loading.value = true
  try {
    const [s, d] = await Promise.all([dashboardApi.stats(), dashboardApi.daily()])
    stats.value = s
    daily.value = d
    computeKpis(s)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <div class="mb-5 flex items-baseline gap-3">
      <h2 class="text-xl">数据看板</h2>
      <span class="text-[13px] text-[#9A958A]">你的错题学习数据总览</span>
    </div>

    <div class="mb-5 grid grid-cols-2 gap-3.5 lg:grid-cols-4">
      <div
        v-for="k in kpis"
        :key="k.label"
        class="card-base p-4 transition-transform hover:-translate-y-0.5 hover:shadow-paper"
      >
        <div class="mb-1.5 text-xs text-[#9A958A]">{{ k.label }}</div>
        <div class="text-[28px] font-medium tabular-nums leading-tight text-[#2B2B28]">{{ k.value }}</div>
        <div class="mt-1 text-xs" :class="k.tone === 'ok' ? 'text-success' : 'text-warn'">{{ k.delta }}</div>
      </div>
    </div>

    <div v-if="loading" class="card-base animate-pulse p-4">
      <div class="h-4 w-1/4 rounded bg-paper-fill"></div>
      <div class="mt-4 h-40 rounded bg-paper-fill"></div>
    </div>

    <div v-else class="grid grid-cols-1 gap-3.5 xl:grid-cols-3">
      <div class="card-base p-4 xl:col-span-2">
        <div class="mb-3 flex items-center justify-between">
          <h3 class="text-[15px]">最近十天做题情况</h3>
          <div class="flex gap-3 text-xs text-[#6B6659]">
            <span><i class="mr-1 inline-block h-2.5 w-2.5 rounded-[3px] bg-inkblue"></i>新增错题</span>
            <span><i class="mr-1 inline-block h-2.5 w-2.5 rounded-[3px] bg-success"></i>复习次数</span>
          </div>
        </div>
        <div class="flex h-[200px] items-end gap-1.5 border-b border-[#E3DCCF] pt-2">
          <div v-for="(d, i) in daily" :key="i" class="flex flex-1 flex-col items-center gap-2" :title="`${d.date}：新增 ${d.total}，复习 ${d.review} 次（正确 ${d.correct}）`">
            <div class="flex h-[165px] items-end gap-0.5">
              <div class="w-2.5 rounded-t-[3px] bg-inkblue transition-all hover:bg-warn" :style="{ height: (d.total / maxBar()) * 150 + 'px' }"></div>
              <div class="w-2.5 rounded-t-[3px] bg-success transition-all" :style="{ height: (d.review / maxBar()) * 150 + 'px' }"></div>
            </div>
            <span class="text-[10.5px] text-[#9A958A]">{{ d.date.slice(5) }}</span>
          </div>
        </div>
      </div>

      <div class="card-base p-4">
        <div class="mb-3 flex items-center justify-between">
          <h3 class="text-[15px]">掌握状态占比</h3>
          <span class="rounded-pill bg-warn-bg px-2 py-0.5 text-[10px] font-medium tracking-wider text-warn">AI</span>
        </div>
        <div class="flex items-center justify-center gap-7 py-2">
          <div
            class="relative flex h-[130px] w-[130px] items-center justify-center rounded-full"
            :style="{ background: donutGradient() }"
          >
            <div class="absolute inset-[22px] rounded-full bg-paper-card"></div>
            <div class="relative z-[1] text-center">
              <div class="text-2xl font-medium tabular-nums leading-tight">{{ stats ? stats.mastery_rate + '%' : '-' }}</div>
              <div class="text-[11px] text-[#9A958A]">已掌握</div>
            </div>
          </div>
          <div class="flex flex-col gap-2.5 text-[13px] text-[#6B6659]">
            <div class="flex items-center gap-2">
              <i class="h-2.5 w-2.5 rounded-[3px] bg-success"></i>
              已掌握 <b class="ml-auto pl-4 font-medium tabular-nums text-[#2B2B28]">{{ stats?.mastered ?? '-' }}</b>
            </div>
            <div class="flex items-center gap-2">
              <i class="h-2.5 w-2.5 rounded-[3px] bg-warn"></i>
              待复习 <b class="ml-auto pl-4 font-medium tabular-nums text-[#2B2B28]">{{ stats?.reviewing ?? '-' }}</b>
            </div>
            <div class="flex items-center gap-2">
              <i class="h-2.5 w-2.5 rounded-[3px] bg-error"></i>
              未掌握 <b class="ml-auto pl-4 font-medium tabular-nums text-[#2B2B28]">{{ stats?.pending ?? '-' }}</b>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
