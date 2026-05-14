import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 用于文件上传的实例（不设 Content-Type，让浏览器自动设置 multipart boundary）
const uploadApi = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

function addAuthInterceptor(instance: ReturnType<typeof axios.create>) {
  // 请求拦截：自动注入 JWT
  instance.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  // 响应拦截：401 时先尝试刷新 token，失败则降级为 guest
  instance.interceptors.response.use(
    (res) => res,
    async (error) => {
      const original = error.config
      if (error.response?.status === 401 && !original._retry) {
        original._retry = true
        // 尝试用 refresh token 换取新的 access token
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          try {
            const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
            localStorage.setItem('access_token', data.access_token)
            localStorage.setItem('refresh_token', data.refresh_token)
            original.headers.Authorization = `Bearer ${data.access_token}`
            return instance(original)
          } catch {
            // refresh 失败，降级为 guest
          }
        }
        try {
          const { data } = await axios.post('/api/v1/auth/guest')
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return instance(original)
        } catch {
          localStorage.clear()
        }
      }
      return Promise.reject(error)
    }
  )
}

addAuthInterceptor(api)
addAuthInterceptor(uploadApi)

export default api
export { uploadApi }
