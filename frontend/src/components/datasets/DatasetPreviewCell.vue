<template>
  <div v-if="mediaItems.length" class="flex flex-wrap gap-2">
    <figure
      v-for="(item, index) in mediaItems"
      :key="`${item.source}-${index}`"
      class="m-0 max-w-full">
      <img
        v-if="item.kind === 'image'"
        :src="item.source"
        :alt="item.path || column"
        class="max-h-48 max-w-64 rounded object-contain"
        loading="lazy" />
      <audio
        v-else-if="item.kind === 'audio'"
        :src="item.source"
        class="max-w-64"
        controls
        preload="metadata" />
      <video
        v-else
        :src="item.source"
        class="max-h-48 max-w-64 rounded"
        controls
        preload="metadata" />
    </figure>
  </div>
  <span v-else class="whitespace-pre-wrap break-words">{{ displayValue }}</span>
</template>

<script setup>
  import { computed } from 'vue'

  const props = defineProps({
    value: {
      default: null
    },
    column: {
      type: String,
      default: ''
    },
    namespacePath: {
      type: String,
      default: ''
    },
    currentBranch: {
      type: String,
      default: 'main'
    }
  })

  const mediaExtensions = {
    image: ['apng', 'avif', 'bmp', 'gif', 'jpeg', 'jpg', 'png', 'svg', 'webp'],
    audio: ['aac', 'flac', 'm4a', 'mp3', 'oga', 'ogg', 'opus', 'wav'],
    video: ['avi', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'ogv', 'webm']
  }

  const mimeTypes = {
    apng: 'image/apng', avif: 'image/avif', bmp: 'image/bmp', gif: 'image/gif',
    jpeg: 'image/jpeg', jpg: 'image/jpeg', png: 'image/png', svg: 'image/svg+xml', webp: 'image/webp',
    aac: 'audio/aac', flac: 'audio/flac', m4a: 'audio/mp4', mp3: 'audio/mpeg',
    oga: 'audio/ogg', ogg: 'audio/ogg', opus: 'audio/ogg', wav: 'audio/wav',
    avi: 'video/x-msvideo', m4v: 'video/mp4', mkv: 'video/x-matroska', mov: 'video/quicktime',
    mp4: 'video/mp4', mpeg: 'video/mpeg', mpg: 'video/mpeg', ogv: 'video/ogg', webm: 'video/webm'
  }

  const extensionOf = (path = '') => {
    const cleanPath = path.split(/[?#]/)[0]
    const match = cleanPath.match(/\.([^.\/]+)$/)
    return match?.[1]?.toLowerCase() || ''
  }

  // sniffMime inspects the first bytes of base64-encoded media so embedded
  // previews keep the real container type (e.g. FLAC bytes must not be
  // declared as audio/wav, otherwise browsers refuse to play them).
  const sniffMime = (base64 = '') => {
    let bytes
    try {
      bytes = atob(base64.slice(0, 24))
    } catch {
      return ''
    }
    if (bytes.length < 4) return ''
    const startsWith = (sig) => bytes.startsWith(sig)
    if (startsWith('fLaC')) return 'audio/flac'
    if (startsWith('OggS')) return 'audio/ogg'
    if (startsWith('ID3') || (bytes.charCodeAt(0) === 0xff && (bytes.charCodeAt(1) & 0xe0) === 0xe0)) return 'audio/mpeg'
    if (startsWith('RIFF') && bytes.slice(8, 12) === 'WAVE') return 'audio/wav'
    if (startsWith('RIFF') && bytes.slice(8, 12) === 'WEBP') return 'image/webp'
    if (startsWith('\xff\xd8\xff')) return 'image/jpeg'
    if (startsWith('\x89PNG')) return 'image/png'
    if (startsWith('GIF8')) return 'image/gif'
    if (bytes.slice(4, 8) === 'ftyp') return 'video/mp4'
    return ''
  }

  const columnKind = (column) => {
    const match = column.toLowerCase().match(/(?:^|[_\-\s])(image|audio|video)s?(?:$|[_\-\s])/)
    return match?.[1] || ''
  }

  const kindFrom = (column, path) => {
    const extension = extensionOf(path)
    for (const [kind, extensions] of Object.entries(mediaExtensions)) {
      if (extensions.includes(extension)) return kind
    }
    return columnKind(column)
  }

  const repoFileUrl = (path) => {
    if (/^(https?:|data:|blob:)/i.test(path)) return path
    if (!props.namespacePath || !path) return ''
    const namespace = props.namespacePath.split('/').map(encodeURIComponent).join('/')
    const branch = encodeURIComponent(props.currentBranch || 'main')
    const filePath = path.split('/')
      .filter(segment => segment && segment !== '.' && segment !== '..')
      .map(encodeURIComponent)
      .join('/')
    return `/datasets/${namespace}/resolve/${branch}/${filePath}`
  }

  const mediaSource = (kind, path, bytes) => {
    const extension = extensionOf(path)
    const sniffed = bytes ? sniffMime(bytes) : ''
    const defaultMime = kind === 'image' ? 'image/png' : kind === 'audio' ? 'audio/wav' : 'video/mp4'
    return bytes
      ? `data:${sniffed || mimeTypes[extension] || defaultMime};base64,${bytes}`
      : repoFileUrl(path)
  }

  const toMediaItem = (value) => {
    if (typeof value === 'string') {
      const kind = kindFrom(props.column, value)
      if (!kind) return null
      if (/^data:(image|audio|video)\//i.test(value)) {
        return { kind, source: value, path: '' }
      }
      // absolute paths (e.g. "/Users/.../x.flac" cached paths from dataset
      // builders) cannot be resolved inside the repo, show them as plain text
      if (/^([a-z]:[\\/]|\/)/i.test(value)) return null
      if (/^(https?:|blob:)/i.test(value) || extensionOf(value)) {
        return { kind, source: repoFileUrl(value), path: value }
      }
      if (value.length >= 16 && value.length % 4 === 0 && /^[A-Za-z0-9+/]+={0,2}$/.test(value)) {
        return { kind, source: mediaSource(kind, '', value), path: '' }
      }
      return null
    }
    if (!value || typeof value !== 'object' || Array.isArray(value)) return null
    const pathValue = value.path ?? value.Path
    const bytesValue = value.bytes ?? value.Bytes
    const path = typeof pathValue === 'string' ? pathValue : ''
    const bytes = typeof bytesValue === 'string' ? bytesValue : ''
    const kind = kindFrom(props.column, path)
    if (!kind || (!path && !bytes)) return null

    const source = mediaSource(kind, path, bytes)
    if (!source) return null
    return { kind, source, path }
  }

  const mediaItems = computed(() => {
    const values = Array.isArray(props.value) ? props.value : [props.value]
    const items = values.filter(value => value != null).map(toMediaItem)
    return items.length && items.every(Boolean) ? items : []
  })

  const displayValue = computed(() => {
    if (props.value == null) return ''
    if (typeof props.value === 'string') return props.value
    if (typeof props.value === 'number' || typeof props.value === 'boolean') return String(props.value)
    try {
      return JSON.stringify(props.value, null, 2)
    } catch {
      return String(props.value)
    }
  })
</script>
