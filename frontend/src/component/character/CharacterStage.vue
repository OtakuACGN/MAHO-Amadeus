<template>
  <div class="character-stage" ref="stageContainer"></div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as PIXI from 'pixi.js'
import * as TWEEN from '@tweenjs/tween.js'
import { useGameStore } from '@/stores/game'
import { storeToRefs } from 'pinia'

const gameStore = useGameStore()
const { char, audio } = gameStore
const { activeCharacters } = storeToRefs(char)
const { mouthOpen, speakingCharacterId } = storeToRefs(audio)

const stageContainer = ref(null)
let app = null
let background = null
let models = new Map() // 存储当前显示的 Live2D 模型
let tweenGroup = new TWEEN.Group()

// 常用参数名映射（后续可移至配置）
const PARAM_MOUTH_OPEN = 'ParamMouthOpenY'
const PARAM_EYE_L_OPEN = 'ParamEyeROpen'
const PARAM_EYE_R_OPEN = 'ParamEyeROpen2'

onMounted(async () => {
  window.PIXI = PIXI
  const { Live2DModel } = await import('pixi-live2d-display/cubism4')

  // 1. 初始化 PIXI 应用
  app = new PIXI.Application({
    backgroundAlpha: 0,
    resizeTo: window,
    resolution: window.devicePixelRatio || 1,
    autoDensity: true,
  })

  if (stageContainer.value) {
    stageContainer.value.appendChild(app.view)
  }

  // 2. 加载背景
  await loadBackground()

  // 3. 初始加载角色
  await updateModels(Live2DModel)

  // 4. 动画循环
  app.ticker.add(() => {
    tweenGroup.update()
  })

  // 5. 监听角色列表变化
  watch(activeCharacters, () => updateModels(Live2DModel), { deep: true })

  // 6. 监听嘴部动作
  watch([mouthOpen, speakingCharacterId], ([mVal, sId]) => {
    models.forEach((model, id) => {
      const val = (id === sId) ? mVal : 0
      const coreModel = model.internalModel.coreModel
      const paramIds = coreModel._parameterIds
      const params = coreModel._model.parameters.values
      const idx = paramIds.indexOf(PARAM_MOUTH_OPEN)
      if (idx !== -1) {
        params[idx] = val
      }
    })
  })

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (app) {
    app.destroy(true, { children: true, texture: true, baseTexture: true })
  }
  window.removeEventListener('resize', handleResize)
})

async function loadBackground() {
  const bgTexture = PIXI.Texture.from('/bg.png')
  background = new PIXI.Sprite(bgTexture)
  background.anchor.set(0.5)
  handleResize()
  app.stage.addChildAt(background, 0)
}

function handleResize() {
  if (!background || !app) return
  
  // 背景 Cover 逻辑
  const screenRatio = app.screen.width / app.screen.height
  const bgRatio = background.texture.width / background.texture.height
  
  if (screenRatio > bgRatio) {
    background.width = app.screen.width
    background.scale.y = background.scale.x
  } else {
    background.height = app.screen.height
    background.scale.x = background.scale.y
  }
  
  background.x = app.screen.width / 2
  background.y = app.screen.height / 2
  
  // 更新角色位置（简单平铺布局）
  let idx = 0
  models.forEach(model => {
    const total = models.size
    const step = app.screen.width / (total + 1)
    model.x = step * (idx + 1)
    model.y = app.screen.height * 0.65 // 稍微靠下显示
    idx++
  })
}

async function updateModels(Live2DModel) {
  // 找出需要删除的角色
  const activeIds = activeCharacters.value.map(c => c.id)
  for (const [id, model] of models.entries()) {
    if (!activeIds.includes(id)) {
      app.stage.removeChild(model)
      model.destroy()
      models.delete(id)
    }
  }

  // 找出需要添加或更新的角色
  for (const charConfig of activeCharacters.value) {
    if (!models.has(charConfig.id)) {
      const model = await Live2DModel.from(charConfig.modelPath, {
        autoInteract: true
      })
      
      model.anchor.set(0.5, 0.5)
      model.scale.set(charConfig.scale || 0.4)
      
      // 初始位置设置
      app.stage.addChild(model)
      models.set(charConfig.id, model)
      
      // 启动自动眨眼
      startBlinking(model)
    }
  }
  
  handleResize()
}

function startBlinking(model) {
  const coreModel = model.internalModel.coreModel
  const paramIds = coreModel._parameterIds
  const params = coreModel._model.parameters.values
  
  const leftIdx = paramIds.indexOf(PARAM_EYE_L_OPEN)
  const rightIdx = paramIds.indexOf(PARAM_EYE_R_OPEN) || paramIds.indexOf(PARAM_EYE_R_OPEN + '2')

  if (leftIdx === -1) return

  const blink = () => {
    const duration = 120
    const tween = new TWEEN.Tween({ val: params[leftIdx] })
      .to({ val: 0 }, duration)
      .easing(TWEEN.Easing.Quadratic.InOut)
      .onUpdate(obj => {
        params[leftIdx] = obj.val
        if (rightIdx !== -1) params[rightIdx] = obj.val
      })
      .onComplete(() => {
        new TWEEN.Tween({ val: 0 })
          .to({ val: 1 }, duration)
          .easing(TWEEN.Easing.Quadratic.InOut)
          .onUpdate(obj => {
            params[leftIdx] = obj.val
            if (rightIdx !== -1) params[rightIdx] = obj.val
          })
          .start(tweenGroup)
      })
      .start(tweenGroup)

    setTimeout(blink, Math.random() * 4000 + 2000)
  }
  
  blink()
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