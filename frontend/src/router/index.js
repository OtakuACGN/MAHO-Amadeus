import { createRouter, createWebHistory } from 'vue-router'
import config from '../config.json'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('../pages/home/home.vue'),
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../pages/login.vue'),
    }
  ],
})

// 异步路由守卫，通过 HTTP 接口校验 token
router.beforeEach(async (to, from, next) => {
  if (to.name !== 'Login') {
    const token = localStorage.getItem('token')
    if (!token) {
      next({ name: 'Login' })
      return
    }
    // 通过 HTTP 接口验证 token
    try {
      const response = await fetch(`http://${config.ip}:8080/api/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token })
      })
      
      if (!response.ok) {
        localStorage.removeItem('token')
        localStorage.removeItem('username')
        next({ name: 'Login' })
        return
      }
    } catch (e) {
      console.error('Token 验证失败', e)
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      next({ name: 'Login' })
      return
    }
  }
  next()
})

export default router
