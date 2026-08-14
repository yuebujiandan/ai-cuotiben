<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { Question } from '@/types'
import { reviewApi } from '@/api/review'
import RichText from '@/components/RichText.vue'

const router = useRouter()
const queue = ref<Question[]>([])
const index = ref(0)
const loading = ref(true)
const submitting = ref(false)
const showAnswer = ref(false)

// 统计
const doneCount = ref(0)
const stats = ref({ correct: 0, wrong: 0, skip: 0 })

const current = ref<Question | null>(null)

async function reload() {
  loading.value = true
  try {
    queue.value = await reviewApi.queue()
  } catch {
    queue.value = []
  } finally {
    loading.value = false
    current.value = queue.value[0] || null
  }
}

onMounted(reload)

async function submit(result: 'correct' | 'wrong' | 'skip') {
  if (!current.value || submitting.value) return
  submitting.value = true
  try {
    await reviewApi.submit(current.value.id, result)
    stats.value[result]++
    doneCount.value++
    index.value++
    showAnswer.value = false
    current.value = queue.value[index.value] || null
  } catch (e) {
    alert((e as Error).message || '提交失败')
  } finally {
    submitting.value = false
  }
}

function restart() {
  index.value = 0
  doneCount.value = 0
  stats.value = { correct: 0, wrong: 0, skip: 0 }
  reload()
}
</script>

<template>
  <div class="mx-auto max-w-[720px]">
    <div class="mb-5 flex items-center justify-between">
      <h2 class="text-xl">一键复习</h2>
      <span class="text-[13px] text-[#9A958A]">已完成 {{ doneCount }} / {{ queue.length }} 题</span>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="card-base animate-pulse p-6">
      <div class="h-4 w-1/3 rounded bg-paper-fill"></div>
      <div class="mt-4 h-32 rounded bg-paper-fill"></div>
    </div>

    <!-- 空队列 -->
    <div v-else-if="queue.length === 0" class="card-base rounded-card border border-dashed p-12 text-center text-[#9A958A]">
      <p class="mb-2 text-base text-[#3A3A35]">🎉 今日复习完成！</p>
      <p class="mb-6">当前没有待复习的错题（未掌握/待复习）</p>
      <button class="btn btn-secondary" @click="router.push('/bank')">返回错题集</button>
    </div>

    <!-- 完成页 -->
    <div v-else-if="!current" class="card-base rounded-card border border-dashed p-12 text-center">
      <p class="mb-2 text-base text-[#3A3A35]">✅ 本轮复习完成</p>
      <div class="mb-6 mt-4 flex justify-center gap-8 text-[13px] text-[#6B6659]">
        <span>答对 <b class="font-medium text-success">{{ stats.correct }}</b></span>
        <span>答错 <b class="font-medium text-error">{{ stats.wrong }}</b></span>
        <span>跳过 <b class="font-medium text-[#6B6659]">{{ stats.skip }}</b></span>
      </div>
      <div class="flex justify-center gap-2.5">
        <button class="btn btn-secondary" @click="restart">再复习一轮</button>
        <button class="btn btn-primary" @click="router.push('/bank')">返回错题集</button>
      </div>
    </div>

    <!-- 答题卡 -->
    <div v-else class="card-base p-6">
      <div class="mb-3 flex flex-wrap gap-2">
        <span class="tag tag-subject">{{ current.subject }}</span>
        <span v-if="current.knowledge_point" class="tag border border-[#E3DCCF] bg-paper-card text-[#6B6659]">{{ current.knowledge_point }}</span>
        <span class="text-xs text-[#9A958A]">第 {{ index + 1 }} / {{ queue.length }} 题</span>
      </div>

      <div class="mb-4 rounded-btn bg-paper-fill px-4 py-3 text-[15px] leading-7">
        <RichText :text="current.content" />
      </div>

      <div v-if="current.my_answer" class="mb-4 rounded-btn border border-[#E3DCCF] px-4 py-2.5 text-[13px]">
        <b class="font-medium text-[#6B6659]">我的答案：</b><RichText :text="current.my_answer" />
      </div>

      <div v-if="showAnswer" class="mb-4 rounded-btn border-l-[3px] border-l-success bg-success-bg px-4 py-3 text-[13px] leading-7">
        <b class="font-medium text-success">正确答案：</b><RichText :text="current.correct_answer || '—'" />
        <div v-if="current.ai_analysis" class="mt-2 text-[#6B6659]"><RichText :text="current.ai_analysis" /></div>
      </div>

      <button v-if="!showAnswer" class="mb-4 text-[12.5px] text-inkblue hover:underline" @click="showAnswer = true">查看答案与解析</button>

      <div class="flex flex-wrap justify-center gap-2.5 border-t border-[#E3DCCF] pt-4">
        <button class="btn btn-danger" :disabled="submitting" @click="submit('wrong')">✗ 答错了</button>
        <button class="btn btn-secondary" :disabled="submitting" @click="submit('skip')">跳过</button>
        <button class="btn btn-primary" :disabled="submitting" @click="submit('correct')">✓ 答对了</button>
      </div>
      <p class="mt-3 text-center text-[11.5px] text-[#9A958A]">连续答对 2 次 → 已掌握；答错 → 重新积累</p>
    </div>
  </div>
</template>
