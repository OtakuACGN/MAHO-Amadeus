import type { Ref } from 'vue'

export function useLipSyncAudio(
  audioQueue: Ref<{ data: string; is_final: boolean }[]>,
  getAudioContext: () => AudioContext,
  onMouthOpen: (value: number) => void
) {
  // 音频分析器
  let analyser: AnalyserNode | null = null
  let dataArray: Uint8Array | null = null

  const initAudioContext = () => {
    const audioContext = getAudioContext()
    if (!analyser) {
      analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      dataArray = new Uint8Array(analyser.frequencyBinCount)
    }
    return audioContext
  }

  const playAudio = (blob: Blob) => {
    return new Promise<void>(async (resolve) => {
      const audioContext = initAudioContext()

      const arrayBuffer = await blob.arrayBuffer()
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

      const source = audioContext.createBufferSource()
      source.buffer = audioBuffer
      source.connect(analyser!)
      analyser!.connect(audioContext.destination)

      let animationId: number
      const updateLipSync = () => {
        if (!analyser || !dataArray) return
        analyser.getByteFrequencyData(dataArray)

        // 计算平均音量
        let sum = 0
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i]
        }
        const average = sum / dataArray.length

        // 增加门限防止一直张嘴 (底噪过滤)
        const threshold = 10
        let value = 0
        if (average > threshold) {
          value = Math.min(1, ((average - threshold) / (255 - threshold)) * 3.0)
        }

        onMouthOpen(value)

        animationId = requestAnimationFrame(updateLipSync)
      }

      source.onended = () => {
        cancelAnimationFrame(animationId)
        onMouthOpen(0) // 播放结束闭嘴
        resolve()
      }

      updateLipSync()
      source.start(0)
    })
  }

  const processAudioQueue = async () => {
    let audioBuffer = ''
    while (true) {
      if (audioQueue.value.length > 0) {
        const chunk = audioQueue.value.shift()
        if (chunk) {
          audioBuffer += chunk.data
          if (chunk.is_final) {
            try {
              const binaryString = window.atob(audioBuffer)
              const len = binaryString.length
              const bytes = new Uint8Array(len)
              for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i)
              }
              const blob = new Blob([bytes], { type: 'audio/wav' })
              await playAudio(blob)
            } catch (error) {
              console.error('音频播放失败:', error)
            } finally {
              audioBuffer = ''
            }
          }
        }
      } else {
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    }
  }

  return {
    processAudioQueue
  }
}
