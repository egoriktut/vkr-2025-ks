<script setup>

const props = defineProps({
  label: {
    type: String,
    default: "",
  }
})
</script>

<template>
  <label>
    <slot></slot>
  </label>

</template>

<style scoped>
label {
  font-family: Arial, Helvetica, sans-serif;
  margin-bottom: 10px;
  text-decoration: none;
}
</style>
