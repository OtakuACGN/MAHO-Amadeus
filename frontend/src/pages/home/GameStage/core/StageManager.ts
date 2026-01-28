import * as PIXI from 'pixi.js'
import * as TWEEN from '@tweenjs/tween.js'
import { CharacterLayer } from './CharacterLayer'
import { BackgroundLayer } from './BackgroundLayer'

export class StageManager {
  public app: PIXI.Application
  public backgroundLayer: BackgroundLayer
  public characterLayer: CharacterLayer
  private tweenGroup: TWEEN.Group = new TWEEN.Group()
  private Live2DModel: any = null

  constructor(options: PIXI.IApplicationOptions) {
    this.app = new PIXI.Application(options)
    
    // 初始化层级
    this.backgroundLayer = new BackgroundLayer()
    this.characterLayer = new CharacterLayer(this.tweenGroup)

    // 添加到舞台 (背景在下，角色在上)
    this.app.stage.addChild(this.backgroundLayer.container)
    this.app.stage.addChild(this.characterLayer.container)

    // 启动动画循环
    this.app.ticker.add(() => {
      this.tweenGroup.update()
    })
  }

  public async initLive2D() {
    const { Live2DModel } = await import('pixi-live2d-display/cubism4')
    this.Live2DModel = Live2DModel
    window.PIXI = PIXI // cubism4 依赖全局 PIXI
  }

  public get screen() {
    return {
      width: this.app.screen.width,
      height: this.app.screen.height
    }
  }

  public resize() {
    this.backgroundLayer.resize(this.screen)
    // 角色位置目前使用比例同步，不需要额外的 resize 逻辑，除非想重排
  }

  public destroy() {
    this.app.destroy(true, { children: true, texture: true, baseTexture: true })
  }
}
