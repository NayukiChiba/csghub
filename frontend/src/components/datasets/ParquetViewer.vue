<template>
  <div
    class="flex flex-col gap-[16px]"
    :class="fullscreen
      ? 'fixed inset-0 z-[2000] bg-white overflow-y-auto p-[32px]'
      : 'border rounded-md p-[16px]'">
    <div class="flex justify-between gap-[16px]">
      <div class="flex w-[181px] h-[28px]">
        <SvgIcon
          name="parquet_viewer"
          width="13px"
          height="13px"
        />
        <p class="ml-[8px] text-gray-900 text-lg leading-[28px]">{{ $t('all.parquet') }}</p>
      </div>
      <div
        class="items-center gap-1.5 flex cursor-pointer"
        @click="toggleFullscreen">
        <SvgIcon :name="fullscreen ? 'x-close' : 'fullscreen'" />
        <div class="text-gray-700 text-xs leading-[18px]">
          {{ fullscreen ? $t('endpoints.playground.exitFullscreen') : $t('endpoints.playground.maximum') }}
        </div>
      </div>
    </div>
    <div class="flex justify-between gap-[16px] text-gray-700 text-sm leading-[20px] xl:flex-col">
      <div class="flex flex-col gap-[8px]">
        <p>{{ $t('all.subset') }}（{{ numSubsets }}）</p>
        <el-select
          v-model="subset"
          @change="changeSubsetName"
          placeholder="Select"
          size="large"
          class="!w-[330px] xl:!w-full">
          <template #prefix>
            <span>{{ showRows }} {{ $t('all.rows') }}</span>
          </template>
          <el-option
            v-for="item in datasetInfo"
            :key="item.config_name"
            :label="item.config_name"
            :value="item.config_name" />
        </el-select>
      </div>
      <div v-if="splits" class="flex flex-col gap-[8px]">
        <p>{{ $t('all.split') }}（{{ numSplits }}）</p>
        <el-select
          v-model="split"
          @change="changeSplitName"
          placeholder="Select"
          size="large"
          class="!w-[330px] xl:!w-full">
          <template #prefix>
            <span>{{ showRows }} {{ $t('all.rows') }}</span>
          </template>
          <el-option
            v-for="item in splits"
            :key="item.name"
            :label="item.name"
            :value="item.name">
          </el-option>
        </el-select>
      </div>
    </div>
    <!-- <div>
      <el-input
        v-model="nameFilterInput"
        clearable
        size="large"
        :prefix-icon="Search"
        placeholder="Search this dataset"
        @change="filterChange"
        class="w-full" />
    </div> -->
    <div>
      <el-table :data="tableData"
                border
                stripe
                :max-height="fullscreen ? 'calc(100vh - 320px)' : '480'"
                @row-click="toggleRow"
                v-loading="previewLoading"
                class="w-full rounded-md mb-4"
                row-class-name="row-item-clamp cursor-pointer"
                cell-class-name="!align-top">
        <el-table-column
          type="index"
          :index="rowIndex"
          label=""
          width="72"
          fixed="left"
          align="right"
          class-name="text-gray-400" />
        <el-table-column
          v-for="(column, columnIndex) in previewData.columns"
          :key="column"
          :prop="column"
          :label="column"
          min-width="240">
          <template #header>
            <div class="flex flex-col leading-[18px]">
              <span class="text-gray-900 font-medium">{{ column }}</span>
              <span
                v-if="previewData.columns_type && previewData.columns_type[columnIndex]"
                class="text-gray-400 text-xs font-normal">
                {{ previewData.columns_type[columnIndex] }}
              </span>
            </div>
          </template>
          <template #default="scope">
            <DatasetPreviewCell
              :value="scope.row[column]"
              :column="column"
              :namespacePath="namespacePath"
              :currentBranch="currentBranch" />
          </template>
        </el-table-column>
      </el-table>
      <CsgPagination
        :perPage="perPage"
        :currentPage="currentPage"
        @currentChange="reloadRows"
        :total="totalRows"
      />
    </div>
  </div>
</template>

