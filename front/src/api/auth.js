import {postData, putData} from '@/api/api.js'

const URL = "auth"


export async function login(data) {
  return putData(`${URL}/login`, data)
}

export async function register(data) {
  return postData(`${URL}/register`, data)
}

export function confirmCode(data) {
  return putData(`${URL}/confirm_registration`, data)
}

export function confirmResetCode(data) {
  return putData(`${URL}/confirm_code`, data)
}

export function sendResetCode(data) {
  return putData(`${URL}/reset_password_code`, data)
}

export async function resetPassword(data) {
  return putData(`${URL}/reset_password`, data)
}

export function sendConfirmationCodeAgain(data) {
  return putData(`${URL}/resend_code`, data)
}