import * as PIXI from 'pixi.js'

export interface TransformProps {
  x?: number
  y?: number
  scale?: number | { x: number; y: number }
  rotation?: number
  anchor?: number | { x: number; y: number }
  visible?: boolean
  alpha?: number
}

/**
 * 基础属性更新工具函数
 * @param target PIXI 对象
 * @param props 要更新的属性（可选）
 * @param screen 选传，用于处理归一化坐标转换 (0-1 -> pixel)
 */
export function applyTransform(
  target: PIXI.DisplayObject,
  props: TransformProps,
  screen?: { width: number; height: number }
) {
  if (props.x !== undefined) {
    target.x = screen ? props.x * screen.width : props.x
  }
  if (props.y !== undefined) {
    target.y = screen ? props.y * screen.height : props.y
  }

  if (props.scale !== undefined) {
    if (typeof props.scale === 'number') {
      target.scale.set(props.scale)
    } else {
      target.scale.set(props.scale.x, props.scale.y)
    }
  }

  if (props.rotation !== undefined) {
    target.rotation = props.rotation
  }

  if (props.visible !== undefined) {
    target.visible = props.visible
  }

  if (props.alpha !== undefined) {
    target.alpha = props.alpha
  }

  // 特殊处理支持 anchor 的对象
  if (props.anchor !== undefined && 'anchor' in target) {
    const t = target as any
    if (typeof props.anchor === 'number') {
      t.anchor.set(props.anchor)
    } else {
      t.anchor.set(props.anchor.x, props.anchor.y)
    }
  }
}
