<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const navOpen = ref(false)

const navItems = [
  { path: '/home', label: '学习台' },
  { path: '/bank', label: '错题集' },
  { path: '/ai', label: 'AI答疑' },
  { path: '/dashboard', label: '数据看板' },
  { path: '/help', label: '帮助' }
]

function go(path: string) {
  navOpen.value = false
  router.push(path)
}
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-[#E3DCCF] bg-paper-card">
    <div class="mx-auto flex h-[60px] max-w-[1200px] items-center justify-between gap-4 px-6">
      <button
        class="flex h-9 w-9 items-center justify-center rounded-btn text-[#6B6659] transition-colors hover:bg-infobg hover:text-inkblue lg:hidden"
        aria-label="打开菜单"
        @click="navOpen = !navOpen"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
          <line x1="4" y1="7" x2="20" y2="7" /><line x1="4" y1="12" x2="20" y2="12" /><line x1="4" y1="17" x2="20" y2="17" />
        </svg>
      </button>

      <RouterLink to="/bank" class="flex items-center gap-2.5">
        <div class="flex h-[34px] w-[34px] items-center justify-center rounded-lg bg-inkblue text-[15px] font-medium tracking-wide text-[#FFFDF8]">R</div>
        <div>
          <div class="text-[16px] font-medium tracking-wide text-[#2B2B28]">Recall</div>
          <div class="text-[10.5px] tracking-wider text-[#9A958A]">AI 智能错题本</div>
        </div>
      </RouterLink>

      <nav class="hidden gap-0.5 rounded-btn bg-paper-fill p-[3px] lg:flex" aria-label="主导航">
        <button
          v-for="item in navItems"
          :key="item.path"
          class="rounded-btn px-[18px] py-[7px] text-[#6B6659] transition-all hover:text-inkblue"
          :class="route.path === item.path ? 'bg-inkblue text-[#FFFDF8]' : ''"
          @click="go(item.path)"
        >
          {{ item.label }}
        </button>
      </nav>

      <div class="flex items-center gap-3">
        <RouterLink
          to="/bank"
          class="flex h-9 w-9 items-center justify-center rounded-btn text-[#6B6659] transition-colors hover:bg-infobg hover:text-inkblue"
          aria-label="录入错题"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <path d="M4 7h11l3 3h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z" /><circle cx="12" cy="13" r="3" />
          </svg>
        </RouterLink>
        <div class="flex h-8 w-8 items-center justify-center rounded-full bg-inkblue text-xs font-medium text-[#FFFDF8]">同</div>
      </div>
    </div>

    <nav
      v-show="navOpen"
      class="flex flex-col gap-1 border-t border-[#E3DCCF] bg-paper-card px-6 py-3 lg:hidden"
      aria-label="移动端导航"
    >
      <button
        v-for="item in navItems"
        :key="item.path"
        class="rounded-btn px-4 py-2.5 text-left text-[#6B6659]"
        :class="route.path === item.path ? 'bg-inkblue text-[#FFFDF8]' : ''"
        @click="go(item.path)"
      >
        {{ item.label }}
      </button>
    </nav>
  </header>
</template>
