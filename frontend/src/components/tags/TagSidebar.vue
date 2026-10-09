<template>
  <div class="flex bg-white flex-col pt-8 pb-15">
    <div class="flex flex-wrap gap-1">
      <TagCategory
        v-for="category in avaliableCategories"
        :key="category.name"
        :name="category.name"
        :zhName="category.show_name"
        :activeCategory="activeNavItem"
        :activeTags="activeTags"
        @changeActiveItem="changeActiveItem" />
    </div>
    <div>
      <TagList
        :activeCategory="activeNavItem"
        :taskTags="tagsForCategory['task']"
        :tags="activeNavItem === 'task' && repoType !== 'mcp' && repoType !== 'skill' ? [] : tagsForCategory[activeNavItem]"
        :activeTags="activeTags"
        :repoType="repoType"
        @setActiveTag="setActiveTag"
      />
    </div>
  </div>
</template>

<script setup>
  import { ref, onMounted, computed, watch } from 'vue'
  import TagList from './TagList.vue'
  import useFetchApi from '../../packs/useFetchApi'
  import { ElMessage } from 'element-plus'
  import TagCategory from './TagCategory.vue'
  const props = defineProps({
    repoType: String,
    selectedTag: String,
    selectedTagType: String,
    externalActiveTags: {
      type: Object,
      default: () => ({})
    }
  })

  const emit = defineEmits(['resetTags', 'updateCategories'])

  const tagCategories = ref([])
  const allTags = ref([])
  const tagsForCategory = ref({})

  const activeNavItem = ref('task')

  const activeTags = ref({})

  const avaliableCategories = computed(() => {
    const categoriesWithTags = new Set(allTags.value.map((tag) => tag.category))
    const configuredCategories = tagCategories.value.filter((category) => {
      if (props.repoType === 'mcp' && category.name === 'runmode') {
        return false
      }
      return category.scope === props.repoType &&
        category.enabled &&
        category.name !== 'publisher' &&
        categoriesWithTags.has(category.name)
    })
    const knownCategoryNames = new Set(
      tagCategories.value
        .filter((category) => category.scope === props.repoType)
        .map((category) => category.name)
    )
    const dynamicCategories = [...categoriesWithTags]
      .filter((name) =>
        name &&
        name !== 'publisher' &&
        !(props.repoType === 'mcp' && name === 'runmode') &&
        !knownCategoryNames.has(name)
      )
      .map((name) => ({
        name,
        show_name: name,
        scope: props.repoType,
        enabled: true
      }))

    return [...configuredCategories, ...dynamicCategories]
  })

  watch(avaliableCategories,
    (newValue) => {
      if (newValue.length > 0 && newValue[0]?.name) {
        activeNavItem.value = newValue[0].name
      }
      emit('updateCategories', newValue.map(item => item.name))
    }
  )

  const changeActiveItem = (currentCategory) => {
    activeNavItem.value = currentCategory
  }

  const emitTag = () => {
    emit('resetTags', activeTags.value)
  }

  const setActiveTag = (category, tagName) => {
    if (activeTags.value[category] === undefined) {
      activeTags.value[category] = []
      activeTags.value[category].push(tagName)
    } else if (Array.isArray(activeTags.value[category])) {
      if (activeTags.value[category].includes(tagName)) {
        const filteredTags = activeTags.value[category].filter((tag) => tag !== tagName)
        activeTags.value[category] = filteredTags
      } else {
        activeTags.value[category].push(tagName)
      }
    }
    emitTag()
  }

  const setTagNameFromParams = () => {
    if (props.selectedTagType && props.selectedTag) {
      const tags = props.selectedTag.split(',').map(t => t.trim()).filter(t => t)
      if (activeTags.value[props.selectedTagType] === undefined) {
        activeTags.value[props.selectedTagType] = tags
        return true
      } else if (Array.isArray(activeTags.value[props.selectedTagType])) {
        tags.forEach(tag => {
          if (!activeTags.value[props.selectedTagType].includes(tag)) {
            activeTags.value[props.selectedTagType].push(tag)
          }
        })
        return true
      }
    }
    return false
  }

  const setTagTypeFromParams = () => {
    if (props.selectedTagType) {
      activeNavItem.value = props.selectedTagType
    }
  }

  const emitTagFromParams = () => {
    setTagTypeFromParams()
    const changed = setTagNameFromParams()
    if (changed) emitTag()
  }

  const syncUIFromActiveTags = () => {
    const categoriesWithTags = Object.entries(activeTags.value).filter(
      ([_, tags]) => Array.isArray(tags) && tags.length > 0
    )
    
    const currentCategoryTags = activeTags.value[activeNavItem.value]
    const currentHasTags = Array.isArray(currentCategoryTags) && currentCategoryTags.length > 0
    
    if (!currentHasTags) {
      if (categoriesWithTags.length > 0) {
        activeNavItem.value = categoriesWithTags[0][0]
      } else {
        if (avaliableCategories.value.length > 0) {
          activeNavItem.value = avaliableCategories.value[0].name
        }
      }
    }
  }

  defineExpose({
    syncUIFromActiveTags
  })

  watch(
    () => props.externalActiveTags,
    (val) => {
      activeTags.value = JSON.parse(JSON.stringify(val || {}))
    },
    { deep: true, immediate: true }
  )

  watch(
    () => [props.selectedTag, props.selectedTagType],
    ([tag, type]) => {
      if (type && tag) {
        activeNavItem.value = type
        const tags = tag.split(',').map(t => t.trim()).filter(t => t)
        activeTags.value = { [type]: tags }
      }
    }
  )

  async function fetchTags() {
    const params = new URLSearchParams({ scope: props.repoType, used: 'true' })
    const { data, error } = await useFetchApi(`/tags?${params.toString()}`).json()
    if (data.value?.data) {
      allTags.value = data.value.data.filter((tag) => tag.scope === props.repoType)

      avaliableCategories.value.forEach((category) => {
        const categoryTags = allTags.value.filter((tag) => tag.category === category.name)
        if (category.name === 'task' && props.repoType !== 'mcp' && props.repoType !== 'skill') {
          tagsForCategory.value.task = categoryTags.reduce((groups, tag) => {
            const group = tag.group || '__other__'
            if (!groups[group]) groups[group] = []
            groups[group].push(tag)
            return groups
          }, {})
        } else {
          tagsForCategory.value[category.name] = categoryTags
        }
      })
    } else {
      ElMessage.error(`Failed to fetch tags: ${error.value}`)
    }
  }

  const fetchTagCategories = async () => {
    const { data, error } = await useFetchApi('/tags/categories').json()
    if (data.value) {
      tagCategories.value = data.value.data
    } else {
      ElMessage.error(`Failed to fetch tag category: ${error.value}`)
    }
  }

  onMounted(async () => {
    await fetchTagCategories()
    await fetchTags()

    // init selected tag from params
    emitTagFromParams()

    // activeNavItem.value = avaliableCategories[0]?.name

    // init initial tag category

    // if (props.repoType === 'code' || props.repoType === 'space') {
    //   activeNavItem.value = 'license'
    //   // toggleTagType()
    // } else {
    //   activeNavItem.value = 'task'
    // }
  })
</script>
