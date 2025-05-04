<template>
  <div v-if="store.isOpen" class="modal-overlay" @click.self="store.closeModal">
    <div class="modal-content">
      <h2>Ошибка</h2>
      <p>{{ store.errorMessage }}</p>
      <Button label="Закрыть" @click="store.closeModal" severity="contrast" class="full-width" />
    </div>
  </div>
</template>

<script setup>
import { useErrorModalStore } from '@/stores/errorModal';
import Button from "primevue/button";

const store = useErrorModalStore();
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  max-width: 500px;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
</style>