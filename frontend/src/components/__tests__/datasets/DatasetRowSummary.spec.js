import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Summary from '../../datasets/DatasetRowSummary.vue'
import useFetchApi from '@/packs/useFetchApi'
vi.mock('@/packs/useFetchApi', () => ({ default: vi.fn() }))
const response = (rows, extra = {}) => ({ data: { value: { data: {
  total_rows: rows, total_datasets: 1, counted_datasets: 1,
  uncounted_datasets: 0, complete: true, ...extra
} } } })
const mockResponse = value => useFetchApi.mockReturnValue({ json: () => Promise.resolve(value) })
describe('DatasetRowSummary', () => {
  it('preserves large integer precision and passes the filter query', async () => {
    mockResponse(response('9007199254740993'))
    const wrapper = mount(Summary, { props: { query: 'search=qa&tag_category=task&tag_name=text' } })
    await flushPromises()
    expect(useFetchApi).toHaveBeenLastCalledWith('/datasets/row-summary?search=qa&tag_category=task&tag_name=text')
    expect(wrapper.text()).toContain(BigInt('9007199254740993').toLocaleString())
    wrapper.unmount()
  })
  it('distinguishes unknown counts from a genuine zero', async () => {
    mockResponse(response('0', { complete: false, uncounted_datasets: 2 }))
    const wrapper = mount(Summary, { props: { query: 'source=local' } })
    await flushPromises()
    expect(wrapper.text()).toContain('Total dataset rows: 0')
    expect(wrapper.text()).toContain('Row counts unavailable for 2 datasets')
    wrapper.unmount()
  })
  it('ignores slow responses for previous filters', async () => {
    let finishOld
    useFetchApi.mockReturnValueOnce({ json: () => new Promise(resolve => { finishOld = resolve }) })
      .mockReturnValueOnce({ json: () => Promise.resolve(response('20')) })
    const wrapper = mount(Summary, { props: { query: 'search=old' } })
    await wrapper.setProps({ query: 'search=new' }); await flushPromises()
    finishOld(response('999')); await flushPromises()
    expect(wrapper.text()).toContain('Total dataset rows: 20')
    expect(wrapper.text()).not.toContain('999')
    wrapper.unmount()
  })
  it('clears stale counts on failure and retries', async () => {
    mockResponse(response('10'))
    const wrapper = mount(Summary, { props: { query: 'search=old' } })
    await flushPromises()
    mockResponse({ data: { value: null }, error: { value: new Error('offline') } })
    await wrapper.setProps({ query: 'search=new' }); await flushPromises()
    expect(wrapper.text()).toContain('Unavailable')
    expect(wrapper.text()).not.toContain('10')
    mockResponse(response('0'))
    await wrapper.find('button').trigger('click'); await flushPromises()
    expect(wrapper.text()).toContain('Total dataset rows: 0')
    expect(wrapper.find('button').exists()).toBe(false)
    wrapper.unmount()
  })
})
