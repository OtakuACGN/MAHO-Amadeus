<template>
  <div>
    <CenterRevealMask :visible="showMask">
      <DialogBackground />
      <meswinName :name="currentName" class="Meswinname" />
      <DialogTextArea 
        :thinkText="thinkText"
        :isInputMode="isInputMode"
        :textQueue="textQueue"
        @send="handleSend"
      />
    </CenterRevealMask>
    <SiriWave :visible="showSiriWave" class="Siri-wave"/>
  </div>
</template>

<script setup lang="js">
import { useVADStore } from '@/stores/vad';
import { ref, onMounted, onUnmounted } from 'vue'
import CenterRevealMask from '@/component/CenterRevealMask.vue'
import DialogBackground from './DialogBackground.vue'
import meswinName from './meswinName.vue';
import SiriWave from './SiriWave.vue'
import DialogTextArea from './DialogTextArea.vue'

const props = defineProps({
  currentName: String,
  videoMode: Boolean,
  thinkText: String,
  isInputMode: Boolean,
  textQueue: Array
})

const emit = defineEmits(['send'])

const vadStore = useVADStore()

const showMask = ref(false)
const showSiriWave = ref(false)

function handleSend(payload) {
  emit('send', payload)
}

// 是否显示/隐藏对话框
const handleKeyDown = (e) => {
  if (e.key.toLowerCase() === 'h' && e.shiftKey) {
    if (showMask.value) {
      showMask.value = false;
    } else {
      showMask.value = true;
    }
  }
}

onMounted(() => {
  vadStore.initVAD()
  vadStore.onVoiceStart = () => {
    if (props.videoMode) {
      showMask.value = false
      showSiriWave.value = true
    }
  }
  vadStore.onVoiceEnd = () => {
    if (props.videoMode) {
      showMask.value = true
      showSiriWave.value = false
    }
  }

  window.addEventListener('keydown', handleKeyDown);
  setTimeout(() => {
    showMask.value = true
  }, 1000)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
})
</script>

<style>
.Meswinname {
  position: absolute;
  bottom: 40px;
  /* 改为固定像素 */
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}
</style>
