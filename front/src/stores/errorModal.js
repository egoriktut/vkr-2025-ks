import { ref } from 'vue';
import { defineStore } from 'pinia';

export const useErrorModalStore = defineStore('errorModal', () => {
    const isOpen = ref(false);
    const errorMessage = ref('');

    const openModal = (message) => {
        errorMessage.value = message;
        isOpen.value = true;
    };

    const closeModal = () => {
        isOpen.value = false;
    };

    return { isOpen, errorMessage, openModal, closeModal };
});