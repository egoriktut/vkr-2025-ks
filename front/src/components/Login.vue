<template>
  <div class="login-container">
    <Card>
      <template #content>
        <form @submit.prevent="onSubmit" class="login-form">
          <h2 style="display: flex; justify-content: center; text-align: center; white-space: pre-wrap;">
            Портал автоматического мониторинга котировочных сессий
          </h2>

          <!-- Ввод email всегда -->
          <FloatLabel variant="on" v-if="step !== 'code'">
            <label for="email">Email</label>
            <InputText
                v-model="username"
                required
                :invalid="errorValid"
                inputId="email"
                class="full-width"
            />
          </FloatLabel>

          <!-- Вход -->
          <template v-if="step === 'login'">
            <FloatLabel variant="on">
              <Password
                  v-model="password"
                  :feedback="false"
                  required
                  toggleMask
                  inputId="password"
                  :invalid="errorValid"
              />
              <label for="password">Пароль</label>
            </FloatLabel>

            <Button label="Войти" type="submit" severity="contrast" class="full-width" />
            <label class="registration-label" @click="step = 'register'">
              Регистрация
            </label>
            <label class="registration-label" @click="step = 'reset'">
              Забыли пароль?
            </label>
          </template>

          <!-- Ввод email для восстановления пароля -->
          <template v-if="step === 'reset'">
            <Button label="Отправить код восстановления" type="submit" severity="contrast" class="full-width" />
            <label class="registration-label" @click="step = 'login'">
              Назад
            </label>
          </template>

          <!-- Ввод кода подтверждения для сброса пароля -->
          <template v-if="step === 'reset-code'">
            <FloatLabel variant="on">
              <label for="reset-code">Код подтверждения</label>
              <InputText
                  v-model="confirmationCode"
                  required
                  inputId="reset-code"
                  class="full-width"
              />
            </FloatLabel>
            <Button label="Подтвердить код" type="submit" severity="contrast" class="full-width" />
            <label
                class="registration-label"
                @click="resendConfirmationCode"
                :style="{ cursor: canResendCode ? 'pointer' : 'not-allowed', color: canResendCode ? '#2c3e50' : 'gray' }"
            >
              {{ canResendCode
                ? `Повторно отправить код на ${username}`
                : `Повторная отправка через ${resendTimer} сек` }}
            </label>
          </template>

          <!-- Ввод нового пароля после подтверждения кода -->
          <template v-if="step === 'reset-password'">
            <FloatLabel variant="on">
              <Password
                  v-model="password"
                  :feedback="false"
                  required
                  toggleMask
                  inputId="new-password"
                  :invalid="errorValid"
              />
              <label for="new-password">Новый пароль</label>
            </FloatLabel>

            <FloatLabel variant="on">
              <Password
                  v-model="confirmPassword"
                  :feedback="false"
                  required
                  toggleMask
                  inputId="confirm-new-password"
                  :invalid="errorValid"
              />
              <label for="confirm-new-password">Подтверждение пароля</label>
            </FloatLabel>

            <Button label="Сбросить пароль" type="submit" severity="contrast" class="full-width" />
          </template>

          <!-- Регистрация -->
          <template v-if="step === 'register'">
            <FloatLabel variant="on">
              <Password
                  v-model="password"
                  :feedback="false"
                  required
                  toggleMask
                  inputId="reg-password"
                  :invalid="errorValid"
              />
              <label for="reg-password">Пароль</label>
            </FloatLabel>

            <FloatLabel variant="on">
              <Password
                  v-model="confirmPassword"
                  :feedback="false"
                  required
                  toggleMask
                  inputId="confirm-password"
                  :invalid="errorValid"
              />
              <label for="confirm-password">Подтверждение пароля</label>
            </FloatLabel>

            <Button label="Зарегистрироваться" type="submit" severity="contrast" class="full-width" />
            <label class="registration-label" @click="step = 'login'">
              Уже есть аккаунт? Войти
            </label>
          </template>

          <!-- Подтверждение кода -->
          <template v-if="step === 'code'">
            <FloatLabel variant="on">
              <label for="code">Код подтверждения</label>
              <InputText
                  v-model="confirmationCode"
                  required
                  inputId="code"
                  class="full-width"
              />
            </FloatLabel>
            <Button label="Подтвердить" type="submit" severity="contrast" class="full-width" />
            <label
                class="registration-label"
                @click="resendConfirmationCode"
                :style="{ cursor: canResendCode ? 'pointer' : 'not-allowed', color: canResendCode ? '#2c3e50' : 'gray' }"
            >
              {{ canResendCode
                ? `Повторно отправить код на почту ${username}`
                : `Повторная отправка через ${resendTimer} сек` }}
            </label>
            <label class="registration-label" @click="step = 'register'">
              Назад
            </label>
          </template>
        </form>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref } from "vue";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Password from "primevue/password";
