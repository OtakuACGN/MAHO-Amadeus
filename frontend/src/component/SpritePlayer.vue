<template>
  <div
    :style="{
      width: width + 'px',
      height: height + 'px',
      overflow: 'hidden',
      position: 'relative',
      display: 'inline-block'
    }"
  >
    <img
      :src="src"
      :style="{
        position: 'absolute',
        left: -frameX * width + 'px',
        top: -frameY * height + 'px',
        width: columns * width + 'px',
        height: rows * height + 'px',
        imageRendering: 'pixelated'
      }"
      draggable="false"
      alt="sprite"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  src: { type: String, required: true },      // 图片路径
  rows: { type: Number, required: true },     // 行数
  columns: { type: Number, required: true },  // 列数
  fps: { type: Number, default: 12 },         // 帧率
  width: { type: Number, required: true },    // 单帧宽度
  height: { type: Number, required: true },   // 单帧高度
  totalFrames: { type: Number, required: true }, // 总帧数
  /**
   * 循环模式：0=无限循环，1=播放一次停止
   */
  loop: { type: Number, default: 0 }
})

const frame = ref(0)
let timer = null

const actualTotalFrames = computed(() =>
  props.totalFrames ?? (props.rows * props.columns)
)

const frameX = computed(() => frame.value % props.columns)
const frameY = computed(() => Math.floor(frame.value / props.columns))

function play() {
  timer = setInterval(() => {
    if (props.loop === 1 && frame.value >= actualTotalFrames.value - 1) {
      clearInterval(timer)
      timer = null
      return
    }
    frame.value = (frame.value + 1) % actualTotalFrames.value
  }, 1000 / props.fps)
}

onMounted(play)
onUnmounted(() => timer && clearInterval(timer))
watch(() => props.fps, (newFps) => {
  if (timer) clearInterval(timer)
  play()
})
</script>