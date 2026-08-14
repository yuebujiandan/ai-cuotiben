<script setup lang="ts">
import { ref } from 'vue'
import { questionApi } from '@/api/questions'
import RichText from '@/components/RichText.vue'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'created', count: number): void
}>()

const props = defineProps<{ notebookId?: number | null }>()

// 入口模式：pick=选择单题/多题；single=单题；multi=多题
const entryMode = ref<'pick' | 'single' | 'multi'>('pick')
const mode = ref<'photo' | 'text'>('photo')
const step = ref<'input' | 'ocr' | 'submitting'>('input')

const content = ref('')
const myAnswer = ref('')
const subject = ref('数学')
const sourceName = ref('')
const loading = ref(false)
const errorMsg = ref('')

// 多题拆分：每道题独立的勾选/编辑
const questions = ref<{ text: string; selected: boolean; my_answer: string }[]>([])

// ===== 入口选择 =====
function pickSingle() {
  entryMode.value = 'single'
  mode.value = 'text' // 单题默认手动输入（最快路径）
  resetFlow()
}
function pickMulti() {
  entryMode.value = 'multi'
  mode.value = 'photo'
  resetFlow()
}
function backToPick() {
  entryMode.value = 'pick'
  resetFlow()
}
function resetFlow() {
  step.value = 'input'
  content.value = ''
  myAnswer.value = ''
  sourceName.value = ''
  errorMsg.value = ''
  questions.value = []
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) handleFile(input.files[0])
  input.value = ''
}

async function onPaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return
  for (const it of items) {
    if (it.type.startsWith('image/')) {
      const f = it.getAsFile()
      if (f) {
        e.preventDefault()
        await handleFile(f)
        return
      }
    }
  }
}

async function handleFile(file: File) {
  loading.value = true
  errorMsg.value = ''
  step.value = 'input'
  try {
    const preview = await questionApi.ocrOnly(file)
    sourceName.value = preview.source
    const segs = preview.questions && preview.questions.length > 0 ? preview.questions : [preview.text]
    questions.value = segs.map((t) => ({ text: t, selected: true, my_answer: '' }))
    content.value = segs[0] || ''

    if (entryMode.value === 'multi') {
      // 多题模式：总是显示勾选列表
      step.value = 'ocr'
    } else {
      // 单题模式：识别出多题时提示切多题，单题直接进入确认
      step.value = 'ocr'
    }
  } catch (e) {
    errorMsg.value = (e as Error).message || 'OCR 识别失败，请重试'
  } finally {
    loading.value = false
  }
}

function toggleQuestion(i: number) {
  const q = questions.value[i]
  q.selected = !q.selected
}

function switchToMulti() {
  entryMode.value = 'multi'
  step.value = 'ocr'
}

async function submit() {
  if (entryMode.value === 'single') {
    // 单题：直接提交 content（手动输入已秒级，无需 OCR）
    if (!content.value.trim()) {
      errorMsg.value = '请输入题目内容'
      return
    }
    loading.value = true
    step.value = 'submitting'
    try {
      await questionApi.create({
        content: content.value,
        my_answer: myAnswer.value || undefined,
        subject: subject.value,
        notebook_id: props.notebookId ?? undefined
      })
      emit('created', 1)
    } catch (e) {
      errorMsg.value = (e as Error).message || '入库失败'
      step.value = 'ocr'
    } finally {
      loading.value = false
    }
    return
  }

  // 多题模式：每道勾选的题独立入库
  const selected = questions.value.filter((q) => q.selected)
  if (selected.length === 0) {
    errorMsg.value = '请至少勾选一道题'
    return
  }
  loading.value = true
  step.value = 'submitting'
  let okCount = 0
  try {
    for (const q of selected) {
      await questionApi.create({
        content: q.text,
        my_answer: q.my_answer || undefined,
        subject: subject.value,
        notebook_id: props.notebookId ?? undefined
      })
      okCount++
    }
    emit('created', okCount)
  } catch (e) {
    errorMsg.value = (e as Error).message || '入库失败'
    step.value = 'ocr'
  } finally {
    loading.value = false
  }
}

function switchToText() {
  mode.value = 'text'
  step.value = 'input'
  questions.value = []
}
</script>

