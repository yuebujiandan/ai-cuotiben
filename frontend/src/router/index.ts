import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/home' },
    { path: '/home', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { title: '学习台' } },
    { path: '/bank', name: 'bank', component: () => import('@/views/BankView.vue'), meta: { title: '错题集' } },
    { path: '/review', name: 'review', component: () => import('@/views/ReviewView.vue'), meta: { title: '一键复习' } },
    { path: '/ai', name: 'ai', component: () => import('@/views/AiTutorView.vue'), meta: { title: 'AI答疑' } },
    { path: '/dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue'), meta: { title: '数据看板' } },
    { path: '/help', name: 'help', component: () => import('@/views/HelpView.vue'), meta: { title: '帮助' } }
  ]
})

router.afterEach((to) => {
  document.title = to.meta.title ? `Recall · ${to.meta.title}` : 'Recall'
})

export default router
