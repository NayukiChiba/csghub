<template>
  <div class="text-sm text-gray-600" data-testid="dataset-row-summary" role="status" aria-live="polite">
    <span>{{ $t('datasets.rowSummary', { total: displayTotal }) }}</span>
    <span v-if="summary && !summary.complete" class="block text-xs text-amber-700">
      {{ $t('datasets.rowSummaryIncomplete', { count: summary.uncounted_datasets }) }}
    </span>
    <button v-if="failed" type="button" class="ml-2 underline" @click="loadSummary">
      {{ $t('datasets.rowSummaryRetry') }}
    </button>
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import useFetchApi from '../../packs/useFetchApi'

const props = defineProps({ query: { type: String, default: '' } })
const { t } = useI18n()
const summary = ref(null)
const loading = ref(false)
const failed = ref(false)
let requestId = 0
const displayTotal = computed(() => {
  if (loading.value) return t('datasets.rowSummaryLoading')
  if (failed.value) return t('datasets.rowSummaryFailed')
  return summary.value ? BigInt(summary.value.total_rows).toLocaleString() : '—'
})

async function loadSummary() {
  const current = ++requestId
  summary.value = null
  failed.value = false
  if (!props.query) { loading.value = false; return }
  loading.value = true
  try {
    const { data, error } = await useFetchApi(`/datasets/row-summary?${props.query}`).json()
    if (current !== requestId) return
    const value = data.value?.data
    if (error?.value || !value || !/^\d+$/.test(String(value.total_rows))) throw new Error('Invalid row summary')
    summary.value = value
  } catch {
    if (current === requestId) failed.value = true
  } finally {
    if (current === requestId) loading.value = false
  }
}
watch(() => props.query, loadSummary, { immediate: true })
onUnmounted(() => { requestId++ })
</script>
