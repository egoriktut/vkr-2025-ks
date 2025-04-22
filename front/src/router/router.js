import { createRouter, createWebHistory } from 'vue-router'
import KS from "@/components/KS.vue";
import Login from "@/components/Login.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login,
    },
    {
      path: '/KS',
      name: 'KS',
      component: KS,
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'redirect',
      redirect: () => {
        return {path: '/KS'}
      },
    },
  ],
})

export default router
