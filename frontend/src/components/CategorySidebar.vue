<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { questionApi } from '@/api/questions'
import type { Category, Notebook } from '@/types'

const props = defineProps<{ modelValue: string; mobile?: boolean }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()

const categories = ref<Category[]>([{ name: 'all', count: 0 }])
const notebooks = ref<Notebook[]>([])
const loadingNb = ref(false)

async function load() {
  try {
    categories.value = await questionApi.categories()
  } catch {
    categories.value = [{ name: 'all', count: 0 }]
  }
  await loadNotebooks()
}

async function loadNotebooks() {
  loadingNb.value = true
  try {
    notebooks.value = await questionApi.notebooks()
  } catch {
    notebooks.value = []
  } finally {
    loadingNb.value = false
  }
}

onMounted(load)

const subjects = ref<Category[]>([])
const smartCats = ['all', '收藏夹', '复习计划']

function splitCategories() {
  subjects.value = categories.value.filter(
    (c) => c.name !== 'all' && c.name !== '收藏夹' && c.name !== '复习计划'
  )
}
// categories 变化后重算学科列表
watch(categories, splitCategories, { immediate: true })

function isActive(v: string) {
  return props.modelValue === v
}

function selectNotebook(nb: Notebook) {
  emit('update:modelValue', `notebook:${nb.id}`)
}
function selectSubject(c: Category) {
  emit('update:modelValue', `subject:${c.name}`)
}
function selectSmart(name: string) {
  emit('update:modelValue', name)
}

async function addNotebook() {
  const name = prompt('输入新错题本名称：')
  if (!name || !name.trim()) return
  try {
    const nb = await questionApi.createNotebook(name.trim())
    await loadNotebooks()
    // 新建后自动选中该错题本
    emit('update:modelValue', `notebook:${nb.id}`)
  } catch (e) {
    alert((e as Error).message || '创建错题本失败')
  }
}

async function removeNotebook(nb: Notebook, ev: Event) {
  ev.stopPropagation()
  if (!confirm(`确定删除错题本「${nb.name}」吗？其中的错题会保留并移出该本。`)) return
  try {
    await questionApi.deleteNotebook(nb.id)
    await loadNotebooks()
    if (props.modelValue === `notebook:${nb.id}`) {
      emit('update:modelValue', 'all')
    }
  } catch (e) {
    alert((e as Error).message || '删除失败')
  }
}
</script>

<template>
  <aside
    :class="mobile
      ? 'flex flex-col gap-4 p-4'
      : 'card-base hidden h-fit flex-col gap-4 p-4 lg:sticky lg:top-20 lg:flex'"
  >
    <!-- 错题本（持久化容器） -->
    <div>
      <div class="mb-2 flex items-center justify-between">
        <span class="text-xs font-medium tracking-widest text-[#9A958A]">错题本</span>
        <button
          class="flex h-6 w-6 items-center justify-center rounded-btn text-[#6B6659] transition-colors hover:bg-infobg hover:text-inkblue"
          title="新增错题本"
          @click="addNotebook"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </button>
      </div>
      <div class="flex flex-col gap-1">
        <button
          v-for="nb in notebooks"
          :key="nb.id"
          class="group flex items-center justify-between rounded-btn px-3 py-2 text-sm transition-colors"
          :class="isActive('notebook:' + nb.id) ? 'bg-infobg font-medium text-inkblue' : 'text-[#6B6659] hover:bg-infobg hover:text-inkblue'"
          @click="selectNotebook(nb)"
        >
          <span class="flex min-w-0 items-center gap-1.5 truncate">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" class="shrink-0 opacity-70"><path d="M4 5a2 2 0 0 1 2-2h6v18H6a2 2 0 0 1-2-2V5z"/><path d="M20 5a2 2 0 0 0-2-2h-6v18h6a2 2 0 0 0 2-2V5z"/></svg>
            <span class="truncate">{{ nb.name }}</span>
          </span>
          <span class="flex items-center gap-1.5">
            <span class="text-xs tabular-nums text-[#9A958A]">{{ nb.count }}</span>
            <svg
              width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              class="shrink-0 opacity-0 transition-opacity group-hover:opacity-100 hover:text-error"
              @click="removeNotebook(nb, $event)"
            ><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </span>
        </button>
        <p v-if="!loadingNb && notebooks.length === 0" class="px-3 py-1 text-xs text-[#9A958A]">
          还没有错题本，点右上角 + 新建
        </p>
      </div>
    </div>

    <!-- 智能筛选 -->
    <div>
      <div class="mb-2 text-xs font-medium tracking-widest text-[#9A958A]">智能</div>
      <div class="flex flex-col gap-1">
        <button
          v-for="name in smartCats"
          :key="name"
          class="flex items-center justify-between rounded-btn px-3 py-2 text-sm transition-colors"
          :class="isActive(name) ? 'bg-infobg font-medium text-inkblue' : 'text-[#6B6659] hover:bg-infobg hover:text-inkblue'"
          @click="selectSmart(name)"
        >
          <span>{{ name === 'all' ? '全部错题' : name }}</span>
          <span v-if="name === 'all'" class="text-xs tabular-nums text-[#9A958A]">{{ categories.find(c => c.name === 'all')?.count ?? 0 }}</span>
        </button>
      </div>
    </div>

    <!-- 学科 -->
    <div v-if="subjects.length">
      <div class="mb-2 text-xs font-medium tracking-widest text-[#9A958A]">学科</div>
      <div class="flex flex-col gap-1">
        <button
          v-for="c in subjects"
          :key="c.name"
          class="flex items-center justify-between rounded-btn px-3 py-2 text-sm transition-colors"
          :class="isActive('subject:' + c.name) ? 'bg-infobg font-medium text-inkblue' : 'text-[#6B6659] hover:bg-infobg hover:text-inkblue'"
          @click="selectSubject(c)"
        >
          <span>{{ c.name }}</span>
          <span class="text-xs tabular-nums text-[#9A958A]">{{ c.count }}</span>
        </button>
      </div>
    </div>
  </aside>
</template>
