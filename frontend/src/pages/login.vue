<template>
  <audio ref="bgm" :src="loginMp3" autoplay loop></audio>
  <div class="login">
    <SpritePlayer class="logo" :src="spriteLogo" :rows="6" :columns="7" :fps="20" :width="logoSize"
      :height="logoSize" :totalFrames="38" :loop="1" />
    <div class="input-group">
      <div class="input-text">
        <div class="input-field">
          <span class="amadeus-label">USER ID</span>
          <input class="amadeus-input" type="text" v-model="username" autocomplete="username" />
        </div>
        <div class="input-field">
          <span class="amadeus-label">PASSWORD</span>
          <input class="amadeus-input" type="password" v-model="password" autocomplete="current-password" />
        </div>
      </div>
      <button class="amadeus-btn" @click="login">
        <img :src="loginButton" alt="登录" class="btn-img" />
      </button>
    </div>
    <p v-if="errorMsg" class="error">{{ errorMsg }}</p>
  </div>
</template>

<script setup>
import SpritePlayer from '../component/SpritePlayer.vue'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import config from '../config.json'
import loginMp3 from '@/assets/login/login.mp3'
import spriteLogo from '@/assets/sprite/sprite_logo.png'
import loginButton from '@/assets/login/login_button.png'

const router = useRouter()
const username = ref('')
const password = ref('')
const logoSize = ref(640)
const errorMsg = ref('')
const bgm = ref(null)

onMounted(() => {
  document.addEventListener('click', () => {
    if (bgm.value) {
      bgm.value.play()
    }
  }, { once: true })
})

async function login() {
  try {
    const response = await fetch(`http://${config.ip}:8080/api/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    })

    if (response.ok) {
      const data = await response.json()
      localStorage.setItem('token', data.token)
      localStorage.setItem('username', data.username)
      console.log('登录成功')
      router.push({ name: 'Home' })
    } else {
      const error = await response.json()
      errorMsg.value = error.detail || '登录失败'
    }
  } catch (e) {
    console.error('登录请求失败', e)
    errorMsg.value = '网络错误，请稍后重试'
  }
}
</script>

<style scoped>
.login {
  background-image: url('/bgLogin.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  min-height: 100vh;
  position: relative;
}

.logo {
  position: absolute;
  top: 15%;
  left: 50%;
  transform: translate(-50%, 0);
  /* 可根据需要调整 top 的百分比 */
  z-index: 0;
}

.input-group {
  position: absolute;
  top: 70%;
  left: 47%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  z-index: 1;
}

.input-text {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin-right: 1em;
}

.input-field {
  display: flex;
  margin-bottom: 1.2em;
}

.amadeus-btn {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  outline: none;
  transform: translateY(1.5em);
}

.btn-img {
  width: 2.8em;
  /* 按需调整 */
  transition: transform 0.2s cubic-bezier(.4, 2, .3, 1);
}

.amadeus-btn:hover .btn-img {
  transform: scale(1.13);
}

.amadeus-label {
  transform: translateY(0.26em);
  margin-right: 1em;
  display: flex;
  align-items: center;
  font-family: 'Cinzel', 'Times New Roman', serif;
  font-size: 1.8em;
  font-weight: 500;
  color: #f7c947;
  letter-spacing: 3px;
  margin-bottom: 0.4em;
  text-shadow:
    0 0 6px rgba(247, 201, 71, 0.8),
    0 0 14px rgba(247, 201, 71, 0.5),
    0 0 24px rgba(0, 0, 0, 0.9);
}

.amadeus-input {
  width: 20em;
  height: 1.6em;
  background: #000000;
  border: 2px solid #aaa9ab;
  color: #f7c947;
  padding: 0 1rem;
  font-family: 'Consolas', 'monospace';
  font-size: 1.8em;;
  letter-spacing: 2px;
  outline: none;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.8);
}

@media (max-width: 768px) {
  .amadeus-input {
    width: 12em;
  }
}

@media (max-width: 480px) {
  .amadeus-input {
    width: 8em;
  }
}

.error {
  color: red;
  margin-top: 1em;
  position: absolute;
  top: 75%;
  left: 50%;
  transform: translateX(-50%);
  font-size: 1.2rem;
}
</style>