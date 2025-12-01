<template>
  <div class="home-page">
    <dialogBox class="dialog" />
    <div class="meswin-bg"></div>
  </div>
</template>

<script setup>
import dialogBox from './dialogBox.vue'
import { onMounted } from 'vue'
import { useHomeStore } from '@/stores/home'

// 音频播放相关
const { audioQueue } = useHomeStore()

const playAudio = (blob) => {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    audio.onended = () => {
      URL.revokeObjectURL(url)
      resolve()
    }
    audio.onerror = (e) => {
      console.error('Audio playback error:', e)
      URL.revokeObjectURL(url)
      resolve()
    }
    audio.play().catch(e => {
      console.error('Play failed:', e)
      resolve()
    })
  })
}

const processAudioQueue = async () => {
  let audioBuffer = ''
  while (true) {
    if (audioQueue.length > 0) {
      const chunk = audioQueue.shift()
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

onMounted(() => {
  processAudioQueue()
})
</script>

<style scoped>
.home-page {
  background-image: url('/bg.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  min-height: 100vh;
  position: relative;
}

.dialog {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2;
}
</style>