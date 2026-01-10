<template>
  <div class="pixi-container"></div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import * as PIXI from 'pixi.js'
import * as TWEEN from '@tweenjs/tween.js'
import { useHomeStore } from '@/stores/home'
import { storeToRefs } from 'pinia'
import config from '@/config.json'

const homeStore = useHomeStore()
const { mouthOpen } = storeToRefs(homeStore)

let currentParams = null
let mouthOpenIndex = -1

onMounted(async () => {
  window.PIXI = PIXI
  const { Live2DModel } = await import('pixi-live2d-display/cubism4')

  const app = new PIXI.Application({
    backgroundAlpha: 0,
    resizeTo: window,
    resolution: 3,
    autoDensity: true,
  })

  document.querySelector('.pixi-container').appendChild(app.view)

  // 鼠标跟踪状态
  let autoInteractEnabled = false

  // tween动画组和定时器句柄
  let tweenGroup = null
  let listeners = [] // 监听器列表，包含定时器和事件监听器

  // 参数缓动动画函数（复用）
  function animateParam(params, paramIndex, toValue, duration, easing = TWEEN.Easing.Quadratic.InOut) {
    const fromValue = params[paramIndex]
    const tween = new TWEEN.Tween({ value: fromValue })
      .to({ value: toValue }, duration)
      .easing(easing)
      .onUpdate(obj => {
        params[paramIndex] = obj.value
      })
      .start()
    tweenGroup.add(tween)
    return tween
  }

  // 创建模型的函数 ========================= 之所以写一个函数，是因为autoInteract这个参数只在创建模型的时候有用
  async function createModel() {
    // 销毁现有模型和清理监听器
    if (app.stage.children.length > 0) {
      app.stage.children.forEach(child => {
        if (child.destroy) {
          child.destroy()
        }
      })
      app.stage.removeChildren()
    }
    
    // 清理所有监听器
    listeners.forEach(cleanup => cleanup())
    listeners = []

    // 加载 Cubism 4 模型
    const model = await Live2DModel.from(config.modelPath, {
      autoInteract: autoInteractEnabled
    })
    model.x = app.screen.width / 2
    model.y = app.screen.height / 1.8
    model.scale.set(0.4)
    model.anchor.set(0.5, 0.5)
    app.stage.addChild(model)

    // 获取参数
    const coreModel = model.internalModel.coreModel
    const paramIds = coreModel._parameterIds
    const params = coreModel._model.parameters.values
    
    // 更新全局引用
    currentParams = params
    mouthOpenIndex = paramIds.indexOf('ParamMouthOpenY')
    
    console.log('模型参数列表:', paramIds)

    // tween动画组
    tweenGroup = new TWEEN.Group()
    app.ticker.add(() => {
      tweenGroup.update()
    })

    // 眨眼函数
    function blink() {
      const leftEyeIndex = paramIds.indexOf('ParamEyeROpen')
      const rightEyeIndex = paramIds.indexOf('ParamEyeROpen2')
      if (leftEyeIndex === -1 || rightEyeIndex === -1) {
        // 兼容部分模型参数名不同
        console.warn('未找到眨眼参数')
        return
      }
      const leftOriginal = params[leftEyeIndex]
      const rightOriginal = params[rightEyeIndex]
      // 闭眼
      animateParam(params, leftEyeIndex, 0, 120)
      animateParam(params, rightEyeIndex, 0, 120)
      // 150ms 后睁眼
      setTimeout(() => {
        animateParam(params, leftEyeIndex, leftOriginal, 120)
        animateParam(params, rightEyeIndex, rightOriginal, 120)
      }, 150)
    }

    // 自动眨眼定时器
    const blinkTimer = setInterval(() => {
      const delay = Math.random() * 3000 + 2000
      setTimeout(() => {
        blink()
      }, delay)
    }, 5000)

    // 添加到监听器列表
    listeners.push(() => clearInterval(blinkTimer))

    console.log('模型已重新加载，鼠标跟踪:', autoInteractEnabled ? '开启' : '关闭')
    return model
  }
  // 创建模型的函数 =================================================================== 结束

  // 初始创建模型
  let model = await createModel()

  // 监听嘴部张开状态
  watch(mouthOpen, (newValue) => {
    if (currentParams && mouthOpenIndex !== -1) {
      currentParams[mouthOpenIndex] = newValue
    }
  })

  // 添加键盘开关(按 'T' 键切换鼠标跟踪)
  window.addEventListener('keydown', async (e) => {
    if (e.key === 't' || e.key === 'T') {
      autoInteractEnabled = !autoInteractEnabled
      model = await createModel()
    }
  })
})
</script>