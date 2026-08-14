<script setup lang="ts">
const items = [
  { no: '1', title: '如何录入错题？', desc: '点击顶部相机按钮或「录入错题」，拍照 / 粘贴截图 / 手动输入，AI 自动识别题目并归类。' },
  { no: '2', title: 'AI 解析怎么用？', desc: '每道错题卡片上的「AI 解析」会给出错因诊断、解题步骤和知识点标签。' },
  { no: '3', title: '如何开始复习？', desc: '点击「开始复习」进入逐题刷题流，系统按掌握度自动安排复习顺序。' },
  { no: '4', title: '数据看板看什么？', desc: '掌握率、错因分布、近十天做题趋势，以及 AI 为你推荐的薄弱知识点。' }
]
</script>

<template>
  <div>
    <div class="mb-5 flex items-baseline gap-3">
      <h2 class="text-xl">帮助中心</h2>
      <span class="text-[13px] text-[#9A958A]">快速上手 Recall</span>
    </div>

    <div class="grid grid-cols-1 gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
      <div v-for="item in items" :key="item.no" class="card-base p-5 transition-transform hover:-translate-y-0.5 hover:shadow-paper">
        <div class="mb-3 flex h-9 w-9 items-center justify-center rounded-btn bg-infobg text-base font-medium text-inkblue">{{ item.no }}</div>
        <h3 class="mb-1.5 text-[14.5px]">{{ item.title }}</h3>
        <p class="text-[13px] leading-7 text-[#6B6659]">{{ item.desc }}</p>
      </div>
    </div>
  </div>
</template>
