import { ref } from 'vue'
import { defineStore } from 'pinia'


export const useAuth = defineStore ("auth", () => {
  const token = ref(localStorage.getItem("token"))
  function setState(state) {
    token.value = state.token
    localStorage.setItem("token", state.token)
  }
  function logout() {
    token.value = ''
    localStorage.removeItem('token');
  }

  return {setState, logout, token}
})
