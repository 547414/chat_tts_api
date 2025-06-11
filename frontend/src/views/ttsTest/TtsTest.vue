<template>
  <div class="tts-page">
    <van-nav-bar title="语音合成（自动播放）"/>
    <div class="tts-page-content">
      <van-cell-group inset>
        <van-field
            v-model="text"
            type="textarea"
            label="输入文本"
            placeholder="请输入中文"
            :autosize="{ minHeight: 80, maxHeight: 110 }"
        />
        <van-field v-model="speaker" label="音色文件名" placeholder="如 seed_648.pt"/>
        <van-field v-model="temperature" label="temperature" type="number"/>
        <van-field v-model="top_p" label="top_p" type="number"/>
        <van-field v-model="top_k" label="top_k" type="digit"/>
        <van-field v-model="prompt" label="风格提示"/>
        <van-field v-model="lang" label="语言"/>
        <van-field label="跳过精修" input-align="right">
          <template #input>
            <van-switch v-model="skipRefineText"/>
          </template>
        </van-field>
        <van-field label="使用解码器" input-align="right">
          <template #input>
            <van-switch v-model="useDecoder"/>
          </template>
        </van-field>
        <van-field label="文本规范化" input-align="right">
          <template #input>
            <van-switch v-model="doTextNormalization"/>
          </template>
        </van-field>
        <van-field label="同音替换" input-align="right">
          <template #input>
            <van-switch v-model="doHomophoneReplacement"/>
          </template>
        </van-field>
      </van-cell-group>
      <div style="padding: 16px">
        <div class="btn-box">
          <van-button type="primary" block :loading="loading" @click="playTTS">
            合成语音
          </van-button>
        </div>
        <div>-----------------------------</div>
        showHlsVideo: {{ !showHlsVideo }}
        <!--    <div v-if="showHlsVideo" style="visibility: hidden; height: 0">-->
        <div v-if="showHlsVideo">
          <HlsVideo :initM3u8Url="m3u8Url"/>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import md5 from 'blueimp-md5'
import HlsVideo from "@/views/ttsTest/HlsVideo.vue";
import {notifyError} from "@/utils/notify.ts";

const text = ref('以后的许多年里，我不断悟出这话的深意。琳，你真的太聪明了，早在几年前，你就嗅出了知识界的政治风向，做出了一些超前的举动，比如你在教学中，把大部分物理定律和参数都改了名字，欧姆定律改叫电阻定律，麦克斯韦方程改名成电磁方程，普朗克常数叫成了量子常数……你对学生们解释说：所有的科学成果都是广大劳动人民智慧的结晶，那些资产阶级学术权威不过是窃取了这些智慧。但即使这样，你仍然没有被"革命主流"所接纳，看看现在的你，衣袖上没有"革命教职员工"都戴着的红袖章；你两手空空地上来，连一本语录都没资格拿……谁让你出生在旧中国那样一个显赫的家庭，你父母又都是那么著名的学者。')

const speaker = ref('seed_648')
const temperature = ref(0.3)
const top_p = ref(0.7)
const top_k = ref(20)
const prompt = ref('[oral_2][break_6]')
const lang = ref('zh')
const skipRefineText = ref(true)
const useDecoder = ref(true)
const doTextNormalization = ref(true)
const doHomophoneReplacement = ref(true)
const loading = ref(false)
const showHlsVideo = ref(false)
const m3u8Url = ref()

const generateFileName = (fileName: string) => {
  const now = new Date()
  const pad = (n: number) => n.toString().padStart(2, '0')
  const formattedDate = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`
  const randomBytes = window.crypto.getRandomValues(new Uint8Array(4))
  const randomStr = Array.from(randomBytes).map(b => b.toString(16).padStart(2, '0')).join('')
  const combinedStr = formattedDate + randomStr
  const hash = md5(combinedStr)
  return `${formattedDate}_${hash}_${fileName}`
}

const playTTS = async () => {
  if (!text.value.trim()) return notifyError('请输入文本')
  if (!speaker.value.trim()) return notifyError('请输入音色文件名')
  loading.value = true
  showHlsVideo.value = false
  const fileName = generateFileName('chattts.mp3')
  const BACKEND_API_KEY = import.meta.env.BACKEND_API_KEY
  const res = await fetch(`${import.meta.env.VITE_APP_BASE_API}/api/chat_tts/proxy_hls`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${BACKEND_API_KEY}`
    },
    body: JSON.stringify({
      text: text.value,
      speaker: speaker.value,
      temperature: temperature.value,
      top_p: top_p.value,
      top_k: top_k.value,
      prompt: prompt.value,
      lang: lang.value,
      do_text_normalization: doTextNormalization.value,
      do_homophone_replacement: doHomophoneReplacement.value,
      skip_refine_text: skipRefineText.value,
      use_decoder: useDecoder.value,
      file_name: fileName
    })
  })

  const data = await res.json()
  m3u8Url.value = `${import.meta.env.VITE_APP_BASE_API}${data.m3u8}`
  console.log(m3u8Url.value)
  loading.value = false
  showHlsVideo.value = true
  loading.value = false
}
</script>

<style scoped lang="scss">
.tts-page {
  width: 100vw;
  background-color: #f5f5f5;
}

.tts-page-content {
  padding: 16px 0;
  height: calc(100vh - 48px);
  overflow-y: auto;
}
</style>
