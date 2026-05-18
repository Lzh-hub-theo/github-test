<script setup>
import { ref, onMounted } from 'vue'

const sentence = ref('')
const author = ref('')
const origin = ref('')
const loading = ref(true)
const error = ref(null)

const fetchPoetry = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await fetch('https://v1.jinrishici.com/all.json')
    const data = await res.json()
    sentence.value = data.content
    author.value = data.author
    origin.value = data.origin
  } catch (e) {
    error.value = '获取失败，请重试'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchPoetry()
})
</script>

<template>
  <div class="ink-bg">
    <div class="ink-layer"></div>
    <div class="mountain mountain-1"></div>
    <div class="mountain mountain-2"></div>
    <div class="mountain mountain-3"></div>

    <main class="container">
      <header class="title-section">
        <h1 class="title">每日一句</h1>
        <div class="title-underline"></div>
      </header>

      <section class="poetry-section">
        <div v-if="loading" class="loading">
          <span class="loading-dot"></span>
          <span class="loading-dot"></span>
          <span class="loading-dot"></span>
        </div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <div v-else class="poetry-card">
          <div class="quote-wrapper">
            <span class="quote-mark quote-mark-left">「</span>
            <p class="sentence">{{ sentence }}</p>
            <span class="quote-mark quote-mark-right">」</span>
          </div>
          <div class="divider"></div>
          <p class="info">{{ author }}《{{ origin }}》</p>
        </div>
      </section>

      <button class="refresh-btn" @click="fetchPoetry" :disabled="loading">
        <span class="btn-text">换一句</span>
        <span class="btn-icon">✦</span>
      </button>

      <footer class="seal">詩</footer>
    </main>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@300;400;600&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  height: 100%;
  overflow-x: hidden;
}

body {
  background: linear-gradient(135deg, #f5f0e8 0%, #e8e0d5 50%, #f0ebe3 100%);
  margin: 0;
}

#app {
  width: 100%;
  max-width: 100%;
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  text-align: center;
}

.ink-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f0e8 0%, #e8e0d5 50%, #f0ebe3 100%);
  position: relative;
  overflow: hidden;
  font-family: 'Noto Serif SC', serif;
}

.ink-layer {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 50% at 20% 80%, rgba(45, 55, 45, 0.03) 0%, transparent 50%),
    radial-gradient(ellipse 60% 40% at 80% 20%, rgba(45, 55, 45, 0.04) 0%, transparent 40%);
  pointer-events: none;
}

.mountain {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 40vh;
  opacity: 0.06;
}

.mountain::before {
  content: '';
  position: absolute;
  bottom: 0;
  border-style: solid;
}

.mountain-1::before {
  left: -10%;
  border-width: 0 25vw 35vh 50vw;
  border-color: transparent transparent #2d3d2d transparent;
}

.mountain-2::before {
  right: -5%;
  border-width: 0 30vw 45vh 40vw;
  border-color: transparent transparent #3d4a3d transparent;
}

.mountain-3::before {
  left: 30%;
  border-width: 0 20vw 30vh 35vw;
  border-color: transparent transparent #4a5a4a transparent;
}

.container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8vh 5vw;
  position: relative;
  z-index: 1;
}

.title-section {
  text-align: center;
  margin-bottom: 8vh;
  opacity: 0;
  animation: fadeInDown 1s ease-out 0.3s forwards;
}

.title {
  font-family: 'Ma Shan Zheng', cursive;
  font-size: clamp(2.5rem, 6vw, 4rem);
  color: #2d3d2d;
  letter-spacing: 0.3em;
  margin-bottom: 1rem;
}

.title-underline {
  width: 3em;
  height: 2px;
  background: linear-gradient(90deg, transparent, #2d3d2d, transparent);
  margin: 0 auto;
}

.poetry-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 800px;
  opacity: 0;
  animation: fadeIn 1.2s ease-out 0.6s forwards;
}

.poetry-card {
  text-align: center;
  padding: 3rem 4rem;
  position: relative;
}

.quote-wrapper {
  position: relative;
  display: inline-block;
}

.quote-mark {
  font-family: 'Ma Shan Zheng', cursive;
  font-size: 4rem;
  color: rgba(45, 61, 45, 0.15);
  position: absolute;
  line-height: 1;
}

.quote-mark-left {
  top: -1rem;
  left: -2rem;
}

.quote-mark-right {
  bottom: -1.5rem;
  right: -2rem;
}

.sentence {
  font-family: 'Ma Shan Zheng', cursive;
  font-size: clamp(1.8rem, 4vw, 2.8rem);
  color: #3d4a3d;
  line-height: 1.8;
  letter-spacing: 0.1em;
  margin: 1.5rem 0;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
}

.divider {
  width: 4em;
  height: 1px;
  background: linear-gradient(90deg, transparent, #8b9a8b, transparent);
  margin: 2rem auto;
}

.info {
  font-family: 'Noto Serif SC', serif;
  font-size: 1rem;
  font-weight: 300;
  color: #6b7b6b;
  letter-spacing: 0.2em;
}

.loading {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.loading-dot {
  width: 8px;
  height: 8px;
  background: #8b9a8b;
  border-radius: 50%;
  animation: loadingPulse 1.4s ease-in-out infinite;
}

.loading-dot:nth-child(2) { animation-delay: 0.2s; }
.loading-dot:nth-child(3) { animation-delay: 0.4s; }

.error {
  color: #8b6b6b;
  font-size: 1rem;
  height: 200px;
  display: flex;
  align-items: center;
}

.refresh-btn {
  margin-top: 6vh;
  padding: 0.8rem 2.5rem;
  background: transparent;
  border: 1px solid rgba(45, 61, 45, 0.3);
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  font-size: 0.9rem;
  color: #4a5a4a;
  letter-spacing: 0.3em;
  transition: all 0.4s ease;
  position: relative;
  overflow: hidden;
  opacity: 0;
  animation: fadeIn 1s ease-out 1s forwards;
}

.refresh-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(45, 61, 45, 0.05);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s ease;
}

.refresh-btn:hover::before {
  transform: scaleX(1);
}

.refresh-btn:hover {
  border-color: rgba(45, 61, 45, 0.5);
  color: #2d3d2d;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-text {
  position: relative;
  z-index: 1;
}

.btn-icon {
  margin-left: 0.5rem;
  position: relative;
  z-index: 1;
  display: inline-block;
  transition: transform 0.4s ease;
}

.refresh-btn:hover .btn-icon {
  transform: rotate(180deg);
}

.seal {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 3.5rem;
  height: 3.5rem;
  background: rgba(45, 61, 45, 0.08);
  border: 2px solid rgba(45, 61, 45, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Ma Shan Zheng', cursive;
  font-size: 1.8rem;
  color: rgba(45, 61, 45, 0.4);
  writing-mode: vertical-rl;
  letter-spacing: 0.2em;
  opacity: 0;
  animation: fadeIn 1s ease-out 1.5s forwards;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes loadingPulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1); }
}

@media (max-width: 640px) {
  .poetry-card {
    padding: 2rem 1.5rem;
  }

  .quote-mark-left { left: -1rem; }
  .quote-mark-right { right: -1rem; }

  .seal {
    width: 2.5rem;
    height: 2.5rem;
    font-size: 1.4rem;
    bottom: 1rem;
    right: 1rem;
  }
}
</style>