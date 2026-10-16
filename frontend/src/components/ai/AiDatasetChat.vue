<template>
  <div class="fixed bottom-[24px] right-[24px] z-[1500] flex flex-col items-end gap-[12px]">
    <div
      v-if="open"
      class="flex h-[560px] w-[380px] flex-col overflow-hidden rounded-[12px] border border-gray-200 bg-white shadow-xl">
      <div class="flex items-center justify-between bg-brand-600 px-[16px] py-[12px] text-white">
        <span class="text-sm font-medium">{{ $t('aiChat.title') }}</span>
        <div class="flex items-center gap-[12px]">
          <button
            class="flex items-center justify-center opacity-80 hover:opacity-100"
            :title="$t('aiChat.minimize')"
            @click="open = false">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 8H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
            </svg>
          </button>
          <button
            class="flex items-center justify-center opacity-80 hover:opacity-100"
            :title="$t('aiChat.newChat')"
            @click="newChat">
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M7.5 2.5V12.5M2.5 7.5H12.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
            </svg>
          </button>
        </div>
      </div>

      <div ref="msgListRef" class="flex flex-1 flex-col gap-[12px] overflow-y-auto p-[16px]">
        <div class="max-w-[85%] self-start rounded-[8px] bg-gray-100 px-[12px] py-[8px] text-sm leading-[20px] text-gray-700">
          {{ $t('aiChat.welcome') }}
        </div>
        <template v-for="(msg, index) in messages" :key="index">
          <div
            v-if="msg.role === 'user'"
            class="max-w-[85%] self-end rounded-[8px] bg-brand-600 px-[12px] py-[8px] text-sm leading-[20px] text-white">
            {{ msg.content }}
          </div>
          <div v-else class="flex max-w-[92%] flex-col gap-[8px] self-start">
            <div
              class="markdown-body overflow-x-auto rounded-[8px] bg-gray-100 px-[12px] py-[8px] text-sm leading-[20px] text-gray-700"
              v-html="msg.content ? renderMarkdown(msg.content) : msg.loading ? $t('aiChat.searching') : ''">
            </div>
            <a
              v-for="ds in msg.datasets"
              :key="ds.namespace + '/' + ds.name"
              :href="`/datasets/${ds.namespace}/${ds.name}`"
              target="_blank"
              rel="noopener"
              class="block rounded-[8px] border border-gray-200 px-[12px] py-[8px] hover:border-brand-500">
              <div class="text-sm font-medium text-brand-600">{{ ds.namespace }}/{{ ds.name }}</div>
              <div v-if="ds.size || ds.created_at" class="mt-[2px] text-xs leading-[18px] text-gray-400">
                {{ ds.size ? formatBytes(ds.size) : '' }}{{ ds.size && ds.created_at ? ' · ' : '' }}{{ ds.created_at || '' }}
              </div>
              <div class="mt-[2px] line-clamp-2 text-xs leading-[18px] text-gray-500">{{ ds.description }}</div>
            </a>
          </div>
        </template>
      </div>

      <div class="flex items-center gap-[8px] border-t border-gray-200 p-[12px]">
        <input
          v-model="input"
          type="text"
          :placeholder="$t('aiChat.placeholder')"
          class="h-[36px] flex-1 rounded-[8px] border border-gray-300 px-[12px] text-sm outline-none focus:border-brand-500"
          :disabled="sending"
          @keyup.enter="send" />
        <button
          class="h-[36px] rounded-[8px] bg-brand-600 px-[16px] text-sm text-white disabled:opacity-50"
          :disabled="sending || !input.trim()"
          @click="send">
          {{ $t('aiChat.send') }}
        </button>
      </div>
    </div>

    <button
      v-if="!open"
      class="flex h-[48px] w-[48px] items-center justify-center rounded-full bg-brand-600 text-base font-semibold text-white shadow-lg hover:bg-brand-700"
      @click="open = true">
      AI
    </button>
  </div>
</template>

<script setup>
  import { inject, nextTick, ref } from 'vue'
  import { fetchEventSource } from '@microsoft/fetch-event-source'
  import { useI18n } from 'vue-i18n'
  import MarkdownIt from 'markdown-it'
  import { Typewriter } from '../../packs/typewriter'

  const mdParser = new MarkdownIt()
  const renderMarkdown = (content) => mdParser.render(content)

  const { t } = useI18n()
  const csghubServer = inject('csghubServer')

  const open = ref(false)
  const input = ref('')
  const sending = ref(false)
  const messages = ref([])
  const msgListRef = ref(null)

  const scrollBottom = () => {
    nextTick(() => {
      if (msgListRef.value) {
        msgListRef.value.scrollTop = msgListRef.value.scrollHeight
      }
    })
  }

  const newChat = () => {
    messages.value = []
  }

  const byteUnits = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']
  const formatBytes = (bytes) => {
    let level = 0
    let n = parseInt(bytes, 10) || 0
    while (n >= 1024 && ++level) {
      n = n / 1024
    }
    return n.toFixed(n < 10 && level > 0 ? 1 : 0) + ' ' + byteUnits[level]
  }

  const send = () => {
    const question = input.value.trim()
    if (!question || sending.value) return
    input.value = ''
    messages.value.push({ role: 'user', content: question })
    const answer = { role: 'assistant', content: '', datasets: [], loading: true }
    messages.value.push(answer)
    scrollBottom()
    sending.value = true

    const typewriter = new Typewriter((str) => {
      answer.content += str
      scrollBottom()
    })

    const history = messages.value
      .slice(0, -2)
      .filter((m) => (m.role === 'user' || m.role === 'assistant') && m.content)
      .map((m) => ({ role: m.role, content: m.content }))

    fetchEventSource(`${csghubServer}/api/v1/ai/dataset_chat`, {
      method: 'POST',
      openWhenHidden: true,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: question, history }),
      onopen(res) {
        if (res.ok) {
          typewriter.start()
        } else {
          throw new Error(`chat request failed: ${res.status}`)
        }
      },
      onmessage(msg) {
        const { data } = msg
        if (data === '[DONE]') {
          typewriter.done()
          return
        }
        try {
          const event = JSON.parse(data)
          if (event.type === 'text' && event.text) {
            typewriter.add(event.text)
          } else if (event.type === 'datasets' && Array.isArray(event.datasets)) {
            answer.datasets = event.datasets
          }
        } catch (e) {
          console.warn('bad chat event', e)
        }
        scrollBottom()
      },
      onclose() {
        typewriter.done()
        answer.loading = false
        sending.value = false
      },
      onerror(err) {
        typewriter.done()
        answer.loading = false
        if (!answer.content) {
          answer.content = t('aiChat.errorTip')
        }
        sending.value = false
        throw err
      }
    })
  }
</script>
