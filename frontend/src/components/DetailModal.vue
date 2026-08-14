<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Question } from '@/types'
import { questionApi } from '@/api/questions'
import RichText from '@/components/RichText.vue'

const props = defineProps<{ question: Question; initialEdit?: boolean }>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'updated', q: Question): void
  (e: 'deleted', id: number): void
  (e: 'ask-ai', q: Question): void
}>()

const editing = ref(!!props.initialEdit)
const saving = ref(false)
const analyzing = ref(false)
const errorMsg = ref('')

// 编辑表单（与 props.question 分离，取消/保存互不影响）
const form = ref({
  subject: props.question.subject || '数学',
  knowledge_point: props.question.knowledge_point || '',
  content: props.question.content || '',
  my_answer: props.question.my_answer || '',
  correct_answer: props.question.correct_answer || '',
  source: props.question.source || ''
})

const subjects = ['数学', '物理', '化学', '英语', '语文', '生物']

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

async function save() {
  if (!form.value.content.trim()) {
    errorMsg.value = '题目内容不能为空'
    return
  }
  saving.value = true
  errorMsg.value = ''
  try {
    const updated = await questionApi.update(props.question.id, {
      subject: form.value.subject,
      knowledge_point: form.value.knowledge_point,
      content: form.value.content,
      my_answer: form.value.my_answer || undefined,
      correct_answer: form.value.correct_answer || undefined,
      source: form.value.source
    })
    editing.value = false
    emit('updated', updated)
  } catch (e) {
    errorMsg.value = (e as Error).message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function reAnalyze() {
  analyzing.value = true
  errorMsg.value = ''
  try {
    const updated = await questionApi.analyze(props.question.id)
    emit('updated', updated)
  } catch (e) {
    errorMsg.value = (e as Error).message || 'AI 分析失败'
  } finally {
    analyzing.value = false
  }
}

async function toggleFavorite() {
  try {
    const updated = await questionApi.update(props.question.id, {
      is_favorite: !props.question.is_favorite
    })
    emit('updated', updated)
  } catch (e) {
    errorMsg.value = (e as Error).message || '操作失败'
  }
}

function remove() {
  if (!confirm('确定删除这道错题吗？删除后不可恢复。')) return
  questionApi.remove(props.question.id).then(() => emit('deleted', props.question.id))
}

function cancelEdit() {
  editing.value = false
  errorMsg.value = ''
}
</script>

<template>
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-[#2B3A67]/30 p-5" @click.self="emit('close')">
    <div class="card-base flex max-h-[90vh] w-full max-w-[680px] flex-col rounded-modal shadow-lg">
      <div class="flex items-center justify-between border-b border-[#E3DCCF] px-6 py-4">
        <h3 class="text-lg text-[#2B2B28]">{{ editing ? '编辑错题' : '错题详情' }}</h3>
        <button class="flex h-9 w-9 items-center justify-center rounded-btn text-[#6B6659] hover:bg-infobg hover:text-inkblue" aria-label="关闭" @click="emit('close')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto px-6 py-4">
        <!-- ===== 编辑模式 ===== -->
        <div v-if="editing" class="flex flex-col gap-3.5">
          <div>
            <label class="mb-1.5 block text-[12.5px] font-medium text-[#6B6659]">学科</label>
            <select v-model="form.subject" class="input-base w-full">
              <option v-for="s in subjects" :key="s">{{ s }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1.5 block text-[12.5px] font-medium text-[#6B6659]">知识点</label>
            <input v-model="form.knowledge_point" type="text" class="input-base w-full" placeholder="如：二次函数顶点坐标" />
          </div>
          <div>
            <label class="mb-1.5 block text-[12.5px] font-medium text-[#6B6659]">题目内容</label>
            <textarea v-model="form.content" rows="4" class="input-base w-full resize-none py-2.5" placeholder="支持 LaTeX，如 \(x^2+1\)"></textarea>
          </div>
          <div>
            <label class="mb-1.5 block text-[12.5px] font-medium text-[#6B6659]">我的答案</label>
            <textarea v-model="form.my_answer" rows="2" class="input-base w-full resize-none py-2.5"></textarea>
          </div>
          <div>
            <label class="mb-1.5 block text-[12.5px] font-medium text-[#6B6659]">正确答案</label>
            <textarea v-model="form.correct_answer" rows="2" class="input-base w-full resize-none py-2.5"></textarea>
          </div>
          <div>
            <label class="mb-1.5 block text-[12.5px] font-medium text-[#6B6659]">来源</label>
            <input v-model="form.source" type="text" class="input-base w-full" placeholder="如：期中试卷" />
          </div>
          <p v-if="errorMsg" class="text-[12px] text-error">{{ errorMsg }}</p>
          <p class="text-[11.5px] text-[#9A958A]">保存后可点击「重新 AI 分析」让 AI 重新归类与诊断（手动修改的字段将保留）。</p>
        </div>

        <!-- ===== 只读详情模式 ===== -->
        <div v-else class="flex flex-col gap-4">
          <div class="flex flex-wrap gap-2">
            <span class="tag tag-subject">{{ question.subject }}</span>
            <span v-if="question.knowledge_point" class="tag border border-[#E3DCCF] bg-paper-card text-[#6B6659]">{{ question.knowledge_point }}</span>
            <span class="tag" :class="statusMeta.cls">{{ statusMeta.label }}</span>
            <span v-if="question.is_favorite" class="tag tag-amber">收藏</span>
          </div>

          <div>
            <div class="mb-1.5 text-[12.5px] font-medium text-[#6B6659]">题目</div>
            <div class="rounded-btn bg-paper-fill px-4 py-3 text-sm leading-7"><RichText :text="question.content" /></div>
          </div>

          <div v-if="question.my_answer" class="grid gap-4 sm:grid-cols-2">
            <div>
              <div class="mb-1.5 text-[12.5px] font-medium text-[#6B6659]">我的答案</div>
              <div class="rounded-btn border border-[#E3DCCF] px-4 py-2.5 text-[13px]"><RichText :text="question.my_answer" /></div>
            </div>
            <div>
              <div class="mb-1.5 text-[12.5px] font-medium text-[#6B6659]">正确答案</div>
              <div class="rounded-btn border border-[#E3DCCF] px-4 py-2.5 text-[13px]"><RichText :text="question.correct_answer || '—'" /></div>
            </div>
          </div>

          <div v-if="question.ai_analysis">
            <div class="mb-1.5 text-[12.5px] font-medium text-success">AI 解析</div>
            <div class="rounded-btn border-l-[3px] border-l-success bg-success-bg px-4 py-3 text-[13px] leading-7"><RichText :text="question.ai_analysis" /></div>
          </div>

          <div class="flex items-center gap-4 text-xs text-[#9A958A]">
            <span>来源：{{ question.source || '—' }}</span>
            <span class="tabular-nums">复习 {{ question.review_count }} 次</span>
            <span>录入 {{ new Date(question.created_at).toLocaleDateString('zh-CN') }}</span>
          </div>
          <p v-if="errorMsg" class="text-[12px] text-error">{{ errorMsg }}</p>
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-2.5 border-t border-[#E3DCCF] px-6 py-4">
        <div class="flex flex-wrap gap-2">
          <button class="btn btn-secondary btn-sm" @click="toggleFavorite">{{ question.is_favorite ? '取消收藏' : '收藏' }}</button>
          <button class="btn btn-secondary btn-sm" :disabled="analyzing" @click="reAnalyze">
            {{ analyzing ? 'AI 分析中…' : '重新 AI 分析' }}
          </button>
          <button class="btn btn-secondary btn-sm" @click="emit('ask-ai', question)">AI 答疑</button>
          <button class="btn btn-danger btn-sm" @click="remove">删除</button>
        </div>
        <div class="flex gap-2.5">
          <button v-if="editing" class="btn btn-secondary btn-sm" @click="cancelEdit">取消</button>
          <button v-if="!editing" class="btn btn-secondary btn-sm" @click="editing = true">编辑</button>
          <button v-if="editing" class="btn btn-primary btn-sm" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
