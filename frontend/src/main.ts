import 'primeicons/primeicons.css'
import './estilos.css'

import Aura from '@primeuix/themes/aura'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import { createApp } from 'vue'

import App from './App.vue'
import { localePtBr } from './locale'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: { preset: Aura, options: { darkModeSelector: 'system' } },
  locale: localePtBr,
})
app.use(ToastService)

app.mount('#app')
