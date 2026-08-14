<script setup lang="ts">
import { computed } from 'vue'
import type { Question } from '@/types'
import RichText from '@/components/RichText.vue'

const props = defineProps<{ question: Question }>()
const emit = defineEmits<{
  (e: 'open', q: Question): void
  (e: 'analyze', q: Question): void
  (e: 'edit', q: Question): void
  (e: 'delete', id: number): void
}>()

const statusMeta = computed(() => {
  switch (props.question.status) {
    case 'green':
      return { label: '已掌握', cls: 'tag-green' }
    case 'amber':
      return { label: '待复习', cls: 'tag-amber' }
    default:
      return { label: '未掌握', cls: 'tag-red' }
  }
})

const borderCls = computed(() => {
  const s = props.question.status
  return s === 'green' ? 'border-l-success' : s === 'amber' ? 'border-l-warn' : 'border-l-error'
})
</script>

<template>
  <article
    class="card-base flex cursor-pointer flex-col gap-4 border-l-[3px] p-4 transition-all hover:border-inkblue hover:shadow-paper sm:flex-row"
    :class="borderCls"
    @click="emit('open', question)"
  >
    <div class="min-w-0 flex-1">
      <div class="mb-2.5 flex flex-wrap gap-2">
        <span class="tag tag-subject">{{ question.subject }}</span>
        <span class="tag border border-[#E3DCCF] bg-paper-card text-[#6B6659]">{{ question.knowledge_point }}</span>
        <span class="tag" :class="statusMeta.cls">{{ statusMeta.label }}</span>
        <span v-if="question.is_favorite" class="tag tag-amber">收藏</span>
      </div>

      <p class="mb-2.5 text-sm leading-7 text-[#3A3A35]"><RichText :text="question.content" /></p>

      <div v-if="question.ai_analysis" class="mt-2.5 rounded-btn border-l-[3px] border-l-success bg-success-bg px-3.5 py-2.5 text-[13px] text-[#6B6659]">
        <b class="font-medium text-success">AI 解析</b> · <RichText :text="question.ai_analysis" />
      </div>

      <div v-if="question.correct_answer" class="mt-2 rounded-btn border-l-[3px] border-l-success bg-success-bg px-3.5 py-2 text-[13px]">
        <b class="font-medium text-success">正确答案</b> · <RichText :text="question.correct_answer" />
      </div>

      <div class="mt-2.5 flex items-center gap-3 text-xs text-[#9A958A]">
        <span>来源：{{ question.source }}</span>
        <span class="tabular-nums">复习 {{ question.review_count }} 次</span>
      </div>
    </div>

    <div class="flex shrink-0 flex-row flex-wrap gap-2 sm:flex-col sm:justify-center" @click.stop>
      <button class="btn btn-secondary btn-sm" @click="emit('analyze', question)">AI 解析</button>
      <button class="btn btn-secondary btn-sm" @click="emit('edit', question)">编辑</button>
      <button class="btn btn-danger btn-sm" @click="emit('delete', question.id)">删除</button>
    </div>
  </article>
</template>
