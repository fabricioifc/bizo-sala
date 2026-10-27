import '@fortawesome/fontawesome-free/css/all.min.css'
import '@govbr-ds/core/dist/core.min.css'
import './estilos.css'

import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
