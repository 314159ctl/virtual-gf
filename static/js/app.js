/* ============================================================
   虚拟女友 - 前端交互逻辑
   ============================================================ */

// ---- DOM 引用缓存 ----
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dom = {
  sidebar: $('#sidebar'),
  charList: $('#character-list'),
  chatMessages: $('#chat-messages'),
  messageInput: $('#message-input'),
  welcomeScreen: $('#welcome-screen'),
  headerAvatar: $('#header-avatar'),
  headerName: $('#header-name'),
  headerDesc: $('#header-desc'),
  imageUpload: $('#image-upload'),
  imagePreview: $('#image-preview-container'),
  imagePreviewImg: $('#image-preview-img'),
  audioPlayer: $('#audio-player'),
};

// ---- 状态 ----
let state = {
  socket: null,
  characters: [],
  currentChar: null,
  selectedImage: null,
  isGenerating: false,
  enableVoice: true,
  paintingHistory: [],
  isStreaming: false,
};

// ============================================================
// 初始化
// ============================================================
function init() {
  connectSocket();
  loadCharacters();
  bindEvents();
  loadSettings();
}

function connectSocket() {
  state.socket = io({ transports: ['websocket', 'polling'] });

  state.socket.on('connect', () => console.log('[Socket] 已连接'));

  state.socket.on('chat_chunk', (data) => {
    if (data.done) {
      onStreamComplete(data);
    } else {
      onStreamChunk(data.chunk);
    }
  });

  state.socket.on('chat_error', (data) => {
    removeTypingIndicator();
    state.isStreaming = false;
    showToast(data.error || '发送失败', 'error');
  });

  state.socket.on('image_result', (data) => {
    onImageResult(data);
  });

  state.socket.on('speech_result', (data) => {
    if (data.audio) playAudio(data.audio);
  });

  state.socket.on('disconnect', () => console.log('[Socket] 已断开'));
}

// ============================================================
// 事件绑定
// ============================================================
function bindEvents() {
  // 发送消息
  dom.messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  $('#btn-send').addEventListener('click', sendMessage);

  // 自动调整输入框高度
  dom.messageInput.addEventListener('input', () => {
    dom.messageInput.style.height = 'auto';
    dom.messageInput.style.height = Math.min(dom.messageInput.scrollHeight, 120) + 'px';
  });

  // 图片上传
  $('#btn-upload-image').addEventListener('click', () => dom.imageUpload.click());
  dom.imageUpload.addEventListener('change', handleImageSelect);
  $('#btn-remove-image').addEventListener('click', clearImage);

  // 侧边栏切换
  $('#btn-toggle-sidebar').addEventListener('click', () => dom.sidebar.classList.toggle('open'));

  // 语音开关
  $('#btn-voice-toggle').addEventListener('click', toggleVoice);

  // 清空聊天
  $('#btn-clear-chat').addEventListener('click', clearChat);

  // 设置
  $('#btn-open-settings').addEventListener('click', () => openModal('modal-settings'));
  $('#btn-save-settings').addEventListener('click', saveSettings);

  // 角色编辑
  $('#btn-new-character').addEventListener('click', () => openCharacterModal(null));
  $('#btn-save-character').addEventListener('click', saveCharacter);
  $('#btn-delete-character').addEventListener('click', deleteCharacter);

  // AI 绘画
  $('#btn-open-gallery').addEventListener('click', () => openModal('modal-painting'));
  $('#btn-generate-painting').addEventListener('click', generatePainting);

  // 记忆管理
  $('#btn-open-memories').addEventListener('click', openMemories);
  $('#btn-add-memory').addEventListener('click', addMemory);

  // 弹窗关闭
  document.querySelectorAll('.modal-backdrop, .btn-close, [data-close]').forEach(el => {
    el.addEventListener('click', (e) => {
      const id = el.dataset.close || el.closest('.modal').id;
      closeModal(id);
    });
  });

  // 点击弹窗外关闭
  document.querySelectorAll('.modal-backdrop').forEach(bd => {
    bd.addEventListener('click', () => closeModal(bd.parentElement.id));
  });

  // 下载绘画图片
  $('#btn-download-painting').addEventListener('click', downloadPainting);

  // 全局键盘快捷键
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAllModals();
  });
}

