<template>
  <n-modal
    v-model:show="modalShow"
    preset="card"
    style="width: min(720px, 96vw)"
    :mask-closable="false"
    :segmented="{ content: true, footer: 'soft' }"
    title="完整工作流撰稿"
  >
    <n-space vertical :size="14" class="gwm-body">
      <n-text depth="3" style="font-size: 12px">子项目 8：上下文构建 + LLM 生成 + 一致性检查</n-text>
      <n-form-item label="章节" :show-feedback="false">
        <n-select
          v-model:value="chapterNumber"
          :options="chapterOptions"
          placeholder="选择章号"
          :disabled="generating"
        />
      </n-form-item>
      <n-form-item label="本章大纲" :show-feedback="false">
        <n-input
          v-model:value="outline"
          type="textarea"
          placeholder="粘贴或编写本章大纲（必填）"
          :autosize="{ minRows: 5, maxRows: 14 }"
          :disabled="generating"
        />
      </n-form-item>

      <n-space v-if="!result" justify="end" :size="10">
        <n-button @click="close">取消</n-button>
        <n-button type="primary" :loading="generating" @click="runGenerate">生成</n-button>
      </n-space>

      <template v-else>
        <n-alert v-if="saveError" type="error" :title="saveError" />
        <ConsistencyReportPanel
          :report="result.consistency_report"
          :token-count="result.token_count"
          @location-click="onLocationClick"
        />
        <n-form-item label="正文（可编辑后再保存）" :show-feedback="false">
          <n-input
            v-model:value="editedContent"
            type="textarea"
            :autosize="{ minRows: 12, maxRows: 28 }"
            :disabled="saving"
          />
        </n-form-item>
        <n-space justify="end" :size="10">
          <n-button @click="resetResult">重新生成</n-button>
          <n-button type="primary" :loading="saving" @click="saveToChapter">保存到章节</n-button>
        </n-space>
      </template>
    </n-space>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { workflowApi, type GenerateChapterWorkflowResponse } from '../../api/workflow'
import { chapterApi } from '../../api/chapter'
import ConsistencyReportPanel from './ConsistencyReportPanel.vue'

export interface ChapterOption {
  id: number
  title: string
}

const props = defineProps<{
  show: boolean
  slug: string
  chapters: ChapterOption[]
  defaultChapterId?: number | null
}>()

const emit = defineEmits<{
  (e: 'update:show', v: boolean): void
  (e: 'saved'): void
}>()

const message = useMessage()

const modalShow = computed({
  get: () => props.show,
  set: (v: boolean) => {
    emit('update:show', v)
    if (!v) {
      result.value = null
      editedContent.value = ''
      outline.value = ''
    }
  },
})

const chapterNumber = ref<number | null>(null)
const outline = ref('')
const generating = ref(false)
const saving = ref(false)
const saveError = ref('')
const result = ref<GenerateChapterWorkflowResponse | null>(null)
const editedContent = ref('')

const chapterOptions = computed(() =>
  props.chapters.map(c => ({
    label: `第${c.id}章 ${c.title ? c.title.slice(0, 16) : ''}`,
    value: c.id,
  }))
)

watch(
  () => [props.show, props.chapters, props.defaultChapterId] as const,
  () => {
    if (!props.show) return
    const ch = props.chapters
    if (!ch.length) {
      chapterNumber.value = null
      return
    }
    const def = props.defaultChapterId
    if (def != null && ch.some(x => x.id === def)) {
      chapterNumber.value = def
    } else if (chapterNumber.value == null || !ch.some(x => x.id === chapterNumber.value)) {
      chapterNumber.value = ch[0].id
    }
  },
  { immediate: true }
)

watch(
  () => props.show,
  v => {
    if (!v) {
      generating.value = false
      saveError.value = ''
    }
  }
)

function close() {
  modalShow.value = false
}

function resetResult() {
  result.value = null
  editedContent.value = ''
  saveError.value = ''
}

async function runGenerate() {
  const n = chapterNumber.value
  const o = outline.value.trim()
  if (n == null) {
    message.warning('请选择章节')
    return
  }
  if (!o) {
    message.warning('请填写本章大纲')
    return
  }
  generating.value = true
  saveError.value = ''
  try {
    const data = await workflowApi.generateChapterWithContext(props.slug, {
      chapter_number: n,
      outline: o,
    })
    result.value = data
    editedContent.value = data.content || ''
    message.success('生成完成')
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    message.error(err.response?.data?.detail || err.message || '生成失败')
  } finally {
    generating.value = false
  }
}

async function saveToChapter() {
  const n = chapterNumber.value
  if (n == null) return
  const content = editedContent.value
  const title =
    props.chapters.find(c => c.id === n)?.title?.trim() || `第${n}章`
  saving.value = true
  saveError.value = ''
  try {
    await chapterApi.updateChapter(props.slug, n, { title, content })
    message.success('已保存到章节')
    emit('saved')
    emit('update:show', false)
    result.value = null
    editedContent.value = ''
    outline.value = ''
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    saveError.value = err.response?.data?.detail || err.message || '保存失败'
  } finally {
    saving.value = false
  }
}

function onLocationClick(location: number) {
  message.info(`问题位置标记：${location}（可在章节视图内对照）`)
}
</script>

<style scoped>
.gwm-body {
  width: 100%;
}
</style>
