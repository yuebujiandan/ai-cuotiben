<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { chatApi } from '@/api/chat'
import type { AIConversation } from '@/types'
import ChatWindow from '@/components/ChatWindow.vue'

const route = useRoute()
const conversations = ref<AIConversation[]>([])
const activeId = ref<number | undefined>(undefined)
const pendingQuestion = ref('')
// 从错题卡片跳转时携带的题目上下文（问题 ID 是题目 ID，与会话 ID 是两套序列，不能混用）
const questionContext = ref('')
// 移动端历史抽屉
const mobileHistoryOpen = ref(false)

async function loadList() {
  try {
    conversations.value = await chatApi.list()
  } catch {
    conversations.value = []
  }
}

function newChat() {
  activeId.value = undefined
  pendingQuestion.value = ''
}

function onConversationChange(id: number) {
  activeId.value = id
  loadList()
}

function selectMobile(c: AIConversation) {
  activeId.value = c.id
  mobileHistoryOpen.value = false
}

onMounted(() => {
  loadList()
  const q = route.query.q as string | undefined
  const id = route.query.id as string | undefined
  if (q) pendingQuestion.value = q
  // 注意：query.id 是「题目 ID」，仅作为上下文标识，不能当会话 ID 使用，
  // 否则会把题目 ID 误当 conversation_id 导致 404 或加载错历史。
  if (id) questionContext.value = `当前错题上下文：题目 #${id}`
})
</script>

<template>
  <div class="grid h-[calc(100dvh-150px)] min-h-[500px] grid-cols-1 items-start gap-6 lg:grid-cols-[216px_1fr]">
    <aside class="card-base hidden h-full flex-col p-4 lg:flex">
      <div class="mb-3 text-xs font-medium tracking-widest text-[#9A958A]">对话历史</div>
      <button class="mb-3 flex w-full items-center justify-center gap-1.5 rounded-btn border-[1.5px] border-dashed border-[#D8D2C2] py-2.5 text-[13px] text-inkblue transition-colors hover:border-inkblue hover:bg-infobg" @click="newChat">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新建对话
      </button>

      <button
        class="flex items-center justify-between rounded-btn px-3 py-2 text-sm transition-colors"
        :class="activeId === undefined ? 'bg-infobg font-medium text-inkblue' : 'text-[#6B6659] hover:bg-infobg hover:text-inkblue'"
        @click="newChat"
      >
        <span>新对话</span>
      </button>

      <button
        v-for="c in conversations"
        :key="c.id"
        class="flex items-center justify-between rounded-btn px-3 py-2 text-sm transition-colors"
        :class="activeId === c.id ? 'bg-infobg font-medium text-inkblue' : 'text-[#6B6659] hover:bg-infobg hover:text-inkblue'"
        @click="activeId = c.id"
      >
        <span class="truncate">{{ c.title }}</span>
      </button>
    </aside>

    <div class="flex h-full min-h-0 flex-col gap-2.5">
      <!-- 移动端：历史抽屉入口 -->
      <button
        class="flex w-fit items-center gap-1 rounded-btn border border-[#E3DCCF] bg-paper-card px-3 py-1.5 text-[12.5px] text-inkblue lg:hidden"
        aria-label="打开对话历史"
        @click="mobileHistoryOpen = true"
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        对话历史
      </button>

      <ChatWindow
        :conversation-id="activeId"
        :initial-question="pendingQuestion"
        :question-context="questionContext"
        @conversation-change="onConversationChange"
      />
    </div>
  </div>

  <!-- 移动端历史抽屉 -->
  <div
    v-if="mobileHistoryOpen"
    class="fixed inset-0 z-[90] bg-[#2B3A67]/30 lg:hidden"
    @click.self="mobileHistoryOpen = false"
  >
    <div class="absolute inset-y-0 left-0 flex w-[280px] max-w-[85vw] flex-col bg-paper-card shadow-lg">
      <div class="flex items-center justify-between border-b border-[#E3DCCF] px-5 py-3.5">
        <span class="text-[15px] font-medium text-[#2B2B28]">对话历史</span>
        <button class="flex h-9 w-9 items-center justify-center rounded-btn text-[#6B6659] hover:bg-infobg hover:text-inkblue" aria-label="关闭历史" @click="mobileHistoryOpen = false">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-4">
        <button class="mb-2 flex w-full items-center justify-center gap-1.5 rounded-btn border-[1.5px] border-dashed border-[#D8D2C2] py-2.5 text-[13px] text-inkblue" @click="newChat; mobileHistoryOpen = false">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          新建对话
        </button>
        <button
          class="mb-1 flex w-full items-center rounded-btn px-3 py-2 text-sm transition-colors"
          :class="activeId === undefined ? 'bg-infobg font-medium text-inkblue' : 'text-[#6B6659] hover:bg-infobg'"
          @click="newChat; mobileHistoryOpen = false"
        >
          新对话
        </button>
        <button
          v-for="c in conversations"
          :key="c.id"
          class="mb-1 flex w-full items-center rounded-btn px-3 py-2 text-sm transition-colors"
          :class="activeId === c.id ? 'bg-infobg font-medium text-inkblue' : 'text-[#6B6659] hover:bg-infobg'"
          @click="selectMobile(c)"
        >
          <span class="truncate">{{ c.title }}</span>
        </button>
        <p v-if="conversations.length === 0" class="px-3 py-2 text-xs text-[#9A958A]">暂无历史对话</p>
      </div>
    </div>
  </div>
</template>
