<script setup lang="ts">
import { ref } from 'vue'
import type { Question } from '@/types'

const props = defineProps<{
  questions: Question[]
  /** 当前列表筛选参数（PDF 按筛选导出用） */
  scopeParams?: { subject?: string; status?: string; keyword?: string; notebook_id?: number }
}>()
const emit = defineEmits<{ (e: 'close'): void }>()

const scope = ref<'all' | 'filtered'>('all')
const format = ref<'pdf' | 'md'>('pdf')
const withAnalysis = ref(true)
const withMyAnswer = ref(false)
const exporting = ref(false)
const errorMsg = ref('')

function buildPdfUrl(): string {
  const p = props.scopeParams || {}
  const params = new URLSearchParams()
  if (scope.value === 'filtered') {
    if (p.subject) params.set('subject', p.subject)
    if (p.status) params.set('status', p.status)
    if (p.keyword) params.set('keyword', p.keyword)
    if (p.notebook_id) params.set('notebook_id', String(p.notebook_id))
  }
  const qs = params.toString()
  return '/api/dashboard/export' + (qs ? '?' + qs : '')
}

function exportMarkdown() {
  const list = scope.value === 'all' ? props.questions : props.questions
  if (!list.length) {
    errorMsg.value = '没有可导出的错题'
    return
  }
  const lines: string[] = [`# Recall 错题集导出（${new Date().toLocaleDateString('zh-CN')}）`, '']
  list.forEach((q, i) => {
    lines.push(`## ${i + 1}. [${q.subject}] ${q.knowledge_point || '未分类'}`)
    lines.push('')
    lines.push(`**题目**：${q.content}`)
    if (withMyAnswer.value && q.my_answer) lines.push(`**我的解答**：${q.my_answer}`)
    if (q.correct_answer) lines.push(`**正确答案**：${q.correct_answer}`)
    if (withAnalysis.value && q.ai_analysis) lines.push(`**AI 解析**：${q.ai_analysis}`)
    lines.push('---')
    lines.push('')
  })
  const blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/markdown;charset=utf-8' })
  downloadBlob(blob, `recall-错题-${new Date().toISOString().slice(0, 10)}.md`)
  emit('close')
}

function exportPdf() {
  exporting.value = true
  errorMsg.value = ''
  const url = buildPdfUrl()
  // 用 fetch 先探测状态，404（无数据）时给出友好提示
  fetch(url)
    .then((res) => {
      if (!res.ok) throw new Error(res.status === 404 ? '当前范围没有可导出的错题' : '导出失败，请稍后再试')
      return res.blob()
    })
    .then((blob) => {
      downloadBlob(blob, `recall-错题-${new Date().toISOString().slice(0, 10)}.pdf`)
      emit('close')
    })
    .catch((e) => {
      errorMsg.value = (e as Error).message || '导出失败'
    })
    .finally(() => {
      exporting.value = false
    })
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function doExport() {
  errorMsg.value = ''
  if (format.value === 'md') exportMarkdown()
  else exportPdf()
}
</script>

<template>
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-[#2B3A67]/30 p-5" @click.self="emit('close')">
    <div class="card-base w-full max-w-[440px] rounded-modal shadow-lg">
      <div class="flex items-center justify-between border-b border-[#E3DCCF] px-6 py-4">
        <h3 class="text-lg text-[#2B2B28]">导出错题</h3>
        <button class="flex h-9 w-9 items-center justify-center rounded-btn text-[#6B6659] hover:bg-infobg hover:text-inkblue" aria-label="关闭" @click="emit('close')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <div class="flex flex-col gap-4 px-6 py-5">
        <div>
          <div class="mb-1.5 text-[12.5px] font-medium text-[#6B6659]">导出范围</div>
          <div class="flex gap-2">
            <button class="flex-1 rounded-btn border px-3 py-2 text-[13px] transition-colors" :class="scope === 'all' ? 'border-inkblue bg-infobg text-inkblue' : 'border-[#D8D2C2] text-[#6B6659]'" @click="scope = 'all'">全部错题</button>
            <button class="flex-1 rounded-btn border px-3 py-2 text-[13px] transition-colors" :class="scope === 'filtered' ? 'border-inkblue bg-infobg text-inkblue' : 'border-[#D8D2C2] text-[#6B6659]'" @click="scope = 'filtered'">当前筛选结果</button>
          </div>
        </div>

        <div>
          <div class="mb-1.5 text-[12.5px] font-medium text-[#6B6659]">导出格式</div>
          <div class="flex gap-2">
            <button class="flex-1 rounded-btn border px-3 py-2 text-[13px] transition-colors" :class="format === 'pdf' ? 'border-inkblue bg-infobg text-inkblue' : 'border-[#D8D2C2] text-[#6B6659]'" @click="format = 'pdf'">PDF</button>
            <button class="flex-1 rounded-btn border px-3 py-2 text-[13px] transition-colors" :class="format === 'md' ? 'border-inkblue bg-infobg text-inkblue' : 'border-[#D8D2C2] text-[#6B6659]'" @click="format = 'md'">Markdown</button>
          </div>
        </div>

        <div class="flex flex-col gap-2 text-[13px] text-[#3A3A35]">
          <label class="flex cursor-pointer items-center gap-2.5">
            <input v-model="withAnalysis" type="checkbox" class="h-4 w-4 accent-[#2B3A67]" />
            包含 AI 解析
          </label>
          <label class="flex cursor-pointer items-center gap-2.5">
            <input v-model="withMyAnswer" type="checkbox" class="h-4 w-4 accent-[#2B3A67]" />
            包含我的解答 <span class="text-[11px] text-[#9A958A]">（默认关，保护隐私）</span>
          </label>
        </div>

        <p v-if="errorMsg" class="text-[12px] text-error">{{ errorMsg }}</p>
      </div>

      <div class="flex justify-end gap-2.5 border-t border-[#E3DCCF] px-6 py-4">
        <button class="btn btn-secondary btn-sm" @click="emit('close')">取消</button>
        <button class="btn btn-primary btn-sm" :disabled="exporting" @click="doExport">
          {{ exporting ? '导出中…' : '开始导出' }}
        </button>
      </div>
    </div>
  </div>
</template>
