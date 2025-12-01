<template>
  <div class="home-page">
    <SpritePlayer src="/sprite_logo.png" :rows="6" :columns="7" :fps="20" :width="200" :height="200" />
  </div>
</template>

<script setup>
import SpritePlayer from '@/component/SpritePlayer.vue';
</script>

<style scoped>
.home-page {
  background-image: url('/bg.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  min-height: 100vh;
}
</style>