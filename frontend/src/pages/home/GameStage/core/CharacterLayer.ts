import * as PIXI from 'pixi.js'
import { applyTransform } from '@/util/transform'
import type { CharacterConfig } from '@/stores/modules/character'
import * as TWEEN from '@tweenjs/tween.js'

export class CharacterLayer {
  public container: PIXI.Container
  private models: Map<string, any> = new Map()
  private tweenGroup: TWEEN.Group

  constructor(tweenGroup: TWEEN.Group) {
    this.container = new PIXI.Container()
    this.container.name = 'layer:characters'
    this.tweenGroup = tweenGroup
  }

  /**
   * 同步角色列表
   */
  public async syncCharacters(configs: CharacterConfig[], Live2DModel: any, screen: { width: number, height: number }) {
    const activeIds = configs.map(c => c.id)

    // 1. 移除不再需要的模型
    for (const [id, model] of this.models.entries()) {
      if (!activeIds.includes(id)) {
        this.container.removeChild(model)
        model.destroy()
        this.models.delete(id)
      }
    }

    // 2. 更新或增加模型
    for (const config of configs) {
      let model = this.models.get(config.id)

      if (!model) {
        // 创建新模型
        model = await Live2DModel.from(config.modelPath, { autoInteract: true })
        model.anchor.set(0.5, 0.5)
        this.container.addChild(model)
        this.models.set(config.id, model)
        
        // 启动眨眼动画
        this.startBlinking(model)
      }

      // 应用变换 (坐标使用归一化 -> 像素转换)
      applyTransform(model, {
        x: config.position?.x ?? 0.5,
        y: config.position?.y ?? 0.65,
        scale: config.scale ?? 0.4
      }, screen)
    }
  }

  /**
   * 更新口型同步
   */
  public updateLipSync(characterId: string | null, value: number) {
    if (!characterId) return
    const model = this.models.get(characterId)
    if (!model) return

    // 常见的 Live2D 嘴巴开口参数名
    const PARAM_MOUTH_OPEN_Y = 'ParamMouthOpenY'
    model.internalModel.coreModel.setParameterValueById(PARAM_MOUTH_OPEN_Y, value)
  }

  private startBlinking(model: any) {
    const PARAM_EYE_L_OPEN = 'ParamEyeROpen'
    const PARAM_EYE_R_OPEN = 'ParamEyeROpen2'
    
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
          new TWEEN.Tween({ val: 1 })
            .to({ val: 1 }, duration)
            .easing(TWEEN.Easing.Quadratic.InOut)
            .onUpdate(obj => {
              params[leftIdx] = obj.val
              if (rightIdx !== -1) params[rightIdx] = obj.val
            })
            .start(this.tweenGroup)
        })
        .start(this.tweenGroup)

      setTimeout(blink, Math.random() * 4000 + 2000)
    }
    
    blink()
  }
}
