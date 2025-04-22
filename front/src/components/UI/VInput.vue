<script setup>

import InputText from "primevue/inputtext";
import FloatLabel from "primevue/floatlabel";
import {computed} from "vue";
import Password from "primevue/password";

const props = defineProps({
  label: {
    type: String,
    default: "",
  },
  modelValue: {
    type: String,
    default: "",
  },
  type: {
    type: String,
    default: "input",
  },
  disabled: {
    type: Boolean,
    default: false,
  }
})

const value = computed({
  get: () => props.modelValue,
  set: (newValue) => {
    emit("update:modelValue", newValue);
  },
});
const emit = defineEmits(["update:modelValue"]);
</script>

<template>
  <div style="margin-bottom: 10px">
    <FloatLabel v-if="type === 'input'" variant="on" >
      <label for="on_label">{{ label }}</label>
      <InputText
        v-model="value"
        inputId="on_label"
        class="full-width"
        :disabled="disabled"
      />
    </FloatLabel>
    <FloatLabel v-else variant="on">
      <Password
        v-model="value"
        :feedback="false"
        required
        toggleMask
        type="submit"
        :invalid="false"
        inputId="on_label"
        :disabled="disabled"
      />
      <label for="inputId">Пароль</label>
    </FloatLabel>
  </div>
</template>

<style scoped>
.full-width {
  width: 254px;
}
</style>
