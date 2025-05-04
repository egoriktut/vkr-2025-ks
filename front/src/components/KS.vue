<script setup>
import {ref, onMounted, onUnmounted, computed} from 'vue'
import {deleteData, getData, postData} from "@/api/api.js";
import BodyComponent from "@/components/BodyComponent.vue";
import Button from "primevue/button";

const url = ref("")
const selectedReasons = ref([])
const reasons = [
  { value: 1, label: "Наименование закупки совпадает с наименованием в техническом задании и/или в проекте контракта" },
  { value: 2, label: "Обеспечение исполнения контракта" },
  { value: 3, label: "Наличие сертификатов/лицензий" },
  { value: 4, label: "График поставки И этап поставки" },
  { value: 5, label: "Максимальное значение цены контракта ИЛИ начальная цена" },
  { value: 6, label: "Спецификации" },
]

function isValidUrl(string) {
  const pattern = new RegExp('^(https?:\\/\\/)?' +
      '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|' +
      '((\\d{1,3}\\.){3}\\d{1,3}))' +
      '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*' +
      '(\\?[;&a-z\\d%_.~+=-]*)?' +
      '(\\#[-a-z\\d_]*)?$', 'i');
  return !!pattern.test(string);
}

const tasksData = ref([])
const canProcess = ref(true)

async function checkKS() {
  if (!canProcess.value) {
    return
  }

  const urlsSend = url.value.split('\n').map(item => item.trim()).filter(Boolean);

  if (urlsSend.length === 0) {
    alert("Введите хотя бы один URL для проверки.");
    return;
  }

  const invalidUrls = urlsSend.filter(item => !isValidUrl(item));
  if (invalidUrls.length > 0) {
    alert(`Найдены некорректные URL:\n${invalidUrls.join('\n')}`);
    return;
  }

  if (selectedReasons.value.length === 0) {
    alert("Выберите хотя бы одно основание для проверки.");
    return;
  }
  const selectedLabels = selectedReasons.value
    .map(selected => reasons.find(reason => reason.value === selected)?.label)
    .map((label, index) => `${index + 1}. ${label}`);

  alert(`Проверка КС по URL:\n${urlsSend.join('\n')}\n\nВыбранные основания: \n${selectedLabels.join('\n')}`);

  isSubmitting.value = true;
  const response = await postData("analyze", {urls: urlsSend, validate_params: selectedReasons.value})
  if (response) {
    console.log("Start processing")
  } else {
    alert("Ошибка обработки ссылок КС")
  }

}

function toggleSelectAll(event) {
  if (event.target.checked) {
    selectedReasons.value = reasons.map(reason => reason.value);
  } else {
    selectedReasons.value = [];
  }
}

const sendReportTask = (task) => {
  getData(`analyze/send_task/${task.ids}`)
  alert(`Отчет по КС: ${task.url} \n"${task.description}"\n Отправлен на почту`)
}

const clearHistory = () => {
  tasksData.value = [];
  deleteData("analyze/clear_task_history", {})
};

let timerId = null;

const analyze = () => {
  getData(`analyze`).then((response) => {
    tasksData.value = response;
    isSubmitting.value = false;
  })
}

onMounted(() => {
  console.log('activated KS');
  analyze()
  timerId = setInterval(analyze, 2000);
})

onUnmounted(() => {
  console.log('deactivated KS')
  clearInterval(timerId);
  timerId = null;
})

const getStatusText = (status) => {
  const statusMap = {
    'PENDING': 'В обработке',
    'SUCCESS': 'Успешно',
    'FAILURE': 'Ошибка'
  };
  return statusMap[status] || status;
};

const isResultValid = (result) => {
  try {
    const parsed = JSON.parse(result);
    return parsed.analysis && Object.values(parsed.analysis).every(item => item.status);
  } catch {
    return false;
  }
};

const parseAnalysis = (result) => {
  try {
    const parsed = JSON.parse(result);
    return parsed.analysis || {};
  } catch {
    return {};
  }
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString();
};

const searchQuery = ref('');
const sortField = ref('created_at');
const sortAsc = ref(false);

