<template>
  <Toolbar style="border-radius: 1rem; padding: 1rem 1rem 1rem 1.5rem">
    <template #start>
      <div class="flex items-center gap-2">
        <RouterLink to="/KS" style="text-decoration: none;">
          <VLabel
            class="nav-label"
            :class="{ 'active-tab': route.path === '/KS' }"
          >
            Катировочные сессии
          </VLabel>
        </RouterLink>

        <RouterLink to="/account" style="text-decoration: none;">
          <VLabel
              class="nav-label"
              :class="{ 'active-tab': route.path === '/account' }"
          >
            Личный кабинет
          </VLabel>
        </RouterLink>

      </div>
    </template>

    <template #end>
      <div class="flex items-center gap-2">
        <label class="nav-label" @click="logout">Выйти</label>
      </div>
    </template>
  </Toolbar>
</template>

<script setup>
import {useRoute} from 'vue-router';
import Toolbar from 'primevue/toolbar';
import router from '@/router/router.js';
import {useAuth} from "@/stores/auth.js";
import VLabel from "@/components/UI/VLabel.vue";

const auth = useAuth();
const route = useRoute();

const logout = () => {
  auth.logout();
  router.push('/login');
};
</script>

<style scoped>
.nav-label {
  cursor: pointer;
  padding: 0.5rem;
  color: #42b983;
  font-size: 1rem;
}

.active-tab {
  border-bottom: 4px solid ;
}

</style>
