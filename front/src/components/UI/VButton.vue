<script setup>

const props = defineProps({
  label: {
    default: "",
    type: String,
  },
})

import Button from "primevue/button";
</script>

<template>
  <Button :label="label" severity="contrast" size="small" style="margin-bottom: 10px"/>
</template>

<style scoped>

</style>
