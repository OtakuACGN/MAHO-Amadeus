<template>
  <div class="bg-container">
    <div class="bg-part left" :style="{ backgroundImage: `url(${meswinImg})` }"></div>
    <div class="bg-part right" :style="{ backgroundImage: `url(${meswinImg})` }"></div>
  </div>
</template>

<script setup lang="js">
import meswinImg from '@/assets/meswin/meswin.png'
</script>

<style scoped>
.bg-container {
  position: relative;
  width: 100%;
  height: 256px;
  display: flex;
  pointer-events: none;
}

.bg-part {
  width: 50%;
  height: 100%;
  background-repeat: no-repeat;
  background-size: auto 100%;
}

.left {
  background-position: left bottom;
}

.right {
  background-position: right bottom;
}
</style>