// Фильтрация и сортировка задач
const filteredAndSortedTasks = computed(() => {
  let filtered = tasksData.value;

  // Поиск
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(task =>
        task.url.toLowerCase().includes(query) ||
        task.description.toLowerCase().includes(query)
    );
  }

  // Сортировка
  return [...filtered].sort((a, b) => {
    let fieldA = a[sortField.value];
    let fieldB = b[sortField.value];

    if (sortField.value === 'created_at') {
      fieldA = new Date(fieldA);
      fieldB = new Date(fieldB);
    } else if (sortField.value === 'status') {
      // Сортируем по порядку: PROCESSING, PENDING, SUCCESS, FAILURE
      const order = { 'PROCESSING': 1, 'PENDING': 2, 'SUCCESS': 3, 'FAILURE': 4 };
      fieldA = order[a.status];
      fieldB = order[b.status];
    }

    return sortAsc.value
        ? fieldA > fieldB ? 1 : -1
        : fieldA < fieldB ? 1 : -1;
  });
});

const toggleSortOrder = () => {
  sortAsc.value = !sortAsc.value;
};

const isSubmitting = ref(false);
</script>

<template>
  <BodyComponent>
    <div class="container">
      <div class="input-section">
        <h2>Основания для снятия КС с публикации</h2>

        <div class="form-group">
          <label for="url">Введите URL (каждый с новой строки)</label>
          <textarea
              id="url"
              v-model="url"
              placeholder="Введите URL для проверки, каждый с новой строки..."
          ></textarea>
        </div>

        <div class="checkboxes">
          <h3>Критерии проверки:</h3>
          <div class="checkbox-item select-all">
            <input
                type="checkbox"
                :checked="selectedReasons.length === reasons.length"
                @change="toggleSelectAll"
                id="select-all"
            />
            <label for="select-all">Выбрать все</label>
          </div>
          <div v-for="reason in reasons" :key="reason.value" class="checkbox-item">
            <input
                type="checkbox"
                :value="reason.value"
                v-model="selectedReasons"
                :id="'reason-' + reason.value"
            />
            <label :for="'reason-' + reason.value">{{ reason.label }}</label>
          </div>
        </div>

        <Button
            @click="checkKS"
            type="submit"
            severity="contrast"
            class="full-width"
            :loading="isSubmitting"
        >
          Проверить КС
        </Button>
      </div>

      <div v-if="tasksData.length > 0" class="tasks-section">
        <div class="tasks-controls">
          <h3>Результат обработки КС</h3>

          <div class="controls-row">
            <div class="search-box">
              <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="Поиск по URL или описанию..."
                  class="search-input"
              >
              <i class="search-icon">🔍</i>
            </div>

            <div class="sort-controls">
              <select v-model="sortField" class="sort-select">
                <option value="created_at">Дата создания</option>
                <option value="status">Статус</option>
                <option value="description">Описание</option>
              </select>

              <button
                  @click="toggleSortOrder"
                  class="sort-direction"
                  :class="{ 'asc': sortAsc, 'desc': !sortAsc }"
              >
                {{ sortAsc ? '↑' : '↓' }}
              </button>
            </div>

            <button @click="clearHistory" class="clear-btn">
              Очистить историю
            </button>
          </div>
        </div>

        <div class="tasks-list">
          <div
              v-for="task in filteredAndSortedTasks"
              :key="task.id"
              class="task-card"
              :class="task.status.toLowerCase()"
          >
            <!-- Остальное содержимое карточки задачи без изменений -->
            <div class="task-header">
              <span class="task-id">Задача #{{ task.id }}</span>
              <span class="task-status" :class="task.status.toLowerCase()">
            {{ getStatusText(task.status) }}
          </span>
            </div>

            <div class="task-body">
              <h4>{{ task.description }}</h4>
              <a :href="task.url" target="_blank" class="task-url">{{ task.url }}</a>

              <div v-if="task.status === 'PENDING'" class="task-pending">
                <div class="loader"></div>
                <span>Идет анализ</span>
              </div>

              <div v-else-if="task.status === 'SUCCESS'" class="task-result">
                <div class="result-summary" :class="{ valid: isResultValid(task.result), invalid: !isResultValid(task.result) }">
                  {{ isResultValid(task.result) ? '✓ КС корректна' : '✗ КС должна быть снята' }}
                </div>

                <details class="result-details">
                  <summary>Подробности анализа</summary>
                  <div class="analysis-items">
                    <div v-for="(item, key) in parseAnalysis(task.result)" :key="key" class="analysis-item">
                  <span :class="item.status ? 'valid' : 'invalid'">
                    {{ item.status ? '✓' : '✗' }}
                  </span>
                      <span>{{ `${reasons.find(r => r.value === parseInt(key)).label}:` }}</span>
                      <h3>{{ `${item.description}` }}</h3>
                    </div>
                  </div>
                </details>
              </div>

              <div v-else-if="task.status === 'FAILURE'" class="task-failed">
                Ошибка при обработке задачи
              </div>
            </div>

            <div class="task-footer">
          <span class="task-date">
            Создано: {{ formatDate(task.created_at) }}
            <span v-if="task.completed_at"> | Завершено: {{ formatDate(task.completed_at) }}</span>
          </span>
              <button v-if="task.status === 'SUCCESS'" @click="sendReportTask(task)" class="report-btn">
                Отправить отчет на почту
              </button>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="tasks-section">
        <h2>Не найдено обработанных КС</h2>
      </div>
    </div>
  </BodyComponent>
