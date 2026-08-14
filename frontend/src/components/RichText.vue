<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps<{ text: string; display?: boolean }>()

const root = ref<HTMLElement | null>(null)

/**
 * 将包含 LaTeX/markdown 的混合文本渲染到 DOM。
 * - `\(...\)` 和 `\[...\]`：行内/块级数学
 * - 普通文本：保留换行和 HTML 转义
 */
function renderMixed(text: string): string {
  if (!text) return ''
  // 先转义 HTML
  let safe = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')

  // 替换 \[...\] 块级数学（display=true）
  safe = safe.replace(/\\\[([\s\S]*?)\\\]/g, (_, tex) => {
    try { return katex.renderToString(tex.trim(), { displayMode: true, throwOnError: false }) }
    catch { return `<code>${tex}</code>` }
  })
  // 替换 \(...\) 行内数学
  safe = safe.replace(/\\\(([\s\S]*?)\\\)/g, (_, tex) => {
    try { return katex.renderToString(tex.trim(), { displayMode: false, throwOnError: false }) }
    catch { return `<code>${tex}</code>` }
  })
  return safe
}

const html = computed(() => renderMixed(props.text))

// 题目预览场景下，检测是否含 LaTeX（用于显示/隐藏"包含公式"标签）
const hasLatex = computed(() => /\\\(.+?\\\)|\\\[[\s\S]+?\\\]|\$[^$]+\$/.test(props.text || ''))

watch(html, () => {
  if (root.value) root.value.innerHTML = html.value
}, { immediate: true })
onMounted(() => { if (root.value) root.value.innerHTML = html.value })

defineExpose({ hasLatex })
</script>

<template>
  <span ref="root" class="katex-wrap break-words"></span>
</template>