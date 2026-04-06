<template>
  <div class="chapter-status-panel">
    <n-empty v-if="!chapter" description="请从左侧选择一个章节" style="margin-top: 48px" />

    <n-space v-else vertical :size="16" style="width: 100%; padding: 8px 4px">
      <n-card title="本章概览" size="small" :bordered="false">
        <n-descriptions :column="1" label-placement="left" size="small">
          <n-descriptions-item label="章节号">第 {{ chapter.number }} 章</n-descriptions-item>
          <n-descriptions-item label="标题">{{ chapter.title || '（无标题）' }}</n-descriptions-item>
          <n-descriptions-item label="收稿状态">
            <n-tag :type="chapter.word_count > 0 ? 'success' : 'default'" size="small" round>
              {{ chapter.word_count > 0 ? '已收稿' : '未收稿' }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="正文字数">{{ chapter.word_count ?? 0 }} 字</n-descriptions-item>
        </n-descriptions>
      </n-card>

      <n-alert v-if="readOnly" type="warning" :show-icon="true" title="托管运行中">
        全托管正在执行时，辅助撰稿区仅可阅读正文与关联信息，无法保存或改稿。请停止托管后再编辑。
      </n-alert>

      <n-text v-else depth="3" style="font-size: 12px">
        下方「人工审阅 / 正文结构」来自 API；「AI 生成质检」来自最近一次流式生成，一致性报告含问题、警告与建议。
      </n-text>

      <n-spin :show="metaLoading">
        <n-card
          v-if="slug"
          title="人工审阅（落库）"
          size="small"
          :bordered="false"
        >
          <n-empty
            v-if="chapterReview === null && !metaLoading"
            description="暂无审阅记录或尚未拉取"
            size="small"
          />
          <n-descriptions v-else-if="chapterReview" :column="1" label-placement="left" size="small">
            <n-descriptions-item label="状态">
              <n-tag size="small" round>{{ reviewStatusLabel(chapterReview.status) }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="备忘">
              <n-text style="font-size: 12px; white-space: pre-wrap">{{ chapterReview.memo || '—' }}</n-text>
            </n-descriptions-item>
            <n-descriptions-item v-if="chapterReview.updated_at" label="更新">
              {{ chapterReview.updated_at }}
            </n-descriptions-item>
          </n-descriptions>
          <n-text depth="3" class="meta-hint">
            与章节编辑页「审定」同源；GET/PUT
            <code class="inline-code">/novels/{id}/chapters/{n}/review</code>
          </n-text>
        </n-card>

        <n-card
          v-if="slug"
          title="正文结构分析"
          size="small"
          :bordered="false"
        >
          <n-empty
            v-if="chapterStructure === null && !metaLoading"
            description="暂无结构分析（或章节未生成正文）"
            size="small"
          />
          <n-descriptions v-else-if="chapterStructure" :column="1" label-placement="left" size="small">
            <n-descriptions-item label="分段数">{{ chapterStructure.paragraph_count ?? '—' }}</n-descriptions-item>
            <n-descriptions-item label="场景数">{{ chapterStructure.scene_count ?? '—' }}</n-descriptions-item>
            <n-descriptions-item label="对白占比">
              {{ chapterStructure.dialogue_ratio != null ? `${Math.round(chapterStructure.dialogue_ratio * 100)}%` : '—' }}
            </n-descriptions-item>
            <n-descriptions-item label="节奏">{{ pacingLabel(chapterStructure.pacing) }}</n-descriptions-item>
          </n-descriptions>
          <n-text depth="3" class="meta-hint">
            <code class="inline-code">GET …/chapters/{章节号}/structure</code>
          </n-text>
        </n-card>
      </n-spin>

      <n-card
        v-if="autopilotChapterReview"
        title="全托管 · 章末审阅"
        size="small"
        :bordered="false"
      >
        <n-descriptions :column="1" label-placement="left" size="small">
          <n-descriptions-item label="审阅章号">
            第 {{ autopilotChapterReview.chapter_number }} 章
            <n-tag
              v-if="chapter && chapter.number !== autopilotChapterReview.chapter_number"
              size="tiny"
              type="info"
              style="margin-left: 6px"
            >
              当前浏览为第 {{ chapter.number }} 章
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="张力（1–10）">{{ autopilotChapterReview.tension }}</n-descriptions-item>
          <n-descriptions-item label="叙事管线">
            <n-tag
              :type="autopilotChapterReview.narrative_sync_ok ? 'success' : 'warning'"
              size="small"
              round
            >
              {{ autopilotChapterReview.narrative_sync_ok ? '摘要/向量/伏笔已落库' : '同步失败或降级' }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="文风相似度">
            {{
              autopilotChapterReview.similarity_score != null
                ? Number(autopilotChapterReview.similarity_score).toFixed(3)
                : '—'
            }}
          </n-descriptions-item>
          <n-descriptions-item label="漂移告警">
            <n-tag :type="autopilotChapterReview.drift_alert ? 'error' : 'success'" size="small" round>
              {{ autopilotChapterReview.drift_alert ? '是（可能已触发删章重写）' : '否' }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item v-if="autopilotChapterReview.at" label="审阅时间">
            {{ autopilotChapterReview.at }}
          </n-descriptions-item>
        </n-descriptions>
        <n-text depth="3" style="font-size: 11px; display: block; margin-top: 8px">
          与守护进程 AUDITING 阶段一致：章后管线含叙事同步、文风、图谱推断与伏笔/三元组落库。
        </n-text>
      </n-card>

      <n-card
        v-if="lastWorkflowResult && qcChapterNumber != null"
        title="AI 生成质检"
        size="small"
        :bordered="false"
      >
        <n-space vertical :size="12">
          <n-alert
            v-if="chapter.number !== qcChapterNumber"
            type="info"
            :show-icon="true"
            style="font-size: 12px"
          >
            以下结果为最近一次针对「第 {{ qcChapterNumber }} 章」流式生成的质检摘要；当前浏览为第
            {{ chapter.number }} 章。切换到第 {{ qcChapterNumber }} 章可对照正文。
          </n-alert>

          <ConsistencyReportPanel
            :report="lastWorkflowResult.consistency_report"
            :token-count="lastWorkflowResult.token_count"
            @location-click="onLocationClick"
          />

          <n-collapse
            v-if="
              lastWorkflowResult.style_warnings && lastWorkflowResult.style_warnings.length > 0
            "
            class="cliche-collapse"
          >
            <n-collapse-item
              :title="`俗套句式命中 ${lastWorkflowResult.style_warnings.length} 处（点击展开）`"
              name="cliche"
            >
              <n-space vertical :size="6">
                <n-alert
                  v-for="(w, i) in lastWorkflowResult.style_warnings"
                  :key="i"
                  :type="w.severity === 'warning' ? 'warning' : 'info'"
                  :title="w.pattern"
                  style="font-size: 12px"
                >
                  「{{ w.text }}」
                </n-alert>
              </n-space>
            </n-collapse-item>
          </n-collapse>

          <n-collapse
            v-if="ghostAnnotationLines.length > 0"
            class="cliche-collapse"
          >
            <n-collapse-item :title="`冲突 / 幽灵批注 ${ghostAnnotationLines.length} 条`" name="ghost">
              <n-space vertical :size="6">
                <n-alert
                  v-for="(line, gi) in ghostAnnotationLines"
                  :key="gi"
                  type="warning"
                  style="font-size: 12px"
                >
                  {{ line }}
                </n-alert>
              </n-space>
            </n-collapse-item>
          </n-collapse>

          <n-space :size="8" wrap>
            <n-button size="small" quaternary @click="$emit('go-editor')">打开章节编辑</n-button>
            <n-button size="small" quaternary @click="$emit('clear-qc')">清除质检摘要</n-button>
          </n-space>
        </n-space>
      </n-card>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useMessage } from 'naive-ui'
import type { GenerateChapterWorkflowResponse } from '../../api/workflow'
import ConsistencyReportPanel from './ConsistencyReportPanel.vue'
import { chapterApi, type ChapterReviewDTO, type ChapterStructureDTO } from '../../api/chapter'

interface Chapter {
  id: number | string
  number: number
  title: string
  word_count: number
}

export interface AutopilotChapterAudit {
  chapter_number: number
  tension: number
  drift_alert: boolean
  similarity_score: number | null
  narrative_sync_ok: boolean
  at: string | null
}

const props = defineProps<{
  /** 作品 id，用于 chapter review / structure API */
  slug?: string
  chapter: Chapter | null
  readOnly?: boolean
  lastWorkflowResult?: GenerateChapterWorkflowResponse | null
  qcChapterNumber?: number | null
  /** 全托管章末审阅（与 /autopilot/status.last_chapter_audit 同源） */
  autopilotChapterReview?: AutopilotChapterAudit | null
}>()

defineEmits<{
  (e: 'clear-qc'): void
  (e: 'go-editor'): void
}>()

const message = useMessage()

const metaLoading = ref(false)
const chapterReview = ref<ChapterReviewDTO | null>(null)
const chapterStructure = ref<ChapterStructureDTO | null>(null)

const ghostAnnotationLines = computed(() => {
  const raw = props.lastWorkflowResult?.ghost_annotations
  if (!raw || !Array.isArray(raw) || raw.length === 0) return []
  const lines: string[] = []
  for (const item of raw) {
    if (item == null) continue
    if (typeof item === 'string') {
      lines.push(item)
      continue
    }
    if (typeof item === 'object') {
      const o = item as Record<string, unknown>
      const msg =
        (typeof o.message === 'string' && o.message) ||
        (typeof o.summary === 'string' && o.summary) ||
        (typeof o.text === 'string' && o.text) ||
        JSON.stringify(o)
      lines.push(msg)
    }
  }
  return lines
})

function reviewStatusLabel(s: string) {
  const m: Record<string, string> = {
    draft: '草稿',
    reviewed: '已审',
    approved: '已通过',
    pending: '待定',
  }
  return m[s] || s || '—'
}

function pacingLabel(p: string) {
  const m: Record<string, string> = {
    slow: '慢',
    medium: '中',
    fast: '快',
  }
  return m[p] || p || '—'
}

async function loadChapterMeta() {
  chapterReview.value = null
  chapterStructure.value = null
  if (!props.slug || !props.chapter) return
  metaLoading.value = true
  try {
    const [rev, struct] = await Promise.allSettled([
      chapterApi.getChapterReview(props.slug, props.chapter.number),
      chapterApi.getChapterStructure(props.slug, props.chapter.number),
    ])
    chapterReview.value = rev.status === 'fulfilled' ? rev.value : null
    chapterStructure.value = struct.status === 'fulfilled' ? struct.value : null
  } finally {
    metaLoading.value = false
  }
}

watch(
  () => [props.slug, props.chapter?.number] as const,
  () => {
    void loadChapterMeta()
  },
  { immediate: true }
)

function onLocationClick(location: number) {
  message.info(`问题位置约在第 ${location} 字附近，可在章节编辑中搜索或滚动查看。`)
}
</script>

<style scoped>
.chapter-status-panel {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  padding: 12px 20px 20px;
}

.cliche-collapse :deep(.n-collapse-item__header) {
  font-size: 13px;
}

.inline-code {
  font-size: 11px;
  padding: 1px 4px;
  border-radius: 4px;
  background: var(--n-code-color);
}

.meta-hint {
  display: block;
  margin-top: 10px;
  font-size: 11px;
  line-height: 1.45;
}
</style>
