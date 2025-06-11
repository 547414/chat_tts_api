<template>
  <div>
    <div>hls video</div>
    <div ref="videoBox" style="margin-top: 16px"/>
  </div>
</template>

<script setup lang="ts">
import {ref, onMounted} from 'vue'
import Hls from 'hls.js'

const videoBox = ref<HTMLDivElement | null>(null)
const props = defineProps({
  initM3u8Url: {
    type: String,
    default: ''
  }
})

onMounted(() => {
  const m3u8Url = props.initM3u8Url

  const video = document.createElement('video')
  video.controls = true
  video.setAttribute('playsinline', 'true')
  video.setAttribute('webkit-playsinline', 'true')
  video.muted = true // 必须 muted 才能自动播放
  video.autoplay = true // 尝试自动播放
  video.style.width = '100%'
  // video.style.minHeight = '60px'
  video.style.backgroundColor = '#000'

  if (Hls.isSupported()) {
    console.log(1, 'HLS is supported')
    const hls = new Hls()
    hls.loadSource(m3u8Url)
    hls.attachMedia(video)
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      video.play().then(() => {
        setTimeout(() => {
          video.muted = false // 延后取消静音
        }, 500)
      }).catch((err) => {
        alert('播放失败: ' + err.message)
      })
    })
  } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
    console.log(2, 'HLS is supported by native player')
    video.src = m3u8Url
    video.addEventListener('canplay', () => {
      video.play().then(() => {
        setTimeout(() => {
          video.muted = false
        }, 500)
      }).catch((err) => {
        alert('播放失败: ' + err.message)
      })
    })
  } else {
    console.log(3, 'HLS is not supported')
    alert('此设备不支持 HLS 播放')
  }

  if (videoBox.value) {
    videoBox.value.innerHTML = ''
    videoBox.value.appendChild(video)
  }
})
</script>