<script setup>
  import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
  import { ElMessage } from 'element-plus'
  import useFetchApi from '../../packs/useFetchApi'
  import CsgPagination from '../shared/CsgPagination.vue'
  import DatasetPreviewCell from './DatasetPreviewCell.vue'
  import { useI18n } from 'vue-i18n'

  const props = defineProps({
    datasetInfo: {
      type: Array,
      default: () => []

    },
    namespacePath: String,
    currentBranch: {
      type: String,
      default: 'main'
    }
  })

  const { t } = useI18n()
  const previewLoading = ref(false)

  const previewData = ref({ columns: [], columns_type: [], rows: [], total: 0 })
  const currentPage = ref(1)
  const totalRows = computed(() => { return previewData.value.total });
  const fullscreen = ref(false)
  const NORMAL_PER_PAGE = 4
  const FULLSCREEN_PER_PAGE = 20
  const perPage = ref(NORMAL_PER_PAGE)
  const nameFilterInput = ref('')
  // 默认subset和split的值
  const splits = ref((props.datasetInfo && props.datasetInfo[0]?.splits) || [])
  const subset = ref(props.datasetInfo && props.datasetInfo[0]?.config_name || [])
  const split = ref(splits.value[0]?.name || '')
  const Rows = ref(splits.value[0]?.num_examples || 0)

  const numSplits = computed(() => {
    return splits.value?.length || 0
  })
  const numSubsets = computed(() => {
    return props.datasetInfo?.length || 0
  })

  watch(() => props.datasetInfo, (newValue) => {
    splits.value = (newValue && newValue[0]?.splits) || []
    subset.value = (newValue && newValue[0]?.config_name) || []
    split.value = splits.value[0]?.name || ''
    Rows.value = splits.value[0]?.num_examples || 0
  })

  const tableData = computed(() => {
    if (!previewData.value?.rows || !previewData.value?.columns) {
      return []
    }

    const { rows, columns } = previewData.value

    return rows.map(row =>
      columns.reduce((obj, column, index) => {
        obj[column] = row[index]
        return obj
      }, {})
    )
  })

  const showRows = computed(() => {
    let result = ''
    if (Rows.value >= 1000000) {
      result = (Rows.value / 1000000).toFixed(1) + 'M';
    } else if (Rows.value >= 1000) {
      result = (Rows.value / 1000).toFixed(1) + 'K';
    } else {
      result = Rows.value;
    }

    return result
  })

  const rowIndex = (index) => {
    return (currentPage.value - 1) * perPage.value + index + 1
  }

  const toggleRow = (_row, _column, event) => {
    const row = event.target.closest('.el-table__row')
    row.classList.toggle('row-item-clamp')
  }

  const toggleFullscreen = () => {
    fullscreen.value = !fullscreen.value
    perPage.value = fullscreen.value ? FULLSCREEN_PER_PAGE : NORMAL_PER_PAGE
    currentPage.value = 1
    reloadRows()
  }

  const onKeydown = (event) => {
    if (event.key === 'Escape' && fullscreen.value) {
      toggleFullscreen()
    }
  }

  const changeSubsetName = (value) => {
    const filteredItem = props.datasetInfo.find(item => item.config_name === value)
    splits.value = filteredItem ? filteredItem.splits: null
    subset.value = filteredItem ? filteredItem.config_name: null
    split.value = splits.value[0]?.name || ''
    Rows.value = splits.value[0]?.num_examples || 0
    currentPage.value = 1
    reloadRows()
  }

  const changeSplitName = (value) => {
    currentPage.value = 1
    Rows.value = splits.value.find(item => item.name === value).num_examples
    reloadRows()
  }

  const filterChange = () => {
    currentPage.value = 1
    reloadRows()
  }

  const reloadRows = (childCurrent) => {
    if(childCurrent){
      currentPage.value = childCurrent
    }
    let url = `datasets/${props.namespacePath}/dataviewer/rows`
    url = url + `?page=${childCurrent ? childCurrent : currentPage.value}`
    url = url + `&per=${perPage.value}`
    url = url + `&search=${nameFilterInput.value}`

    url = url + `&namespace=${props.namespacePath.split('/')[0]}`
    url = url + `&config=${subset.value}`
    url = url + `&split=${split.value}`
    loadRows(url)
  }

  async function loadRows(url) {
    previewLoading.value = true
    const { error, data } = await useFetchApi(url).json()
    if (!data.value) {
      ElMessage({
        message: error.value.msg || t('all.fetchError'),
        type: 'warning'
      })
    } else {
      previewData.value = data.value.data
    }
    previewLoading.value = false
  }

  onMounted(() => {
    reloadRows()
    window.addEventListener('keydown', onKeydown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', onKeydown)
  })
</script>

<style scoped>
  :deep(.row-item-clamp .cell) {
    overflow: hidden;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
  }

  :deep(.el-table__header-wrapper th) {
    background-color: #F9FAFB;
  }

  /* HuggingFace-like breathing room: taller rows, wider gutters */
  :deep(.el-table th.el-table__cell) {
    padding: 10px 0;
  }

  :deep(.el-table td.el-table__cell) {
    padding: 14px 0;
  }

  :deep(.el-table .cell) {
    padding: 0 20px;
    line-height: 22px;
  }
</style>
