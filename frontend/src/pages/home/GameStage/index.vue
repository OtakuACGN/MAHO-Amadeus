<template>
  <div class="character-stage" ref="stageContainer"></div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useGameStore } from '@/stores/game'
import { storeToRefs } from 'pinia'
import { StageManager } from './core/StageManager'

const gameStore = useGameStore()
const { char, stage } = gameStore
const { activeCharacters } = storeToRefs(char)
const { background } = storeToRefs(stage)

const stageContainer = ref(null)
let stageManager = null

onMounted(async () => {
  // 1. 初始化管理器
  stageManager = new StageManager({
    backgroundAlpha: 0,
    resizeTo: window,
    resolution: window.devicePixelRatio || 1,
    autoDensity: true,
  })

  if (stageContainer.value) {
    stageContainer.value.appendChild(stageManager.app.view)
  }

  // 2. 加载 Live2D 运行库
  await stageManager.initLive2D()

  // 3. 初始同步背景与角色
  await syncAll()

  // 4. 监听变化
  watch(activeCharacters, () => stageManager.characterLayer.syncCharacters(
    activeCharacters.value, 
    stageManager.Live2DModel, 
    stageManager.screen
  ), { deep: true })

  watch(background, () => stageManager.backgroundLayer.syncBackground(
    background.value, 
    stageManager.screen
  ), { deep: true })

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (stageManager) {
    stageManager.destroy()
  }
  window.removeEventListener('resize', handleResize)
})

async function syncAll() {
  if (!stageManager) return
  
  await Promise.all([
    stageManager.backgroundLayer.syncBackground(background.value, stageManager.screen),
    stageManager.characterLayer.syncCharacters(activeCharacters.value, stageManager.Live2DModel, stageManager.screen)
  ])
}

function handleResize() {
  if (stageManager) {
    stageManager.resize()
  }
}
</script>

<style scoped>
.character-stage {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background-color: #000;
}
</style>