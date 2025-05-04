<template>
  <BodyComponent>
    <div class="account-container">
      <h2 class="account-title">Личный кабинет</h2>

      <div class="account-card">
        <form @submit.prevent="handleSubmit" class="account-form">
          <div class="form-group">
            <label for="email">Email</label>
            <InputText
                id="email"
                v-model="userData.email"
                disabled
                class="disabled-input full-width"
            />
          </div>

          <div class="form-row">
            <div class="form-group full-width">
              <label for="firstName">Имя</label>
              <InputText
                  id="firstName"
                  v-model="userData.first_name"
                  placeholder="Введите ваше имя"
                  class="full-width"
              />
            </div>

            <div class="form-group full-width">
              <label for="lastName">Фамилия</label>
              <InputText
                  id="lastName"
                  v-model="userData.last_name"
                  placeholder="Введите вашу фамилию"
                  class="full-width"
              />
            </div>
          </div>

          <div class="form-footer">
            <Button
                label="Сохранить изменения"
                type="submit"
                severity="contrast"
                class="full-width"
                :loading="isSubmitting"
            />
          </div>
        </form>

        <div class="account-meta full-width">
          <div class="meta-item">
            <span class="meta-label">Дата регистрации:</span>
            <span class="meta-value">{{ formatDate(userData.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </BodyComponent>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import BodyComponent from "@/components/BodyComponent.vue";
import { getData, putData } from "@/api/api.js";

// Данные пользователя
const userData = ref({
  email: null,
  first_name: null,
  last_name: null,
  created_at: null,
});

const isSubmitting = ref(false);

// Загрузка данных пользователя
onMounted(() => {
  getData('user/account').then(response => {
    console.log(response);
    userData.value = response;
  });
});

const formatDate = (dateString) => {
  const options = {year: 'numeric', month: 'long', day: 'numeric'};
  return new Date(dateString).toLocaleDateString('ru-RU', options);
};

const handleSubmit = async () => {
  isSubmitting.value = true;

  try {
    await putData('user/account', {
      first_name: userData.value.first_name,
      last_name: userData.value.last_name
    });

    alert('Данные успешно обновлены');
  } catch (error) {
    console.error('Ошибка при обновлении данных:', error);
    alert('Не удалось обновить данные');
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.account-container {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 2rem;
  box-sizing: border-box;
}

.account-title {
  color: var(--primary-color);
  text-align: center;
  margin-bottom: 2rem;
  font-size: 1.8rem;
  width: 100%;
}

.account-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 2rem;
  width: 100%;
  box-sizing: border-box;
}

.account-form {
  margin-bottom: 2rem;
  width: 100%;
}

.form-row {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  width: 100%;
}

.form-group {
  margin-bottom: 1.5rem;
  width: 100%;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--surface-700);
  width: 100%;
}

.disabled-input {
  background-color: var(--surface-100) !important;
  color: var(--surface-600) !important;
  cursor: not-allowed;
}

.full-width {
  width: 100%;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 2rem;
  width: 100%;
}

.account-meta {
  padding-top: 1.5rem;
  border-top: 1px solid var(--surface-100);
  width: 100%;
}

.meta-item {
  display: flex;
  margin-bottom: 0.5rem;
  width: 100%;
}

.meta-label {
  font-weight: 500;
  color: var(--surface-600);
  margin-right: 0.5rem;
}

.meta-value {
  color: var(--surface-700);
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    gap: 1rem;
  }

  .account-container {
    padding: 1rem;
  }

  .account-card {
    padding: 1.5rem;
  }
}
</style>