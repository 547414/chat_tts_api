<template>
  <router-view v-slot="{ Component, route }">
    <keep-alive include="Folder">
      <component :is="Component" :key="route.fullPath"/>
    </keep-alive>
  </router-view>
</template>

<script setup lang="ts">
</script>