// ============================================================
// 角色管理
// ============================================================
async function loadCharacters() {
  try {
    const res = await fetch('/api/characters');
    if (!res.ok) throw new Error('加载角色失败');
    state.characters = await res.json();
    renderCharacterList();
    if (state.characters.length > 0 && !state.currentChar) {
      selectCharacter(state.characters[0]);
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderCharacterList() {
  dom.charList.innerHTML = state.characters.map(c => `
    <li data-name="${escHtml(c.name)}" class="${state.currentChar && state.currentChar.name === c.name ? 'active' : ''}">
      <div class="char-avatar">${c.name[0] || '?'}</div>
      <div class="char-info">
        <div class="char-name">${escHtml(c.name)}</div>
        <div class="char-meta">${escHtml(c.description || '')}</div>
      </div>
      <button class="char-edit-btn" data-action="edit" data-name="${escHtml(c.name)}" title="编辑">✎</button>
    </li>
  `).join('');

  // 点击选择角色
  dom.charList.querySelectorAll('li').forEach(li => {
    li.addEventListener('click', (e) => {
      const editBtn = e.target.closest('[data-action="edit"]');
      if (editBtn) {
        e.stopPropagation();
        const name = editBtn.dataset.name;
        const char = state.characters.find(c => c.name === name);
        if (char) openCharacterModal(char);
        return;
      }
      const name = li.dataset.name;
      const char = state.characters.find(c => c.name === name);
      if (char) selectCharacter(char);
    });
  });
}

function selectCharacter(char) {
  state.currentChar = char;
  state.isStreaming = false;
  removeTypingIndicator();

  // 更新 header
  dom.headerName.textContent = char.name;
  dom.headerDesc.textContent = char.description || '';
  dom.headerAvatar.textContent = char.name[0] || '?';

  // 更新欢迎屏
  $('#welcome-name').textContent = char.name;
  $('#welcome-desc').textContent = char.description || '';
  $('#welcome-avatar').textContent = char.name[0] || '?';

  // 重新渲染列表高亮
  renderCharacterList();

  // 加载聊天历史
  loadChatHistory(char.name);

  // 更新绘画弹窗标题
  $('#modal-painting .modal-header h3').textContent = `🖼️ AI 绘画 - ${char.name}`;
}

async function loadChatHistory(characterName) {
  try {
    const res = await fetch(`/api/conversation/${encodeURIComponent(characterName)}`);
    if (!res.ok) return;
    const history = await res.json();

    dom.chatMessages.innerHTML = '';
    if (history.length === 0) {
      dom.welcomeScreen.style.display = 'block';
      return;
    }
    dom.welcomeScreen.style.display = 'none';

    history.forEach(msg => {
      if (msg.role === 'user') {
        if (msg.msg_type === 'image') {
          appendMessage('user', '[图片]', null, msg.image_data);
        } else {
          appendMessage('user', msg.content);
        }
      } else if (msg.role === 'assistant') {
        appendMessage('ai', msg.content, false);
      }
    });
    scrollToBottom();
  } catch (err) {
    console.error('加载历史失败:', err);
  }
}

function openCharacterModal(char = null) {
  if (char) {
    $('#modal-char-title').textContent = '编辑角色';
    $('#char-name').value = char.name;
    $('#char-desc').value = char.description || '';
    $('#char-prompt').value = char.prompt || '';
    $('#btn-delete-character').style.display = 'inline-flex';
    $('#btn-delete-character').dataset.name = char.name;
  } else {
    $('#modal-char-title').textContent = '创建角色';
    $('#char-name').value = '';
    $('#char-desc').value = '';
    $('#char-prompt').value = '';
    $('#btn-delete-character').style.display = 'none';
  }
  openModal('modal-character');
}

async function saveCharacter() {
  const name = $('#char-name').value.trim();
  const description = $('#char-desc').value.trim();
  const prompt = $('#char-prompt').value.trim();

  if (!name || !prompt) {
    showToast('请填写角色名和设定', 'error');
    return;
  }

  try {
    const res = await fetch('/api/characters', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description, prompt })
    });
    if (!res.ok) throw new Error('保存失败');
    closeModal('modal-character');
    await loadCharacters();
    showToast('角色已保存', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteCharacter() {
  const name = $('#btn-delete-character').dataset.name;
  if (!name) return;
  if (!confirm(`确定要删除角色「${name}」吗？此操作不可恢复。`)) return;

  try {
    const res = await fetch(`/api/characters/${encodeURIComponent(name)}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('删除失败');
    closeModal('modal-character');
    state.currentChar = null;
    dom.chatMessages.innerHTML = '';
    dom.welcomeScreen.style.display = 'block';
    await loadCharacters();
    showToast('角色已删除', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ============================================================
// 聊天功能
// ============================================================
function sendMessage() {
  if (state.isStreaming) return;

  const text = dom.messageInput.value.trim();
  const hasImage = state.selectedImage !== null;

  if (!text && !hasImage) return;
  if (!state.currentChar) {
    showToast('请先选择一个角色', 'error');
    return;
  }

  dom.welcomeScreen.style.display = 'none';

  // 显示用户消息
  if (hasImage) {
    appendMessage('user', text || '[图片]', null, state.selectedImage);
  } else {
    appendMessage('user', text);
  }

  // 显示打字指示器
  showTypingIndicator();
  state.isStreaming = true;

  // 禁用发送按钮
  $('#btn-send').disabled = true;

  // 发送到服务器
  const payload = {
    character: state.currentChar.name,
    message: text,
    image: state.selectedImage,
  };

  state.socket.emit('chat_message', payload);

  // 清空输入
  dom.messageInput.value = '';
  dom.messageInput.style.height = 'auto';
  clearImage();
}

function onStreamChunk(chunk) {
  removeTypingIndicator();

  // 查找或创建 AI 消息气泡
  let bubble = dom.chatMessages.querySelector('.message.ai.streaming .message-bubble');
  if (!bubble) {
    appendMessage('ai', '', true);
    bubble = dom.chatMessages.querySelector('.message.ai.streaming .message-bubble');
  }
  if (bubble) {
    bubble.textContent += chunk;
  }
  scrollToBottom();
}

function onStreamComplete(data) {
  state.isStreaming = false;
  $('#btn-send').disabled = false;

  // 移除 streaming 标记
  const msg = dom.chatMessages.querySelector('.message.ai.streaming');
  if (msg) {
    msg.classList.remove('streaming');
    if (data.full_reply) {
      msg.querySelector('.message-bubble').textContent = data.full_reply;
    }
    // 添加时间和语音按钮
    addMessageMeta(msg, data.audio);
  }

  // 播放语音
  if (data.audio && state.enableVoice) {
    playAudio(data.audio);
  }

  scrollToBottom();
}

function appendMessage(role, content, isStreaming = false, imageData = null) {
  const div = document.createElement('div');
  div.className = `message ${role}${isStreaming ? ' streaming' : ''}`;

  const avatarEmoji = role === 'user' ? '🙂' : (state.currentChar ? state.currentChar.name[0] : '?');

  let inner = '';
  if (imageData) {
    inner += `<img class="message-image" src="data:image/jpeg;base64,${imageData}" onclick="viewImage(this.src)" alt="图片">`;
  }
  inner += `<div class="message-bubble">${escHtml(content)}</div>`;

  div.innerHTML = `
    <div class="message-avatar">${avatarEmoji}</div>
    <div class="message-content">
      ${inner}
    </div>
  `;

  dom.chatMessages.appendChild(div);
  scrollToBottom();
  return div;
}

function addMessageMeta(msgElement, audioData) {
  const contentDiv = msgElement.querySelector('.message-content');
  if (!contentDiv) return;

  const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  const timeDiv = document.createElement('div');
  timeDiv.className = 'message-time';
  timeDiv.textContent = time;
  contentDiv.appendChild(timeDiv);

  if (audioData) {
    const btn = document.createElement('button');
    btn.className = 'message-audio-btn';
    btn.textContent = '🔊 朗读';
    btn.addEventListener('click', () => {
      const isPlaying = btn.classList.contains('playing');
      if (isPlaying) {
        dom.audioPlayer.pause();
        btn.classList.remove('playing');
        btn.textContent = '🔊 朗读';
      } else {
        playAudio(audioData, () => {
          btn.classList.remove('playing');
          btn.textContent = '🔊 朗读';
        });
        btn.classList.add('playing');
        btn.textContent = '⏸ 停止';
      }
    });
    contentDiv.appendChild(btn);
  }
}

function showTypingIndicator() {
  removeTypingIndicator();
  const div = document.createElement('div');
  div.className = 'typing-indicator';
  div.id = 'typing-indicator';
  div.innerHTML = '<span></span><span></span><span></span>';
  dom.chatMessages.appendChild(div);
  scrollToBottom();
}

function removeTypingIndicator() {
  const el = $('#typing-indicator');
  if (el) el.remove();
}

function scrollToBottom() {
  requestAnimationFrame(() => {
    dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
  });
}

function clearChat() {
  if (!state.currentChar) return;
  if (!confirm(`确定要清空与「${state.currentChar.name}」的所有聊天记录吗？`)) return;
  dom.chatMessages.innerHTML = '';
  dom.welcomeScreen.style.display = 'block';
  showToast('聊天记录已清空', 'info');
}

// ============================================================
// 图片处理
// ============================================================
function handleImageSelect(e) {
  const file = e.target.files[0];
  if (!file) return;

  if (!file.type.startsWith('image/')) {
    showToast('请选择图片文件', 'error');
    return;
  }

  const reader = new FileReader();
  reader.onload = (ev) => {
    state.selectedImage = ev.target.result.split(',')[1];
    dom.imagePreviewImg.src = ev.target.result;
    dom.imagePreview.style.display = 'block';
    dom.messageInput.placeholder = '描述这张图片（可选）...';
  };
  reader.readAsDataURL(file);
}

function clearImage() {
  state.selectedImage = null;
  dom.imageUpload.value = '';
  dom.imagePreview.style.display = 'none';
  dom.imagePreviewImg.src = '';
  dom.messageInput.placeholder = '输入消息...';
}

function viewImage(src) {
  const win = window.open('', '_blank');
  win.document.write(`<img src="${src}" style="max-width:100%;max-height:100vh;display:block;margin:auto;">`);
}

// ============================================================
// 语音
// ============================================================
function playAudio(base64Data, onEnd = null) {
  if (!base64Data) return;
  const audio = dom.audioPlayer;
  audio.src = `data:audio/mp3;base64,${base64Data}`;
  audio.play().catch(() => {});
  if (onEnd) {
    audio.onended = onEnd;
  }
}

function toggleVoice() {
  state.enableVoice = !state.enableVoice;
  const btn = $('#btn-voice-toggle');
  btn.textContent = state.enableVoice ? '🔊' : '🔇';
  btn.title = state.enableVoice ? '语音播报：开' : '语音播报：关';
  showToast(`语音播报已${state.enableVoice ? '开启' : '关闭'}`, 'info');
}

// ============================================================
// 设置
// ============================================================
async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    if (!res.ok) return;
    const s = await res.json();
    if (s.api_key) $('#setting-api-key').value = s.api_key;
    if (s.base_url) $('#setting-base-url').value = s.base_url;
    if (s.model) $('#setting-model').value = s.model;
    if (s.max_token) $('#setting-max-token').value = s.max_token;
    if (s.temperature) $('#setting-temperature').value = s.temperature;
    if (s.tts_voice) $('#setting-tts-voice').value = s.tts_voice;
    if (s.painting_api_key) $('#setting-painting-api-key').value = s.painting_api_key;
    if (s.painting_base_url) $('#setting-painting-base-url').value = s.painting_base_url;
    if (s.painting_model) $('#setting-painting-model').value = s.painting_model;
  } catch (err) {
    console.error('加载设置失败:', err);
  }
}

async function saveSettings() {
  const settings = {
    api_key: $('#setting-api-key').value.trim(),
    base_url: $('#setting-base-url').value.trim(),
    model: $('#setting-model').value.trim(),
    max_token: parseInt($('#setting-max-token').value) || 2000,
    temperature: parseFloat($('#setting-temperature').value) || 0.9,
    tts_voice: $('#setting-tts-voice').value,
    painting_api_key: $('#setting-painting-api-key').value.trim(),
    painting_base_url: $('#setting-painting-base-url').value.trim(),
    painting_model: $('#setting-painting-model').value.trim(),
  };

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    if (!res.ok) throw new Error('保存失败');
    closeModal('modal-settings');
    showToast('设置已保存', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ============================================================
// AI 绘画
// ============================================================
function generatePainting() {
  const prompt = $('#painting-prompt').value.trim();
  if (!prompt) {
    showToast('请输入图片描述', 'error');
    return;
  }
  if (!state.currentChar) {
    showToast('请先选择一个角色', 'error');
    return;
  }

  $('#painting-loading').style.display = 'block';
  $('#painting-result').style.display = 'none';
  $('#painting-error').style.display = 'none';
  $('#btn-generate-painting').disabled = true;

  state.socket.emit('generate_image', { prompt });
}

function onImageResult(data) {
  $('#painting-loading').style.display = 'none';
  $('#btn-generate-painting').disabled = false;

  if (data.error) {
    $('#painting-error').textContent = data.error;
    $('#painting-error').style.display = 'block';
    return;
  }

  if (data.url) {
    $('#painting-img').src = data.url;
    $('#painting-result').style.display = 'block';

    // 添加到历史
    state.paintingHistory.unshift({ url: data.url, prompt: data.prompt });
    if (state.paintingHistory.length > 12) state.paintingHistory.pop();
    renderPaintingHistory();
  }
}

function renderPaintingHistory() {
  const container = $('#painting-history');
  container.innerHTML = state.paintingHistory.map(p =>
    `<img src="${p.url}" alt="${escHtml(p.prompt)}" title="${escHtml(p.prompt)}" onclick="$('#painting-img').src='${p.url}';$('#painting-result').style.display='block';">`
  ).join('');
}

function downloadPainting() {
  const src = $('#painting-img').src;
  if (!src) return;
  const a = document.createElement('a');
  a.href = src;
  a.download = `painting_${Date.now()}.png`;
  a.click();
}

// ============================================================
// 记忆管理
// ============================================================
async function openMemories() {
  if (!state.currentChar) {
    showToast('请先选择一个角色', 'error');
    return;
  }
  openModal('modal-memories');
  loadMemories();
}

async function loadMemories() {
  // 从后端获取记忆（使用长期记忆 API）
  const container = $('#memories-list');
  try {
    const res = await fetch(`/api/conversation/${encodeURIComponent(state.currentChar.name)}`);
    if (!res.ok) return;

    // 暂时用本地存储模拟长期记忆展示
    const key = `memories_${state.currentChar.name}`;
    const stored = localStorage.getItem(key);
    const memories = stored ? JSON.parse(stored) : [];
    renderMemories(memories);
  } catch (err) {
    container.innerHTML = '<p style="color:#888;text-align:center;padding:16px;">暂无记忆数据</p>';
  }
}

function renderMemories(memories) {
  const container = $('#memories-list');
  if (memories.length === 0) {
    container.innerHTML = '<p style="color:#888;text-align:center;padding:16px;">还没有记录任何记忆，来添加一条吧~</p>';
    return;
  }
  container.innerHTML = memories.map((m, i) => `
    <div class="memory-item">
      <span class="importance-stars">${'★'.repeat(m.importance || 3)}</span>
      <span class="memory-text">${escHtml(m.content)}</span>
      <span class="memory-delete" data-index="${i}">✕</span>
    </div>
  `).join('');

  container.querySelectorAll('.memory-delete').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.index);
      memories.splice(idx, 1);
      localStorage.setItem(`memories_${state.currentChar.name}`, JSON.stringify(memories));
      renderMemories(memories);
    });
  });
}

function addMemory() {
  if (!state.currentChar) return;
  const input = $('#memory-input');
  const content = input.value.trim();
  if (!content) return;

  const key = `memories_${state.currentChar.name}`;
  const stored = localStorage.getItem(key);
  const memories = stored ? JSON.parse(stored) : [];
  memories.unshift({ content, importance: 3, created_at: new Date().toISOString() });
  localStorage.setItem(key, JSON.stringify(memories));

  input.value = '';
  renderMemories(memories);
  showToast('记忆已添加', 'success');
}

// ============================================================
// 弹窗管理
// ============================================================
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add('active');
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove('active');
}

function closeAllModals() {
  document.querySelectorAll('.modal.active').forEach(m => m.classList.remove('active'));
}

// ============================================================
// Toast 通知
// ============================================================
function showToast(message, type = 'info') {
  let container = $('#toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icons = { success: '✅', error: '❌', info: '💡' };
  toast.innerHTML = `<span>${icons[type] || ''}</span> ${escHtml(message)}`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ============================================================
// 工具函数
// ============================================================
function escHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ============================================================
// 启动
// ============================================================
document.addEventListener('DOMContentLoaded', init);
