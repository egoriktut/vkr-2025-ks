<script setup>
import { RouterView } from 'vue-router'
import ModalError from '@/components/ModalError.vue';
</script>

<template>
  <RouterView />
  <ModalError />
</template>

<style>
h2 {
  font-family: Arial, Helvetica, sans-serif;
}
.custom-card {
  -webkit-box-shadow: 3px 0px 64px -1px rgba(34, 60, 80, 0.27);
  -moz-box-shadow: 3px 0px 64px -1px rgba(34, 60, 80, 0.27);
  box-shadow: 3px 0px 64px -1px rgba(34, 60, 80, 0.27);
  border-radius: 1.5rem;
  margin-bottom: 1rem;
}
</style>