<template>
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-[#2B3A67]/30 p-5" @click.self="emit('close')">
    <div class="card-base w-full max-w-[560px] rounded-modal shadow-lg">
      <div class="flex items-center justify-between border-b border-[#E3DCCF] px-6 py-4">
        <div class="flex items-center gap-2">
          <button v-if="entryMode !== 'pick'" class="mr-1 flex h-8 w-8 items-center justify-center rounded-btn text-[#6B6659] hover:bg-infobg hover:text-inkblue" aria-label="返回" @click="backToPick">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
          </button>
          <h3 class="text-lg text-[#2B2B28]">
            {{ entryMode === 'pick' ? '录入错题' : entryMode === 'single' ? '单题录入' : '多题录入' }}
          </h3>
        </div>
        <button class="flex h-9 w-9 items-center justify-center rounded-btn text-[#6B6659] hover:bg-infobg hover:text-inkblue" aria-label="关闭" @click="emit('close')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <!-- ===== 入口选择页 ===== -->
      <div v-if="entryMode === 'pick'" class="flex flex-col gap-3.5 px-6 py-8">
        <button class="card-base flex items-center gap-4 p-5 text-left transition-all hover:border-inkblue hover:shadow-paper" @click="pickSingle">
          <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-btn bg-infobg text-inkblue">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 3v12"/><path d="M8 11l4 4 4-4"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>
          </div>
          <div class="min-w-0">
            <div class="mb-0.5 text-[15px] font-medium text-[#2B2B28]">单题录入</div>
            <div class="text-[12.5px] leading-6 text-[#9A958A]">快速录入一道错题。手动输入秒级入库，无需等待识别</div>
          </div>
          <span class="ml-auto shrink-0 rounded-pill bg-success-bg px-2.5 py-1 text-[11px] font-medium text-success">最快</span>
        </button>

        <button class="card-base flex items-center gap-4 p-5 text-left transition-all hover:border-inkblue hover:shadow-paper" @click="pickMulti">
          <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-btn bg-infobg text-inkblue">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
          </div>
          <div class="min-w-0">
            <div class="mb-0.5 text-[15px] font-medium text-[#2B2B28]">多题录入</div>
            <div class="text-[12.5px] leading-6 text-[#9A958A]">拍照整张试卷，自动拆分多题，勾选后批量入库</div>
          </div>
          <span class="ml-auto shrink-0 rounded-pill bg-infobg px-2.5 py-1 text-[11px] font-medium text-inkblue">批量</span>
        </button>
      </div>

      <!-- ===== 单题 / 多题流程 ===== -->
      <template v-else>
        <div v-if="step === 'input'" class="flex gap-2 px-6 pt-4">
          <button class="rounded-btn px-[18px] py-[7px] text-[13px] transition-colors" :class="mode === 'photo' ? 'bg-inkblue text-[#FFFDF8]' : 'border border-[#E3DCCF] text-[#6B6659]'" @click="mode = 'photo'">拍照 / 截图</button>
          <button v-if="entryMode === 'single'" class="rounded-btn px-[18px] py-[7px] text-[13px] transition-colors" :class="mode === 'text' ? 'bg-inkblue text-[#FFFDF8]' : 'border border-[#E3DCCF] text-[#6B6659]'" @click="mode = 'text'">手动输入</button>
          <span v-else class="self-center text-[12px] text-[#9A958A]">多题请用拍照 / 截图</span>
        </div>

        <div class="px-6 py-4">
          <!-- OCR 识别中 -->
          <div v-if="loading && step === 'input'" class="flex flex-col items-center gap-3 py-8 text-center text-[13px] text-[#6B6659]">
            <div class="flex h-10 w-10 animate-spin items-center justify-center rounded-full border-4 border-[#E3DCCF] border-t-inkblue"></div>
            <p>正在识别图片中的题目…<br><span class="text-[12px] text-[#9A958A]">AI 视觉模型约需 1-2 分钟，请耐心等待</span></p>
          </div>

          <!-- 阶段1：选择文件 / 手输入口 -->
          <div v-if="step === 'input' && !loading">
            <label v-if="mode === 'photo'" class="flex cursor-pointer flex-col items-center rounded-modal border-2 border-dashed border-[#D8D2C2] px-5 py-9 text-center text-[#9A958A] transition-colors hover:border-inkblue hover:bg-infobg hover:text-inkblue">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" class="mb-2.5">
                <path d="M4 7h11l3 3h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z" /><circle cx="12" cy="13" r="3" />
              </svg>
              <p class="text-sm text-[#6B6659]">点击上传图片，或直接粘贴截图 (Ctrl+V)</p>
              <span class="text-xs">{{ entryMode === 'single' ? '识别后直接确认入库' : '识别后自动拆分多题' }}</span>
              <input type="file" accept="image/*" class="hidden" @change="onFileChange" />
            </label>
            <template v-else>
              <textarea
                v-model="content"
                rows="5"
                placeholder="粘贴或输入题目…"
                class="input-base w-full resize-none py-2.5"
                @paste="onPaste"
              ></textarea>
              <div class="mt-2">
                <label class="mb-1.5 block text-[12.5px] font-medium text-[#6B6659]" for="m-answer">我的答案（可选）</label>
                <textarea id="m-answer" v-model="myAnswer" rows="2" placeholder="输入作答内容，AI 将自动批改…" class="input-base w-full resize-none py-2.5"></textarea>
              </div>
              <div class="mt-2">
                <label class="mb-1.5 block text-[12.5px] font-medium text-[#6B6659]" for="m-subject2">学科</label>
                <select id="m-subject2" v-model="subject" class="input-base w-full">
                  <option>数学</option><option>物理</option><option>化学</option><option>英语</option><option>语文</option><option>生物</option>
                </select>
              </div>
            </template>
            <p v-if="errorMsg" class="mt-2 text-[12px] text-error">{{ errorMsg }}</p>
          </div>

          <!-- 阶段2：OCR 结果预览 -->
          <div v-else-if="step === 'ocr'" class="flex flex-col gap-4">
            <div class="flex items-center justify-between text-[12px]">
              <span class="text-success">
                <template v-if="questions.length > 1">已识别 {{ questions.length }} 道题</template>
                <template v-else>已识别，可在线修改</template>
              </span>
              <button class="text-inkblue underline-offset-2 hover:underline" @click="switchToText">重新上传</button>
            </div>

            <!-- 单题模式识别出多题 → 提示切多题 -->
            <div v-if="entryMode === 'single' && questions.length > 1" class="rounded-btn border border-warn bg-warn-bg px-4 py-3 text-[13px] text-[#6B6659]">
              这张图识别出 <b class="font-medium text-warn">{{ questions.length }}</b> 道题。
              <button class="ml-2 font-medium text-inkblue hover:underline" @click="switchToMulti">切换到多题模式批量入库 →</button>
            </div>

            <!-- 多题勾选列表 -->
            <div v-if="entryMode === 'multi' || questions.length > 1" class="flex flex-col gap-3">
              <div
                v-for="(q, i) in questions"
                :key="i"
                class="rounded-btn border p-3"
                :class="q.selected ? 'border-inkblue bg-infobg/30' : 'border-[#E3DCCF] bg-paper-card opacity-60'"
              >
                <div class="mb-2 flex items-center justify-between">
                  <label class="flex cursor-pointer items-center gap-2 text-[13px]">
                    <input type="checkbox" :checked="q.selected" class="h-4 w-4 accent-[#2B3A67]" @change="toggleQuestion(i)" />
                    第 {{ i + 1 }} 题
                  </label>
                </div>
                <textarea v-model="q.text" rows="3" class="input-base mb-2 w-full resize-none py-2 font-mono text-[12.5px]"></textarea>
                <input v-model="q.my_answer" type="text" placeholder="我的答案（可选）" class="input-base w-full py-1.5 text-[12.5px]" />
              </div>
            </div>

            <!-- 单题确认（单题模式 + 只有1题） -->
            <template v-else>
              <div>
                <label class="mb-1.5 block text-[12.5px] font-medium text-[#6B6659]">题目内容 <span class="text-[10px] text-[#9A958A]">(支持 LaTeX 公式，如 \(x^2+1\))</span></label>
                <textarea v-model="content" rows="5" class="input-base w-full resize-none py-2.5 font-mono text-[13px]"></textarea>
                <p v-if="sourceName" class="mt-1 text-[11px] text-[#9A958A]">来源：{{ sourceName }}</p>
              </div>
              <div>
                <label class="mb-1.5 block text-[12.5px] font-medium text-[#6B6659]" for="m-answer">我的答案（可选）</label>
                <textarea id="m-answer" v-model="myAnswer" rows="2" placeholder="输入作答内容，AI 将自动批改…" class="input-base w-full resize-none py-2.5"></textarea>
              </div>
            </template>

            <div>
              <label class="mb-1.5 block text-[12.5px] font-medium text-[#6B6659]" for="m-subject">学科</label>
              <select id="m-subject" v-model="subject" class="input-base w-full">
                <option>数学</option><option>物理</option><option>化学</option><option>英语</option><option>语文</option><option>生物</option>
              </select>
            </div>

            <details class="rounded-btn border border-dashed border-[#D8D2C2] px-3 py-2 text-[12px]">
              <summary class="cursor-pointer text-[#6B6659] hover:text-inkblue">预览效果</summary>
              <div class="mt-2 rounded bg-paper-fill p-3 text-[13px]">
                <RichText :text="questions[0]?.text || content" />
              </div>
            </details>
            <p v-if="errorMsg" class="text-[12px] text-error">{{ errorMsg }}</p>
          </div>

          <!-- 阶段3：提交中 -->
          <div v-else class="flex flex-col items-center gap-3 py-10 text-center text-[13px] text-[#6B6659]">
            <div class="flex h-10 w-10 animate-spin items-center justify-center rounded-full border-4 border-[#E3DCCF] border-t-inkblue"></div>
            <p>正在保存错题…</p>
          </div>
        </div>

        <div class="flex justify-end gap-2.5 border-t border-[#E3DCCF] px-6 py-4">
          <button class="btn btn-secondary btn-sm" @click="emit('close')">{{ step === 'submitting' ? '后台处理' : '取消' }}</button>
          <button v-if="step === 'input' && mode === 'text'" class="btn btn-primary btn-sm" :disabled="!content.trim() || loading" @click="submit">秒级入库</button>
          <button v-if="step === 'ocr' && (entryMode === 'multi' || questions.length > 1)" class="btn btn-primary btn-sm" :disabled="loading || !questions.some((q) => q.selected)" @click="submit">
            批量入库 {{ questions.filter((q) => q.selected).length }} 道题
          </button>
          <button v-if="step === 'ocr' && entryMode === 'single' && questions.length <= 1" class="btn btn-primary btn-sm" :disabled="!content.trim() || loading" @click="submit">确认入库并 AI 解析</button>
        </div>
      </template>
    </div>
  </div>
</template>
