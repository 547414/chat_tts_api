import {createApp} from 'vue'
import App from './App.vue'
import router from './router'
import {Icon} from '@iconify/vue';
import './public.scss'
import './style.css'
import 'vant/lib/index.css';
import {Notify} from 'vant';
// 桌面端适配
import '@vant/touch-emulator';

const app = createApp(App)

app.use(router)
app.use(Notify);

app.component('Icon', Icon)

app.mount('#app')
