<template>
  <SpritePlayer
    v-if="visible"
    :src="ringImg"
    :rows="12"
    :columns="5"
    :fps="45"
    :width="size"
    :height="size"
    :totalFrames="60"
    :loop="0"
    :style="style"
  />
</template>

<script setup lang="js">
import { ref, watch, computed, onMounted } from 'vue'
import SpritePlayer from '@/component/SpritePlayer.vue'
// @ts-ignore
import getCaretCoordinates from 'textarea-caret';
import ringImg from '@/assets/sprite/ring.png'

const props = defineProps({
  // 目标 textarea 元素
  textarea: {
    type: Object,
    required: true
  },
  // 文本内容，用于触发位置更新
  text: {
    type: String,
    default: ''
  },
  // 是否显示
  visible: {
    type: Boolean,
    default: true
  },
  // 动画大小
  size: {
    type: Number,
    default: 44
  }
})

const caretX = ref(0)
const caretY = ref(0)

// 更新光标位置的逻辑
const updatePosition = () => {
  const textarea = props.textarea
  if (!textarea) return
  
  // 始终定位到文本末尾
  const pos = textarea.value.length
  const coords = getCaretCoordinates(textarea, pos)
  
  // 这里的偏移量 (16, 12) 保持与原逻辑一致
  caretX.value = coords.left + 16
  caretY.value = coords.top + 12
}

// 监听文本变化，自动更新位置
watch(() => props.text, () => {
  updatePosition()
})

// 监听可见性变化
watch(() => props.visible, (val) => {
  if (val) {
    setTimeout(updatePosition, 0)
  }
})

const style = computed(() => ({
  position: 'absolute',
  left: caretX.value + 'px',
  top: caretY.value + 'px',
  pointerEvents: 'none',
  zIndex: 9999
}))

// 暴露给父组件手动调用的方法
defineExpose({ updatePosition })

onMounted(() => {
  setTimeout(updatePosition, 100)
})
</script>
