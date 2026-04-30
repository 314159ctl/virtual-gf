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

  // 响应拦截：401 时尝试刷新 token
  instance.interceptors.response.use(
    (res) => res,
    async (error) => {
      const original = error.config
      if (error.response?.status === 401 && !original._retry) {
        original._retry = true
        const refresh = localStorage.getItem('refresh_token')
        if (refresh) {
          try {
            const res = await axios.post('/api/v1/auth/refresh', null, {
              params: { refresh_token: refresh },
            })
            const { access_token, refresh_token } = res.data
            localStorage.setItem('access_token', access_token)
            localStorage.setItem('refresh_token', refresh_token)
            original.headers.Authorization = `Bearer ${access_token}`
            return instance(original)
          } catch {
            localStorage.clear()
            window.location.href = '/login'
          }
        } else {
          localStorage.clear()
          window.location.href = '/login'
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
