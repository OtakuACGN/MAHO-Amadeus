import * as PIXI from 'pixi.js'
import type { BackgroundConfig } from '@/stores/modules/stage'

export class BackgroundLayer {
  public container: PIXI.Container
  private sprite: PIXI.Sprite | null = null

  constructor() {
    this.container = new PIXI.Container()
    this.container.name = 'layer:background'
  }

  public async syncBackground(config: BackgroundConfig, screen: { width: number, height: number }) {
    if (!this.sprite || this.sprite.texture.baseTexture.cacheId !== config.path) {
      if (this.sprite) {
        this.container.removeChild(this.sprite)
        this.sprite.destroy()
      }
      
      const texture = PIXI.Texture.from(config.path)
      this.sprite = new PIXI.Sprite(texture)
      this.sprite.anchor.set(0.5)
      this.container.addChild(this.sprite)
    }

    if (this.sprite) {
      this.sprite.alpha = config.alpha ?? 1
      this.resize(screen)
    }
  }

  public resize(screen: { width: number, height: number }) {
    if (!this.sprite) return

    const screenRatio = screen.width / screen.height
    const bgRatio = this.sprite.texture.width / this.sprite.texture.height
    
    // Cover 逻辑
    if (screenRatio > bgRatio) {
      this.sprite.width = screen.width
      this.sprite.scale.y = this.sprite.scale.x
    } else {
      this.sprite.height = screen.height
      this.sprite.scale.x = this.sprite.scale.y
    }
    
    this.sprite.x = screen.width / 2
    this.sprite.y = screen.height / 2
  }
}
