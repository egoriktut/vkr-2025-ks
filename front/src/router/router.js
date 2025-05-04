import { createRouter, createWebHistory } from 'vue-router'
import KS from "@/components/KS.vue";
import Login from "@/components/Login.vue";
import Account from "@/components/Account.vue";

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
      path: '/account',
      name: 'account',
      component: Account,
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'redirect',
      redirect: () => {
        return {path: '/login'}
      },
    },
  ],
})

export default router