</template>

<style scoped>
.container {
  max-width: 95%;
  margin: 0 auto;
  padding: 20px;
}

/* Input section styles */
.input-section {
  background: #fff;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  margin-bottom: 30px;
}

h2, h3 {
  color: #2c3e50;
  margin-bottom: 20px;
  text-align: center;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #34495e;
}

textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  min-height: 120px;
  resize: vertical;
  font-family: inherit;
}

.checkboxes {
  margin: 25px 0;
}

.checkbox-item {
  margin: 8px 0;
  display: flex;
  align-items: center;
}

.checkbox-item input {
  margin-right: 10px;
}

.select-all {
  font-weight: bold;
  padding-bottom: 10px;
  margin-bottom: 10px;
  border-bottom: 1px solid #eee;
}

button {
  width: 100%;
  //padding: 12px;
  //background: #3498db;
  //color: white;
  //border: none;
  //border-radius: 6px;
  //font-weight: 500;
  //cursor: pointer;
  //transition: all 0.2s;
}
/*
button:hover {
  background: #2980b9;
}

button.disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}
*/
/* Tasks section styles */
.tasks-section {
  background: #fff;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.task-card {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 15px;
  transition: all 0.2s;
}

.task-card:hover {
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.1);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f5f5f5;
}

.task-id {
  font-size: 0.9em;
  color: #7f8c8d;
}

.task-status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.8em;
  font-weight: 500;
}

.task-status.pending {
  background: #fff3cd;
  color: #856404;
}

.task-status.processing {
  background: #e2f0fd;
  color: #004085;
}

.task-status.success {
  background: #d4edda;
  color: #155724;
}

.task-status.failed {
  background: #f8d7da;
  color: #721c24;
}

.task-body {
  margin: 10px 0;
}

.task-body h4 {
  margin: 0 0 8px 0;
  font-size: 1.1em;
  color: #2c3e50;
  text-align: left;
}

.task-url {
  color: #3498db;
  word-break: break-all;
  display: block;
  margin-bottom: 10px;
}

.task-pending,
.task-processing {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #7f8c8d;
  padding: 10px 0;
}

.loader {
  border: 2px solid #f3f3f3;
  border-top: 2px solid #3498db;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.task-result {
  margin: 10px 0;
}

.result-summary {
  font-weight: 500;
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 10px;
}

.result-summary.valid {
  background: #d4edda;
  color: #155724;
}

.result-summary.invalid {
  background: #f8d7da;
  color: #721c24;
}

.result-details {
  margin-top: 10px;
}

.result-details summary {
  cursor: pointer;
  color: #3498db;
  font-weight: 500;
}

.analysis-items {
  margin-top: 10px;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}

.analysis-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 6px 0;
}

.analysis-item .valid {
  color: #28a745;
}

.analysis-item .invalid {
  color: #dc3545;
}

.task-failed {
  color: #dc3545;
  padding: 10px 0;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #f5f5f5;
  font-size: 0.85em;
  color: #7f8c8d;
}

.report-btn {
  padding: 6px 12px;
  //background: #6c757d;
  //color: white;
  font-size: 0.85em;
  width: auto;
}

.report-btn:hover {
  cursor: pointer;
}

.tasks-controls {
  margin-bottom: 20px;
}

.controls-row {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-top: 15px;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  flex-grow: 1;
  max-width: 400px;
}

.search-input {
  width: 100%;
  padding: 10px 15px 10px 35px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.95em;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.6;
}

.sort-controls {
  display: flex;
  gap: 5px;
}

.sort-select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
  font-size: 0.95em;
}

.sort-direction {
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.sort-direction:hover {
  background-color: #f5f5f5;
}

.sort-direction.asc::after {
  content: ' ↑';
}

.sort-direction.desc::after {
  content: ' ↓';
}

.clear-btn {
  padding: 10px 15px;
  background-color: #8a1725;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.95em;
}

.clear-btn:hover {
  background-color: #75030f;
}

/* Адаптивность */
@media (max-width: 768px) {
  .controls-row {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    max-width: 100%;
  }

  .sort-controls {
    justify-content: flex-end;
  }
}
</style>