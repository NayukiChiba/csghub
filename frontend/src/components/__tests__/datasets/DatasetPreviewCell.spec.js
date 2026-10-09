import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DatasetPreviewCell from '../../datasets/DatasetPreviewCell.vue'

const mountCell = (props = {}) => mount(DatasetPreviewCell, {
  props: {
    namespacePath: 'test-namespace/test-dataset',
    currentBranch: 'feature/preview',
    ...props
  }
})

describe('DatasetPreviewCell', () => {
  it('renders embedded image bytes as a data URL', () => {
    const wrapper = mountCell({
      column: 'image',
      value: {
        bytes: 'aW1hZ2UtYnl0ZXM=',
        path: 'images/example.png'
      }
    })

    const image = wrapper.get('img')
    expect(image.attributes('src')).toBe('data:image/png;base64,aW1hZ2UtYnl0ZXM=')
    expect(image.attributes('alt')).toBe('images/example.png')
  })

  it('renders a top-level media byte array returned as Base64', () => {
    const wrapper = mountCell({
      column: 'sample_video',
      value: 'dmlkZW8tY29udGVudA=='
    })

    expect(wrapper.get('video').attributes('src')).toBe(
      'data:video/mp4;base64,dmlkZW8tY29udGVudA=='
    )
  })

  it('resolves repository audio paths using the selected branch', () => {
    const wrapper = mountCell({
      column: 'audio',
      value: {
        bytes: null,
        path: 'audio/sample.wav'
      }
    })

    expect(wrapper.get('audio').attributes('src')).toBe(
      '/datasets/test-namespace/test-dataset/resolve/feature%2Fpreview/audio/sample.wav'
    )
  })

  it('renders repository video paths', () => {
    const wrapper = mountCell({
      column: 'recording',
      value: {
        bytes: null,
        path: 'video/sample.mp4'
      }
    })

    expect(wrapper.get('video').attributes('src')).toContain('/video/sample.mp4')
  })

  it('renders sequences of media values', () => {
    const wrapper = mountCell({
      column: 'images',
      value: [
        { bytes: 'Zmlyc3Q=', path: 'first.jpg' },
        { bytes: 'c2Vjb25k', path: 'second.webp' }
      ]
    })

    expect(wrapper.findAll('img')).toHaveLength(2)
    expect(wrapper.findAll('img')[0].attributes('src')).toBe('data:image/jpeg;base64,Zmlyc3Q=')
    expect(wrapper.findAll('img')[1].attributes('src')).toBe('data:image/webp;base64,c2Vjb25k')
  })

  it('keeps non-media nested values readable as JSON', () => {
    const wrapper = mountCell({
      column: 'metadata',
      value: {
        labels: ['cat', 'speech'],
        score: 0.9
      }
    })

    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.text()).toContain('"labels"')
    expect(wrapper.text()).toContain('"speech"')
  })
})
