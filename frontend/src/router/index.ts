import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
    },
    {
      path: '/chat/:characterId',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
      props: true,
    },
  ],
})

export default router
