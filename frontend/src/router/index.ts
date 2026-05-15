import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/auth',
      name: 'auth',
      component: () => import('@/views/AuthView.vue'),
    },
    {
      path: '/chat/:characterId',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
      props: true,
      meta: { requiresAuth: true },
    },
    {
      path: '/character/:characterId/edit',
      name: 'characterEdit',
      component: () => import('@/views/CharacterEditView.vue'),
      props: true,
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  if (to.path === '/auth') {
    // 已登录用户访问登录页 → 跳回首页
    if (token) return '/'
    return true
  }
  // 其他页面需要 token
  if (!token) return '/auth'
  return true
})

export default router
