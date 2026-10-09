<template>
  <div class="max-w-[640px] mt-4">
    <p class="text-gray-500 mb-6">{{ $t('resourceConsole.aiSearch.desc') }}</p>

    <el-form label-position="top">
      <el-form-item :label="$t('resourceConsole.aiSearch.baseUrl')">
        <el-input
          v-model="form.llm_endpoint"
          placeholder="http://your-llm-host/v1/chat/completions" />
      </el-form-item>
      <el-form-item :label="$t('resourceConsole.aiSearch.apiKey')">
        <el-input
          v-model="form.llm_api_key"
          type="password"
          show-password
          :placeholder="$t('resourceConsole.aiSearch.apiKeyPlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('resourceConsole.aiSearch.modelName')">
        <el-input v-model="form.llm_model" placeholder="model-name" />
      </el-form-item>
    </el-form>

    <div class="flex gap-3 mt-2">
      <CsgButton
        class="btn btn-primary btn-sm"
        :name="$t('resourceConsole.aiSearch.save')"
        :loading="saving"
        @click="save" />
      <CsgButton
        class="btn btn-secondary-gray btn-sm"
        :name="$t('resourceConsole.aiSearch.test')"
        :loading="testing"
        @click="test" />
    </div>
  </div>
</template>

<script setup>
  import { onMounted, reactive, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { ElMessage } from 'element-plus'
  import useFetchApi from '../../packs/useFetchApi'
  import CsgButton from '../shared/CsgButton.vue'

  const { t } = useI18n()

  const form = reactive({
    llm_endpoint: '',
    llm_api_key: '',
    llm_model: ''
  })
  const saving = ref(false)
  const testing = ref(false)

  const fetchConfig = async () => {
    const { data, error } = await useFetchApi('/admin/ai_search/config').json()
    if (error.value) {
      ElMessage.error(t('resourceConsole.aiSearch.loadFailed'))
      return
    }
    if (data.value) {
      form.llm_endpoint = data.value.llm_endpoint || ''
      form.llm_api_key = data.value.llm_api_key || ''
      form.llm_model = data.value.llm_model || ''
    }
  }

  const save = async () => {
    saving.value = true
    const { error } = await useFetchApi('/admin/ai_search/config', {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    }).put().json()
    saving.value = false
    if (error.value) {
      ElMessage.error(t('resourceConsole.aiSearch.saveFailed'))
    } else {
      ElMessage.success(t('resourceConsole.aiSearch.saveSuccess'))
    }
  }

  const test = async () => {
    testing.value = true
    const { data, error } = await useFetchApi('/admin/ai_search/test', {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    }).post().json()
    testing.value = false
    if (error.value) {
      ElMessage.error(data.value?.msg || t('resourceConsole.aiSearch.testFailed'))
    } else {
      ElMessage.success(t('resourceConsole.aiSearch.testSuccess'))
    }
  }

  onMounted(fetchConfig)
</script>
