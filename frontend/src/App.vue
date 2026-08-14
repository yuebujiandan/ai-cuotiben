<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue'
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <AppHeader />
    <main class="mx-auto w-full max-w-[1200px] flex-1 px-6 pb-12 pt-6">
      <RouterView />
    </main>
  </div>
</template>