import Button from "primevue/button";
import FloatLabel from "primevue/floatlabel";
import router from "@/router/router.js";
import { useAuth } from "@/stores/auth.js";
import { login, register, confirmCode, confirmResetCode, sendResetCode, resetPassword, sendConfirmationCodeAgain } from "@/api/auth.js";

const step = ref("login"); // 'login' | 'register' | 'code' | 'reset' | 'reset-code' | 'reset-password'

const username = ref("");
const password = ref("");
const confirmPassword = ref("");
const confirmationCode = ref("");
const errorValid = ref(false);

const auth = useAuth();

const token = localStorage.getItem("token")
// if (token) {
//   router.push("/main")
// }


const onSubmit = async () => {
  try {
    if (step.value === "login") {
      const response = await login({ email: username.value, password: password.value });
      auth.setState({ token: response });
      router.push("/KS");

    } else if (step.value === "register") {
      if (password.value !== confirmPassword.value) {
        errorValid.value = true;
        return;
      }
      await register({ email: username.value, password: password.value });
      step.value = "code";
      startResendTimer();

    } else if (step.value === "code") {
      await confirmCode({ email: username.value, verification_code: confirmationCode.value });
      router.push("/KS");

    } else if (step.value === "reset") {
      await sendResetCode({ email: username.value }); // новый API
      step.value = "reset-code";
      startResendTimer();

    } else if (step.value === "reset-code") {
      await confirmResetCode({ email: username.value, verification_code: confirmationCode.value, password: ""});
      step.value = "reset-password";

    } else if (step.value === "reset-password") {
      if (password.value !== confirmPassword.value) {
        errorValid.value = true;
        return;
      }
      await resetPassword({ email: username.value, password: password.value, verification_code:  confirmationCode.value});
      step.value = "login";
    }

  } catch (e) {
    errorValid.value = true;
    console.error(e);
  } finally {
    setTimeout(() => {
      errorValid.value = false;
    }, 2000);
  }
};


const canResendCode = ref(false);
const resendTimer = ref(60);
let intervalId = null;

const startResendTimer = () => {
  canResendCode.value = false;
  resendTimer.value = 60;

  if (intervalId) {
    clearInterval(intervalId);
  }

  intervalId = setInterval(() => {
    resendTimer.value--;
    if (resendTimer.value <= 0) {
      canResendCode.value = true;
      clearInterval(intervalId);
    }
  }, 1000);
};

const resendConfirmationCode = async () => {
  if (!canResendCode.value) return;

  try {
    await sendConfirmationCodeAgain({
      email: username.value,
      verification_code: confirmationCode.value,
      password: password.value
    });
    startResendTimer();
  } catch (e) {
    console.error('Ошибка при повторной отправке кода', e);
  }
};

</script>

<style scoped>
.login-container {
  width: 100%;
  max-width: 700px;
  margin: 0 auto;
  padding: 2rem;
  margin-top: 200px;
}

.login-form {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.full-width {
  width: 254px;
}

.registration-label {
  margin-top: 10px;
  color: #2c3e50;
  transition: color 0.3s ease;
}

.registration-label:hover {
  color: #1c714b;
  cursor: pointer;
  text-decoration: underline;
}
</style>
