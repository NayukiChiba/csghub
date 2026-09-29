import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import TagSidebar from '@/components/tags/TagSidebar.vue'
import TagCategory from '@/components/tags/TagCategory.vue'
import TaskTagItem from '@/components/tags/TaskTagItem.vue'
import useFetchApi from '@/packs/useFetchApi'

const categories = [
  { id: 1, name: 'task', show_name: '任务', scope: 'dataset', enabled: true },
  { id: 2, name: 'license', show_name: '许可证', scope: 'dataset', enabled: true },
  { id: 3, name: 'framework', show_name: '框架', scope: 'dataset', enabled: true },
  { id: 4, name: 'disabled-quality', show_name: '已禁用', scope: 'dataset', enabled: false }
]

const tags = [
  { id: 1, name: 'text-generation', show_name: '文本生成', category: 'task', group: 'text_processing', scope: 'dataset', built_in: true },
  { id: 2, name: 'agent-trajectory', show_name: 'Agent轨迹', category: 'task', group: '', scope: 'dataset', built_in: false },
  { id: 3, name: 'hallucination-risk', show_name: '幻觉风险', category: 'quality', group: '', scope: 'dataset', built_in: false },
  { id: 4, name: 'hidden-tag', show_name: '隐藏标签', category: 'disabled-quality', group: '', scope: 'dataset', built_in: false },
  { id: 5, name: 'pytorch', show_name: 'PyTorch', category: 'framework', group: '', scope: 'dataset', built_in: true },
  { id: 6, name: 'custom-runtime', show_name: '自定义运行时', category: 'framework', group: '', scope: 'dataset', built_in: false }
]

vi.mock('@/packs/useFetchApi', () => ({
  default: vi.fn((url) => ({
    json: async () => {
      if (url === '/tags/categories') {
        return { data: { value: { data: categories } }, error: { value: null } }
      }
      if (url === '/tags?scope=dataset&used=true') {
        return { data: { value: { data: tags } }, error: { value: null } }
      }
      return { data: { value: null }, error: { value: 'unexpected request' } }
    }
  }))
}))

const createWrapper = () => mount(TagSidebar, {
  props: {
    repoType: 'dataset',
    externalActiveTags: {}
  }
})

describe('TagSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads and selects custom task tags without requiring built_in', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    expect(useFetchApi).toHaveBeenCalledWith('/tags?scope=dataset&used=true')
    expect(wrapper.text()).toContain('agent trajectory')
    expect(wrapper.text()).toContain('Others')

    const customTag = wrapper.findAllComponents(TaskTagItem)
      .find((item) => item.props('tag').name === 'agent-trajectory')
    await customTag.trigger('click')

    expect(wrapper.emitted('resetTags').at(-1)[0]).toEqual({
      task: ['agent-trajectory']
    })
  })

  it('adds categories found in tag data even without category metadata', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const dynamicCategory = wrapper.findAllComponents(TagCategory)
      .find((item) => item.props('name') === 'quality')
    expect(dynamicCategory).toBeDefined()
    expect(wrapper.findAllComponents(TagCategory)
      .some((item) => item.props('name') === 'disabled-quality')).toBe(false)

    await dynamicCategory.trigger('click')
    expect(wrapper.text()).toContain('hallucination risk')
  })

  it('only renders framework tags returned by the tags API', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const frameworkCategory = wrapper.findAllComponents(TagCategory)
      .find((item) => item.props('name') === 'framework')
    await frameworkCategory.trigger('click')

    expect(wrapper.text()).toContain('PyTorch')
    expect(wrapper.text()).toContain('custom runtime')
    expect(wrapper.text()).not.toContain('TensorFlow')
    expect(wrapper.text()).not.toContain('Safetensors')
  })
})
