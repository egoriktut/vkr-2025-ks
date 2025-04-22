<script setup>
import NavBar from '@/components/NavBar.vue'
import router from '@/router/router.js'
import { onMounted } from 'vue'


const authChecker = () => {
  const token = localStorage.getItem('token')
  if (!token) {
    router.push("/login")
  }
}

onMounted(() => {
  authChecker()
})
</script>

<template>
  <nav-bar />
  <div class="body-component">
    <slot></slot>
  </div>
</template>

<style scoped>
.body-component {
  border-radius: 1rem;
  padding: 1rem;
  background: white;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  flex: 1;
  margin: 1rem 0rem;
  min-height: 100vh;
  display: flex;
  align-items: center;
  flex-direction: column;
}
.body-component > ::v-deep * {
  width: 100%;
}
</style>
