/**
 * Antigravity CLI - Mobile Web Dashboard Frontend Logic
 * Full Web Speech API (Push-to-Talk), Camera/Gallery Uploads, Clipboard Paste,
 * Markdown Rendering with Syntax Highlighting & Callouts, and Image Lightbox.
 */

(() => {
  // DOM Elements
  const chatContainer = document.getElementById('chat-container');
  const messagesList = document.getElementById('messages-list');
  const welcomeCard = document.getElementById('welcome-card');
  const typingIndicator = document.getElementById('typing-indicator');
  const chatBottomAnchor = document.getElementById('chat-bottom-anchor');
  const scrollBottomBtn = document.getElementById('scroll-bottom-btn');
  
  const chatInput = document.getElementById('chat-input');
  const btnSend = document.getElementById('btn-send');
  const btnMic = document.getElementById('btn-mic');
  const btnCamera = document.getElementById('btn-camera');
  const btnGallery = document.getElementById('btn-gallery');
  const cameraInput = document.getElementById('camera-input');
  const galleryInput = document.getElementById('gallery-input');
  const attachmentStrip = document.getElementById('attachment-strip');
  
  // Status Bar Elements
  const connectionStatus = document.getElementById('connection-status');
  const statusLabel = document.getElementById('status-label');
  const pingBadge = document.getElementById('ping-badge');
  const currentPathLabel = document.getElementById('current-path-label');
  const modelBadge = document.getElementById('model-badge');
  const btnOpenPathModal = document.getElementById('btn-open-path-modal');
  const btnClearChat = document.getElementById('btn-clear-chat');
  const btnTheme = document.getElementById('btn-theme');
  const btnInfo = document.getElementById('btn-info');
  
  // Voice Overlay Elements
  const voiceOverlay = document.getElementById('voice-overlay');
  const voiceInterimText = document.getElementById('voice-interim-text');
  const voiceStatusTitle = document.getElementById('voice-status-title');
  const voiceLangSelect = document.getElementById('voice-lang-select');
  const voiceCancelBtn = document.getElementById('voice-cancel-btn');
  const voiceDoneBtn = document.getElementById('voice-done-btn');
  
  // Modals & Lightbox
  const lightboxModal = document.getElementById('lightbox-modal');
  const lightboxImg = document.getElementById('lightbox-img');
  const lightboxFilename = document.getElementById('lightbox-filename');
  const lightboxDownload = document.getElementById('lightbox-download');
  const lightboxClose = document.getElementById('lightbox-close');
  const lightboxBackdrop = document.getElementById('lightbox-backdrop');
  
  const pathModal = document.getElementById('path-modal');
  const pathModalClose = document.getElementById('path-modal-close');
  const manualPathInput = document.getElementById('manual-path-input');
  const btnApplyPath = document.getElementById('btn-apply-path');
  const fileBrowserList = document.getElementById('file-browser-list');
  const pathBreadcrumb = document.getElementById('path-breadcrumb');
  
  const infoModal = document.getElementById('info-modal');
  const infoModalClose = document.getElementById('info-modal-close');
  const infoModalContent = document.getElementById('info-modal-content');

  const fileModal = document.getElementById('file-modal');
  const fileModalClose = document.getElementById('file-modal-close');
  const fileModalTitle = document.getElementById('file-modal-title');
  const fileModalPath = document.getElementById('file-modal-path');
  const fileModalIcon = document.getElementById('file-modal-icon');
  const fileSizeBadge = document.getElementById('file-size-badge');
  const fileEditorTextarea = document.getElementById('file-editor-textarea');
  const btnFileSave = document.getElementById('btn-file-save');
  const btnFileRunPython = document.getElementById('btn-file-run-python');
  const btnFileAskAi = document.getElementById('btn-file-ask-ai');
  const astContent = document.getElementById('ast-content');
  const flowContent = document.getElementById('flow-content');
  const tabBtnCode = document.getElementById('tab-btn-code');
  const tabBtnAst = document.getElementById('tab-btn-ast');
  const tabBtnFlow = document.getElementById('tab-btn-flow');
  const panelCode = document.getElementById('panel-code');
  const panelAst = document.getElementById('panel-ast');
  const panelFlow = document.getElementById('panel-flow');

  // Application State
  const state = {
    attachedImages: [], // Array of { url, filename, size }
    currentCwd: '~',
    isRecording: false,
    isOverlayOpen: false,
    recognition: null,
    committedSpeech: '',
    currentSessionFinal: '',
    currentSessionInterim: '',
    isSending: false,
    ttsKeepAliveTimer: null,
    activeTTSBtn: null
  };

  // =========================================================================
  // INITIALIZATION
  // =========================================================================
  function init() {
    setupEventListeners();
    setupSpeechRecognition();
    setupClipboardPaste();
    loadHistory();
    fetchStatus();
    setInterval(fetchStatus, 8000);
  }

  // =========================================================================
  // STATUS & CONNECTION HEARTBEAT
  // =========================================================================
  async function fetchStatus() {
    const startTime = performance.now();
    try {
      const res = await fetch('/api/status');
      const ping = Math.round(performance.now() - startTime);
      
      if (!res.ok) throw new Error('Status error');
      const data = await res.json();
      
      // Update UI
      connectionStatus.className = 'connection-indicator online';
      statusLabel.textContent = 'Online';
      pingBadge.textContent = `${ping}ms`;
      
      state.currentCwd = data.cwd || '~';
      currentPathLabel.textContent = formatPathBasename(state.currentCwd);
      currentPathLabel.parentElement.title = state.currentCwd;
      
      if (data.model) {
        modelBadge.textContent = data.model;
      }
    } catch (err) {
      connectionStatus.className = 'connection-indicator offline';
      statusLabel.textContent = 'Getrennt';
      pingBadge.textContent = '--';
    }
  }

  function formatPathBasename(path) {
    if (!path) return '~';
    const parts = path.split('/').filter(Boolean);
    if (parts.length === 0) return '/';
    return parts[parts.length - 1];
  }

  // =========================================================================
  // LOAD & RENDER CHAT HISTORY
  // =========================================================================
  async function loadHistory() {
    try {
      const res = await fetch('/api/history');
      if (!res.ok) return;
      const data = await res.json();
      if (data.messages && data.messages.length > 0) {
        welcomeCard.classList.add('hidden');
        messagesList.innerHTML = '';
        data.messages.forEach(msg => appendMessageToDOM(msg, false));
        scrollToBottom(false);
      } else {
        welcomeCard.classList.remove('hidden');
      }
    } catch (err) {
      console.error('Error loading history:', err);
    }
  }

  // =========================================================================
  // SEND MESSAGE
  // =========================================================================
  async function sendMessage() {
    const text = chatInput.value.trim();
    const images = [...state.attachedImages];

    if (!text && images.length === 0) return;
    if (state.isSending) return;

    // Haptic feedback
    if (navigator.vibrate) navigator.vibrate(25);

    // Clear input & attachments
    chatInput.value = '';
    adjustTextareaHeight();
    state.attachedImages = [];
    renderAttachmentStrip();
    welcomeCard.classList.add('hidden');

    // Render user message immediately
    const userMsg = {
      id: 'usr_' + Date.now(),
      role: 'user',
      content: text,
      images: images.map(img => img.url),
      created_at: new Date().toISOString()
    };
    appendMessageToDOM(userMsg, true);
    scrollToBottom(true);

    state.isSending = true;
    btnSend.disabled = true;

    // Create live assistant message element
    const assistantMsg = {
      id: 'asst_' + Date.now(),
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString()
    };
    const liveEl = createLiveAssistantElement(assistantMsg);
    messagesList.appendChild(liveEl.item);
    scrollToBottom(true);

    try {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          images: images.map(img => img.url)
        })
      });

      if (!res.ok) throw new Error(`HTTP error ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamDone = false;

      while (!streamDone) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep partial line

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            try {
              const evt = JSON.parse(trimmed.slice(6));
              updateLiveAssistantElement(liveEl, evt);
              if (evt.type === 'done' || evt.type === 'error') {
                streamDone = true;
                break;
              }
            } catch (err) {
              console.warn('SSE parse error:', err);
            }
          }
        }
      }

      try {
        await reader.cancel();
      } catch (_) {}

      finalizeLiveAssistantElement(liveEl);
      fetchStatus();
    } catch (err) {
      if (liveEl.statusBadge && liveEl.statusBadge.parentNode) {
        liveEl.statusBadge.remove();
      }
      liveEl.bubble.innerHTML = renderMarkdown(`> [!CAUTION]\n> **Fehler bei der Kommunikation:** ${err.message}`);
      scrollToBottom(true);
    } finally {
      state.isSending = false;
      btnSend.disabled = false;
      chatInput.focus();
    }
  }

  function createLiveAssistantElement(msg) {
    const item = document.createElement('div');
    item.className = 'message-item assistant';
    item.id = msg.id;

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = '⚡';

    const wrapper = document.createElement('div');
    wrapper.className = 'msg-content-wrapper';

    const statusBadge = document.createElement('div');
    statusBadge.className = 'live-status-badge';
    statusBadge.innerHTML = `<span class="live-pulse-dot"></span> <span class="badge-text">Antigravity initialisiert...</span>`;
    wrapper.appendChild(statusBadge);

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.innerHTML = `<span class="streaming-cursor">▍</span>`;
    wrapper.appendChild(bubble);

    const meta = document.createElement('div');
    meta.className = 'msg-meta';
    meta.innerHTML = `<span>Antigravity</span> • <span>${formatTime(msg.created_at)}</span>`;
    wrapper.appendChild(meta);

    item.appendChild(avatar);
    item.appendChild(wrapper);

    return { item, wrapper, bubble, statusBadge, meta, accumulatedText: '' };
  }

  function updateLiveAssistantElement(liveEl, evt) {
    const type = evt.type;
    const data = evt.data || {};

    if (type === 'status') {
      liveEl.statusBadge.innerHTML = `<span class="live-pulse-dot"></span> <span class="badge-text">${escapeHTML(data.text || '')}</span>`;
      scrollToBottom(false);
    } else if (type === 'tool_start') {
      const toolName = escapeHTML(data.tool || 'Tool');
      const detail = escapeHTML(data.detail || '');
      liveEl.statusBadge.innerHTML = `<span class="live-pulse-dot"></span> <strong>⚡ ${toolName}</strong> <span class="tool-detail">${detail}</span>`;
      scrollToBottom(false);
    } else if (type === 'tool_done') {
      const toolName = escapeHTML(data.tool || 'Tool');
      liveEl.statusBadge.innerHTML = `<span class="live-pulse-dot"></span> <span>✅ ${toolName} abgeschlossen</span>`;
      scrollToBottom(false);
    } else if (type === 'delta') {
      liveEl.accumulatedText = data.accumulated !== undefined ? data.accumulated : (liveEl.accumulatedText + (data.text || ''));
      liveEl.bubble.innerHTML = renderMarkdown(liveEl.accumulatedText) + '<span class="streaming-cursor">▍</span>';
      attachCodeBlockHandlers(liveEl.bubble);
      scrollToBottom(false);
    } else if (type === 'done') {
      liveEl.accumulatedText = data.content || liveEl.accumulatedText;
      liveEl.bubble.innerHTML = renderMarkdown(liveEl.accumulatedText);
      attachCodeBlockHandlers(liveEl.bubble);
      if (liveEl.statusBadge && liveEl.statusBadge.parentNode) {
        liveEl.statusBadge.remove();
      }
      scrollToBottom(true);
    } else if (type === 'error') {
      liveEl.bubble.innerHTML = renderMarkdown(data.error || 'Fehler aufgetreten');
      if (liveEl.statusBadge && liveEl.statusBadge.parentNode) {
        liveEl.statusBadge.remove();
      }
      scrollToBottom(true);
    }
  }

  function finalizeLiveAssistantElement(liveEl) {
    if (liveEl.statusBadge && liveEl.statusBadge.parentNode) {
      liveEl.statusBadge.remove();
    }
    const cursor = liveEl.bubble.querySelector('.streaming-cursor');
    if (cursor) cursor.remove();

    if (!liveEl.wrapper.querySelector('.msg-actions') && liveEl.accumulatedText) {
      const actions = document.createElement('div');
      actions.className = 'msg-actions';

      const btnCopy = document.createElement('button');
      btnCopy.className = 'action-pill-btn';
      btnCopy.textContent = '📋 Kopieren';
      btnCopy.addEventListener('click', () => copyToClipboard(liveEl.accumulatedText, btnCopy));

      const btnTTS = document.createElement('button');
      btnTTS.className = 'action-pill-btn';
      btnTTS.textContent = '🔊 Vorlesen';
      btnTTS.addEventListener('click', () => speakText(liveEl.accumulatedText, btnTTS));

      actions.appendChild(btnCopy);
      actions.appendChild(btnTTS);
      liveEl.wrapper.insertBefore(actions, liveEl.meta);
    }
  }

  // =========================================================================
  // DOM RENDERING: MESSAGES & MARKDOWN
  // =========================================================================
  function appendMessageToDOM(msg, animate = true) {
    const isUser = msg.role === 'user';
    const item = document.createElement('div');
    item.className = `message-item ${isUser ? 'user' : 'assistant'}`;
    item.id = `msg-${msg.id}`;

    // Avatar
    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = isUser ? '👤' : '⚡';

    // Content Wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'msg-content-wrapper';

    // Images Attached
    if (msg.images && msg.images.length > 0) {
      const imgGrid = document.createElement('div');
      imgGrid.className = 'msg-images-grid';
      msg.images.forEach(imgUrl => {
        const thumb = document.createElement('img');
        thumb.className = 'msg-img-thumb';
        thumb.src = imgUrl;
        thumb.alt = 'Angehängtes Bild';
        thumb.loading = 'lazy';
        thumb.addEventListener('click', () => openLightbox(imgUrl, 'Bildvorschau'));
        imgGrid.appendChild(thumb);
      });
      wrapper.appendChild(imgGrid);
    }

    // Bubble with Markdown content
    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.innerHTML = renderMarkdown(msg.content);
    wrapper.appendChild(bubble);

    // Meta & Actions
    const meta = document.createElement('div');
    meta.className = 'msg-meta';
    const timeStr = msg.created_at ? formatTime(msg.created_at) : '';
    meta.innerHTML = `<span>${isUser ? 'Du' : 'Antigravity'}</span> • <span>${timeStr}</span>`;

    // Assistant action pills (Copy & Readout TTS)
    if (!isUser) {
      const actions = document.createElement('div');
      actions.className = 'msg-actions';

      const btnCopy = document.createElement('button');
      btnCopy.className = 'action-pill-btn';
      btnCopy.textContent = '📋 Kopieren';
      btnCopy.addEventListener('click', () => copyToClipboard(msg.content, btnCopy));

      const btnTTS = document.createElement('button');
      btnTTS.className = 'action-pill-btn';
      btnTTS.textContent = '🔊 Vorlesen';
      btnTTS.addEventListener('click', () => speakText(msg.content, btnTTS));

      actions.appendChild(btnCopy);
      actions.appendChild(btnTTS);
      wrapper.appendChild(actions);
    }

    wrapper.appendChild(meta);
    item.appendChild(avatar);
    item.appendChild(wrapper);

    // Attach copy button handlers for pre code blocks
    attachCodeBlockHandlers(bubble);

    messagesList.appendChild(item);
  }

  function formatTime(isoStr) {
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  }

  // =========================================================================
  // LIGHTWEIGHT ROBUST MARKDOWN PARSER (With Code, Alerts, Tables)
  // =========================================================================
  function renderMarkdown(md) {
    if (!md) return '';
    let html = escapeHTML(md);

    // 1. Code blocks ```lang\ncode\n```
    html = html.replace(/```([a-zA-Z0-9_\-#+]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const langName = lang.trim() || 'code';
      const cleanCode = code.replace(/\n$/, '');
      return `
        <pre><div class="code-header"><span>${langName}</span><button class="copy-code-btn">Kopieren</button></div><code>${cleanCode}</code></pre>
      `;
    });

    // 2. Inline code `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // 3. GitHub Callout Alerts: > [!NOTE], [!TIP], [!IMPORTANT], [!WARNING], [!CAUTION]
    const alertTypes = ['NOTE', 'TIP', 'IMPORTANT', 'WARNING', 'CAUTION'];
    alertTypes.forEach(type => {
      const regex = new RegExp(`&gt; \\[\\!${type}\\]\\s*\\n((?:&gt; .*(?:\\n|$))+)`, 'gi');
      html = html.replace(regex, (m, content) => {
        const cleanContent = content.replace(/^&gt;\s?/gm, '').trim();
        const iconMap = { NOTE: 'ℹ️', TIP: '💡', IMPORTANT: '📌', WARNING: '⚠️', CAUTION: '🚨' };
        return `
          <div class="callout ${type.toLowerCase()}">
            <div class="callout-title">${iconMap[type]} ${type}</div>
            <div>${cleanContent}</div>
          </div>
        `;
      });
    });

    // Standard blockquotes: > text
    html = html.replace(/^&gt;\s?(.*)$/gm, '<blockquote>$1</blockquote>');

    // 4. Headers #, ##, ###, ####
    html = html.replace(/^#### (.*$)/gm, '<h4>$1</h4>');
    html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');

    // 5. Bold & Italic
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/~~([^~]+)~~/g, '<del>$1</del>');

    // 6. Markdown Tables
    html = renderMarkdownTables(html);

    // 7. Unordered & Ordered Lists
    html = html.replace(/^\s*[-*]\s+(.*)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // 8. Links [title](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    // 9. Paragraphs and line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = `<p>${html}</p>`;
    html = html.replace(/<p><\/p>/g, '');

    return html;
  }

  function renderMarkdownTables(text) {
    return text.replace(/((?:\|[^\n]+\|\r?\n)+)/g, (tableMatch) => {
      const rows = tableMatch.trim().split('\n').map(r => r.trim());
      if (rows.length < 2) return tableMatch;

      let tableHtml = '<table>';
      let isHeader = true;

      for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        if (row.includes('---')) {
          isHeader = false;
          continue;
        }
        const cells = row.split('|').filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
        tableHtml += '<tr>';
        cells.forEach(cell => {
          const tag = isHeader ? 'th' : 'td';
          tableHtml += `<${tag}>${cell.trim()}</${tag}>`;
        });
        tableHtml += '</tr>';
      }
      tableHtml += '</table>';
      return tableHtml;
    });
  }

  function escapeHTML(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
  const escapeHtml = escapeHTML;

  function attachCodeBlockHandlers(container) {
    container.querySelectorAll('.copy-code-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const pre = e.target.closest('pre');
        const code = pre.querySelector('code').textContent;
        navigator.clipboard.writeText(code).then(() => {
          btn.textContent = 'Kopiert! ✓';
          setTimeout(() => { btn.textContent = 'Kopieren'; }, 2000);
        });
      });
    });
  }

  function copyToClipboard(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
      if (btn) {
        const orig = btn.textContent;
        btn.textContent = 'Kopiert! ✓';
        setTimeout(() => { btn.textContent = orig; }, 2000);
      }
    });
  }

  // Text to Speech (TTS)
  function speakText(text, btn) {
    if (!('speechSynthesis' in window)) {
      alert('Sprachausgabe (Text-to-Speech) wird in diesem Browser nicht unterstützt.');
      return;
    }

    // Toggle off if already speaking the same message
    if (window.speechSynthesis.speaking && state.activeTTSBtn === btn) {
      window.speechSynthesis.cancel();
      if (state.ttsKeepAliveTimer) clearInterval(state.ttsKeepAliveTimer);
      if (btn) btn.textContent = '🔊 Vorlesen';
      state.activeTTSBtn = null;
      return;
    }

    // Cancel any previous readout
    window.speechSynthesis.cancel();
    if (state.ttsKeepAliveTimer) clearInterval(state.ttsKeepAliveTimer);
    if (state.activeTTSBtn) {
      state.activeTTSBtn.textContent = '🔊 Vorlesen';
    }

    // Clean up text: remove code blocks, markdown syntax, links, excessive whitespace
    const clean = text
      .replace(/```[\s\S]*?```/g, ' [Code-Block übersprungen] ')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/[#*_>~\[\]\(\)]/g, ' ')
      .replace(/https?:\/\/\S+/g, ' Link ')
      .replace(/\s+/g, ' ')
      .trim();

    if (!clean) return;

    const utter = new SpeechSynthesisUtterance(clean);
    utter.lang = 'de-DE';
    utter.rate = 1.0;
    utter.pitch = 1.0;

    // Pick best matching German voice if available
    const voices = window.speechSynthesis.getVoices();
    const deVoice = voices.find(v => v.lang && v.lang.startsWith('de') && (v.name.includes('Natural') || v.name.includes('Google') || v.default));
    if (deVoice) utter.voice = deVoice;

    if (btn) {
      btn.textContent = '⏹ Stopp';
      state.activeTTSBtn = btn;
    }

    utter.onend = () => {
      if (btn) btn.textContent = '🔊 Vorlesen';
      if (state.ttsKeepAliveTimer) clearInterval(state.ttsKeepAliveTimer);
      state.activeTTSBtn = null;
    };

    utter.onerror = (e) => {
      console.warn('TTS error:', e);
      if (btn) btn.textContent = '🔊 Vorlesen';
      if (state.ttsKeepAliveTimer) clearInterval(state.ttsKeepAliveTimer);
      state.activeTTSBtn = null;
    };

    // Chrome/Android 15s keepalive fix for long utterances
    state.ttsKeepAliveTimer = setInterval(() => {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.pause();
        window.speechSynthesis.resume();
      } else {
        clearInterval(state.ttsKeepAliveTimer);
      }
    }, 10000);

    window.speechSynthesis.speak(utter);
  }

  // =========================================================================
  // WEB SPEECH API (PUSH-TO-TALK & VOICE DICTATION)
  // =========================================================================
  function isSecureOrLocal() {
    return window.isSecureContext || 
           location.hostname === 'localhost' || 
           location.hostname === '127.0.0.1' || 
           location.hostname === '0.0.0.0';
  }

  function formatSpeechText(rawText) {
    if (!rawText) return '';
    let text = rawText.trim();

    // Normalize multiple spaces
    text = text.replace(/\s+/g, ' ');

    // Deduplicate adjacent repeated multi-word phrases & single words
    // Solves Android Web Speech API duplicate stutter / buffer replay
    for (let phraseLen = 8; phraseLen >= 1; phraseLen--) {
      const pattern = new RegExp(`\\b(${'\\S+\\s+'.repeat(phraseLen - 1)}\\S+)\\s+\\1\\b`, 'gi');
      let prev = '';
      while (prev !== text) {
        prev = text;
        text = text.replace(pattern, '$1');
      }
    }

    // Natural punctuation formatting (German & English spoken punctuation)
    text = text
      .replace(/\s+([.,!?:;])/g, '$1')
      .replace(/\b(neue zeile|absatz|new line)\b/gi, '\n')
      .replace(/\b(punkt|full stop|period)\b/gi, '.')
      .replace(/\b(komma|comma)\b/gi, ',')
      .replace(/\b(fragezeichen|question mark)\b/gi, '?')
      .replace(/\b(ausrufezeichen|exclamation mark)\b/gi, '!');

    // Re-clean spacing before punctuation in case replacements created spaces
    text = text.replace(/\s+([.,!?:;])/g, '$1');

    // Sentence casing: Capitalize start of text and after sentence terminators
    text = text.replace(/(^|[.!?\n]\s+)([a-zäöü])/g, (match, prefix, char) => {
      return prefix + char.toUpperCase();
    });

    return text.trim();
  }

  function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Speech Recognition not supported in this browser.');
      btnMic.title = 'Spracheingabe im aktuellen Browser nicht verfügbar (Google Chrome empfohlen)';
      btnMic.style.opacity = '0.5';
      return;
    }

    if (!isSecureOrLocal()) {
      console.warn('Speech Recognition requires HTTPS or localhost/127.0.0.1 context.');
      btnMic.title = 'Spracheingabe benötigt HTTPS oder Aufruf über http://localhost:8080';
    }

    // Touch & Mouse Event Handling with pointer events
    let touchStartTime = 0;
    let isHolding = false;
    let holdTimer = null;

    btnMic.addEventListener('pointerdown', (e) => {
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      touchStartTime = Date.now();
      isHolding = false;

      // Hold threshold for Push-to-Talk (350ms)
      holdTimer = setTimeout(() => {
        isHolding = true;
        if (!state.isRecording) {
          startVoiceCapture(false); // Quick PTT mode
        }
      }, 350);
    });

    btnMic.addEventListener('pointerup', (e) => {
      clearTimeout(holdTimer);
      const pressDuration = Date.now() - touchStartTime;

      if (isHolding) {
        // Was holding PTT -> commit and stop
        isHolding = false;
        stopVoiceCapture(true);
      } else if (pressDuration < 350) {
        // Quick tap/click -> toggle Overlay modal
        if (state.isRecording || state.isOverlayOpen) {
          stopVoiceCapture(true);
        } else {
          startVoiceCapture(true);
        }
      }
    });

    btnMic.addEventListener('pointercancel', () => {
      clearTimeout(holdTimer);
      if (isHolding) {
        isHolding = false;
        stopVoiceCapture(false);
      }
    });

    // Voice Overlay Controls
    voiceDoneBtn.addEventListener('click', () => stopVoiceCapture(true));
    voiceCancelBtn.addEventListener('click', () => stopVoiceCapture(false));
    voiceLangSelect.addEventListener('change', () => {
      if (state.recognition && state.isRecording) {
        const finishedText = (state.currentSessionFinal + ' ' + (state.currentSessionInterim || '')).trim();
        if (finishedText) {
          state.committedSpeech = (state.committedSpeech ? state.committedSpeech + ' ' : '') + finishedText;
        }
        state.currentSessionFinal = '';
        state.currentSessionInterim = '';
        startVoiceCapture(state.isOverlayOpen);
      }
    });
  }

  function createRecognitionInstance() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return null;

    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.maxAlternatives = 1;
    rec.lang = voiceLangSelect.value || 'de-DE';

    rec.onstart = () => {
      state.isRecording = true;
      btnMic.classList.add('active');
      voiceStatusTitle.textContent = 'Ich höre zu...';
    };

    rec.onresult = (event) => {
      let sessionFinal = '';
      let sessionInterim = '';

      // Reconstruct transcript cleanly from event.results to prevent duplicate appending
      for (let i = 0; i < event.results.length; ++i) {
        const item = event.results[i];
        if (item && item[0]) {
          const transcript = item[0].transcript || '';
          if (item.isFinal) {
            sessionFinal += transcript + ' ';
          } else {
            sessionInterim += transcript;
          }
        }
      }

      state.currentSessionFinal = sessionFinal;
      state.currentSessionInterim = sessionInterim;

      const liveText = formatSpeechText([
        state.committedSpeech,
        sessionFinal,
        sessionInterim
      ].filter(Boolean).join(' '));

      voiceInterimText.textContent = liveText || 'Ich höre zu...';
    };

    rec.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      if (event.error === 'no-speech') {
        if (!state.committedSpeech && !state.currentSessionFinal && !state.currentSessionInterim) {
          voiceStatusTitle.textContent = 'Keine Sprache erkannt';
        }
        return;
      }
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        voiceStatusTitle.textContent = 'Mikrofon blockiert';
        voiceInterimText.textContent = isSecureOrLocal()
          ? 'Bitte erlaube den Mikrofon-Zugriff in den Browser-Einstellungen.'
          : 'Web Speech API benötigt HTTPS oder den Aufruf über http://localhost:8080!';
        return;
      }
      if (event.error === 'network') {
        voiceStatusTitle.textContent = 'Netzwerkfehler';
        voiceInterimText.textContent = 'Google Spracherkennungsdienst nicht erreichbar.';
        return;
      }
      if (event.error === 'aborted') {
        return;
      }
      voiceStatusTitle.textContent = `Fehler: ${event.error}`;
    };

    rec.onend = () => {
      // Commit the completed session text safely
      const finishedText = (state.currentSessionFinal + ' ' + (state.currentSessionInterim || '')).trim();
      if (finishedText) {
        if (state.committedSpeech) {
          if (!state.committedSpeech.endsWith(finishedText)) {
            state.committedSpeech = (state.committedSpeech + ' ' + finishedText).trim();
          }
        } else {
          state.committedSpeech = finishedText;
        }
      }
      state.currentSessionFinal = '';
      state.currentSessionInterim = '';

      // Auto-restart if overlay is still actively open and recording was not explicitly stopped
      if (state.isOverlayOpen && state.isRecording) {
        try {
          rec.start();
          return;
        } catch (e) {
          console.warn('Auto-restart recognition failed:', e);
        }
      }
      state.isRecording = false;
      btnMic.classList.remove('active');
    };

    return rec;
  }

  function startVoiceCapture(showOverlay = true) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Die Web Speech API wird in deinem aktuellen Browser nicht unterstützt. Bitte nutze Google Chrome oder Safari.');
      return;
    }

    if (!isSecureOrLocal()) {
      alert('⚠️ Hinweis: Die Web Speech API (Mikrofon) erfordert aus Sicherheitsgründen HTTPS oder den lokalen Aufruf über http://localhost:8080 bzw. http://127.0.0.1:8080 auf diesem Gerät.');
    }

    // Stop any existing instance cleanly
    if (state.recognition) {
      try { state.recognition.abort(); } catch (e) {}
    }

    if (navigator.vibrate) navigator.vibrate(40);
    state.committedSpeech = '';
    state.currentSessionFinal = '';
    state.currentSessionInterim = '';
    state.isRecording = true;
    state.isOverlayOpen = showOverlay;
    voiceInterimText.textContent = 'Sprich jetzt...';
    voiceStatusTitle.textContent = 'Ich höre zu...';

    if (showOverlay) {
      voiceOverlay.classList.remove('hidden');
    }

    state.recognition = createRecognitionInstance();
    if (!state.recognition) return;

    try {
      state.recognition.start();
    } catch (e) {
      console.warn('Recognition start caught:', e);
      try {
        state.recognition.abort();
        setTimeout(() => state.recognition && state.recognition.start(), 100);
      } catch (err) {}
    }
  }

  function stopVoiceCapture(commit = true) {
    const wasRecording = state.isRecording || state.isOverlayOpen;
    state.isOverlayOpen = false;
    state.isRecording = false;

    if (state.recognition) {
      try {
        state.recognition.stop();
      } catch (e) {}
    }

    btnMic.classList.remove('active');
    voiceOverlay.classList.add('hidden');
    if (navigator.vibrate) navigator.vibrate(25);

    if (commit && wasRecording) {
      const fullText = formatSpeechText([
        state.committedSpeech,
        state.currentSessionFinal,
        state.currentSessionInterim
      ].filter(Boolean).join(' '));

      if (fullText) {
        const prev = chatInput.value.trim();
        chatInput.value = prev ? `${prev} ${fullText}` : fullText;
        adjustTextareaHeight();
        chatInput.focus();
      }
    }
    state.committedSpeech = '';
    state.currentSessionFinal = '';
    state.currentSessionInterim = '';
  }

  // =========================================================================
  // IMAGE & PHOTO UPLOAD (CAMERA & GALLERY WITH COMPRESSION)
  // =========================================================================
  function setupImageUploads() {
    btnCamera.addEventListener('click', () => cameraInput.click());
    btnGallery.addEventListener('click', () => galleryInput.click());

    cameraInput.addEventListener('change', (e) => handleFileInput(e.target.files));
    galleryInput.addEventListener('change', (e) => handleFileInput(e.target.files));
  }

  async function handleFileInput(files) {
    if (!files || files.length === 0) return;
    for (let i = 0; i < files.length; i++) {
      await processAndUploadImage(files[i]);
    }
    cameraInput.value = '';
    galleryInput.value = '';
  }

  async function processAndUploadImage(file) {
    if (!file.type.startsWith('image/')) {
      alert('Bitte nur Bilddateien hochladen.');
      return;
    }

    try {
      // Compress image client-side to ensure fast mobile transfer
      const base64Data = await compressImage(file, 1600, 0.85);

      // Upload to server
      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: file.name || `photo_${Date.now()}.jpg`,
          data: base64Data
        })
      });

      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();

      // Add to attachedImages
      state.attachedImages.push({
        url: data.url,
        filename: data.filename,
        size: data.size
      });

      if (navigator.vibrate) navigator.vibrate(30);
      renderAttachmentStrip();
    } catch (err) {
      console.error('Upload error:', err);
      alert('Fehler beim Hochladen des Bildes: ' + err.message);
    }
  }

  function compressImage(file, maxDimension = 1600, quality = 0.85) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          let width = img.width;
          let height = img.height;

          if (width > maxDimension || height > maxDimension) {
            if (width > height) {
              height = Math.round((height * maxDimension) / width);
              width = maxDimension;
            } else {
              width = Math.round((width * maxDimension) / height);
              height = maxDimension;
            }
          }

          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);

          const compressedBase64 = canvas.toDataURL('image/jpeg', quality);
          resolve(compressedBase64);
        };
        img.onerror = reject;
        img.src = e.target.result;
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  function renderAttachmentStrip() {
    if (state.attachedImages.length === 0) {
      attachmentStrip.classList.add('hidden');
      attachmentStrip.innerHTML = '';
      return;
    }

    attachmentStrip.classList.remove('hidden');
    attachmentStrip.innerHTML = '';

    state.attachedImages.forEach((img, idx) => {
      const card = document.createElement('div');
      card.className = 'attach-thumb-card';

      const thumb = document.createElement('img');
      thumb.src = img.url;
      thumb.alt = img.filename;
      thumb.addEventListener('click', () => openLightbox(img.url, img.filename));

      const removeBtn = document.createElement('button');
      removeBtn.className = 'attach-remove-btn';
      removeBtn.textContent = '✕';
      removeBtn.title = 'Entfernen';
      removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        state.attachedImages.splice(idx, 1);
        renderAttachmentStrip();
      });

      card.appendChild(thumb);
      card.appendChild(removeBtn);
      attachmentStrip.appendChild(card);
    });
  }

  // =========================================================================
  // CLIPBOARD PASTE SUPPORT (ZWISCHENABLAGE)
  // =========================================================================
  function setupClipboardPaste() {
    window.addEventListener('paste', async (e) => {
      const items = (e.clipboardData || e.originalEvent.clipboardData).items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
          e.preventDefault();
          const blob = items[i].getAsFile();
          if (blob) {
            await processAndUploadImage(blob);
          }
        }
      }
    });
  }

  // =========================================================================
  // AUTO-EXPANDING TEXTAREA & KEYBOARD SHORTCUTS
  // =========================================================================
  function adjustTextareaHeight() {
    chatInput.style.height = 'auto';
    const newHeight = Math.min(chatInput.scrollHeight, 120);
    chatInput.style.height = `${newHeight}px`;
  }

  // =========================================================================
  // LIGHTBOX MODAL
  // =========================================================================
  function openLightbox(url, name = 'Bildvorschau') {
    lightboxImg.src = url;
    lightboxFilename.textContent = name;
    lightboxDownload.href = url;
    lightboxDownload.setAttribute('download', name);
    lightboxModal.classList.remove('hidden');
  }

  function closeLightbox() {
    lightboxModal.classList.add('hidden');
    lightboxImg.src = '';
  }

  // =========================================================================
  // DIRECTORY BROWSER MODAL
  // =========================================================================
  async function openPathModal() {
    pathModal.classList.remove('hidden');
    manualPathInput.value = state.currentCwd;
    loadFiles(state.currentCwd);
  }

  async function loadFiles(dirPath) {
    fileBrowserList.innerHTML = '<div class="loading-spinner">Lade Ordnerinhalt...</div>';
    try {
      const res = await fetch(`/api/files?path=${encodeURIComponent(dirPath)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Fehler beim Laden');

      manualPathInput.value = data.current_path;
      renderBreadcrumb(data.current_path);

      fileBrowserList.innerHTML = '';
      if (data.parent_path) {
        const parentItem = document.createElement('div');
        parentItem.className = 'file-item is-dir';
        parentItem.innerHTML = `<span>📁 .. (Übergeordneter Ordner)</span>`;
        parentItem.addEventListener('click', () => loadFiles(data.parent_path));
        fileBrowserList.appendChild(parentItem);
      }

      if (data.items.length === 0) {
        const emptyItem = document.createElement('div');
        emptyItem.style.padding = '12px';
        emptyItem.style.color = 'var(--text-muted)';
        emptyItem.style.fontStyle = 'italic';
        emptyItem.style.textAlign = 'center';
        emptyItem.textContent = '(Ordner ist leer)';
        fileBrowserList.appendChild(emptyItem);
      }

      data.items.forEach(item => {
        const el = document.createElement('div');
        el.className = `file-item ${item.is_dir ? 'is-dir' : 'is-file'}`;
        
        let icon = '📄';
        if (item.is_dir) {
          icon = '📁';
        } else if (item.name.endsWith('.py')) {
          icon = '🐍';
        } else if (item.name.endsWith('.pdf')) {
          icon = '📕';
        } else if (item.name.endsWith('.apk')) {
          icon = '🤖';
        } else if (/\.(png|jpe?g|gif|webp|svg)$/i.test(item.name)) {
          icon = '🖼️';
        } else if (/\.(tar\.gz|zip|gz|rar|7z)$/i.test(item.name)) {
          icon = '📦';
        }

        const titleSpan = document.createElement('span');
        titleSpan.innerHTML = `${icon} ${escapeHTML(item.name)}`;
        el.appendChild(titleSpan);

        const actionsWrap = document.createElement('div');
        actionsWrap.className = 'file-item-actions';

        if (item.size) {
          const sizeEl = document.createElement('small');
          sizeEl.style.color = 'var(--text-muted)';
          sizeEl.textContent = formatBytes(item.size);
          actionsWrap.appendChild(sizeEl);
        }

        if (!item.is_dir) {
          const dlBtn = document.createElement('a');
          dlBtn.className = 'file-dl-btn';
          dlBtn.href = `/api/file/download?path=${encodeURIComponent(item.path)}`;
          dlBtn.title = 'Datei auf Smartphone/PC herunterladen';
          dlBtn.textContent = '💾';
          dlBtn.setAttribute('download', item.name);
          dlBtn.addEventListener('click', (e) => e.stopPropagation());
          actionsWrap.appendChild(dlBtn);
        }

        el.appendChild(actionsWrap);

        if (item.is_dir) {
          el.addEventListener('click', () => loadFiles(item.path));
        } else {
          el.addEventListener('click', () => openFileModal(item.path));
        }
        fileBrowserList.appendChild(el);
      });
    } catch (err) {
      fileBrowserList.innerHTML = `<div style="color:var(--accent-red)">Fehler: ${err.message}</div>`;
    }
  }

  // =========================================================================
  // FILE INSPECTOR & AST ANALYZER
  // =========================================================================
  let currentOpenFile = null;
  const btnFileDownload = document.getElementById('btn-file-download');

  async function openFileModal(filePath) {
    currentOpenFile = filePath;
    const filename = filePath.split('/').pop();
    const isPy = filename.endsWith('.py');
    const isImage = /\.(png|jpe?g|gif|webp|svg)$/i.test(filename);
    const isBinaryDoc = /\.(pdf|apk|tar\.gz|zip|gz|rar|7z|bin|so|whl)$/i.test(filename);

    fileModalTitle.textContent = filename;
    fileModalPath.textContent = filePath;
    
    let icon = '📄';
    if (isPy) icon = '🐍';
    else if (isImage) icon = '🖼️';
    else if (filename.endsWith('.pdf')) icon = '📕';
    else if (filename.endsWith('.apk')) icon = '🤖';
    else if (/\.(tar\.gz|zip|gz)$/i.test(filename)) icon = '📦';
    fileModalIcon.textContent = icon;

    fileSizeBadge.textContent = '...';
    fileEditorTextarea.value = 'Lade Dateiinhalt...';

    if (btnFileDownload) {
      btnFileDownload.href = `/api/file/download?path=${encodeURIComponent(filePath)}`;
      btnFileDownload.setAttribute('download', filename);
    }

    // Reset tabs
    switchFileTab('code');
    tabBtnAst.style.display = isPy ? 'block' : 'none';
    tabBtnFlow.style.display = isPy ? 'block' : 'none';
    btnFileRunPython.style.display = isPy ? 'inline-block' : 'none';

    fileModal.classList.remove('hidden');

    // Handle images and binary files gracefully
    if (isImage) {
      fileEditorTextarea.value = `[Bilddatei: ${filename}]\n\nKlicke oben auf '💾 Download' oder öffne das Bild über das Dashboard.`;
      fileSizeBadge.textContent = 'Bild';
      return;
    }

    if (isBinaryDoc) {
      fileEditorTextarea.value = `📕 Dokument / Binärdatei: ${filename}\nPfad: ${filePath}\n\nDiese Datei ist ein Binärformat (z.B. PDF, APK oder Archiv) und kann nicht als Plain Text bearbeitet werden.\n\n💡 Tipp: Klicke oben auf die Schaltfläche '💾 Download', um die Datei direkt auf dein Smartphone oder deinen Computer herunterzuladen.`;
      fileSizeBadge.textContent = filename.split('.').pop().toUpperCase();
      return;
    }

    // 1. Load File Content for text files
    try {
      const res = await fetch(`/api/file/read?path=${encodeURIComponent(filePath)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Fehler beim Lesen');
      fileEditorTextarea.value = data.content;
      fileSizeBadge.textContent = formatBytes(data.size);
    } catch (err) {
      fileEditorTextarea.value = `# Fehler beim Laden:\n# ${err.message}`;
    }

    // 2. Load AST Analysis if Python
    if (isPy) {
      astContent.innerHTML = '<div class="loading-spinner">Analysiere Python AST...</div>';
      flowContent.innerHTML = '<div class="loading-spinner">Erstelle Ablaufdiagramm...</div>';
      try {
        const res = await fetch(`/api/analyze?path=${encodeURIComponent(filePath)}`);
        const data = await res.json();
        if (data.success) {
          renderAstAnalysis(data);
          renderMermaidFlow(data.mermaid);
        } else {
          astContent.innerHTML = `<div style="color:var(--accent-red); padding:10px;">Analysefehler: ${data.error || 'Unbekannt'}</div>`;
          flowContent.innerHTML = `<div style="color:var(--accent-red); padding:10px;">Diagramm konnte nicht erstellt werden.</div>`;
        }
      } catch (err) {
        astContent.innerHTML = `<div style="color:var(--accent-red); padding:10px;">Fehler: ${err.message}</div>`;
        flowContent.innerHTML = `<div style="color:var(--accent-red); padding:10px;">Fehler: ${err.message}</div>`;
      }
    }
  }

  function switchFileTab(tabName) {
    [tabBtnCode, tabBtnAst, tabBtnFlow].forEach(btn => btn.classList.remove('active'));
    [panelCode, panelAst, panelFlow].forEach(p => p.classList.remove('active'));

    if (tabName === 'code') {
      tabBtnCode.classList.add('active');
      panelCode.classList.add('active');
    } else if (tabName === 'ast') {
      tabBtnAst.classList.add('active');
      panelAst.classList.add('active');
    } else if (tabName === 'flow') {
      tabBtnFlow.classList.add('active');
      panelFlow.classList.add('active');
    }
  }

  function renderAstAnalysis(data) {
    const stats = data.stats || {};
    const imports = data.imports || [];
    const classes = data.classes || [];
    const functions = data.functions || [];

    let html = `
      <div class="ast-section">
        <div class="ast-section-title">📊 Datei-Metriken</div>
        <div style="display:flex; gap:6px; flex-wrap:wrap;">
          <span class="ast-pill">Gesamt: ${stats.total_lines || 0} Zeilen</span>
          <span class="ast-pill">Code: ${stats.code_lines || 0} Zeilen</span>
          <span class="ast-pill">Kommentare: ${stats.comment_lines || 0}</span>
          <span class="ast-pill">Funktionen: ${stats.functions_count || 0}</span>
          <span class="ast-pill">Klassen: ${stats.classes_count || 0}</span>
        </div>
      </div>
    `;

    if (imports.length > 0) {
      html += `
        <div class="ast-section">
          <div class="ast-section-title">🌐 Importierte Module (${imports.length})</div>
          <div style="display:flex; gap:4px; flex-wrap:wrap;">
            ${imports.map(i => `<span class="ast-pill" style="background:rgba(192, 132, 252, 0.15); color:#c084fc;">${i.module ? (i.module + '.' + (i.name || '')) : (i.module || i.name)}</span>`).join('')}
          </div>
        </div>
      `;
    }

    if (classes.length > 0) {
      html += `
        <div class="ast-section">
          <div class="ast-section-title">📦 Klassen (${classes.length})</div>
          ${classes.map(c => `
            <div class="ast-card">
              <div class="ast-card-title">class ${c.name}${c.bases.length ? `(${c.bases.join(', ')})` : ''} <small style="color:var(--text-muted); float:right;">Zeile ${c.lineno}</small></div>
              ${c.docstring ? `<div class="ast-card-doc">"${c.docstring}"</div>` : ''}
              <div style="margin-top:6px; font-size:0.75rem; color:var(--text-secondary);">
                Methoden: ${c.methods.map(m => `<code>${m.name}()</code>`).join(', ') || 'Keine'}
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    if (functions.length > 0) {
      html += `
        <div class="ast-section">
          <div class="ast-section-title">⚙️ Funktionen & Methoden (${functions.length})</div>
          ${functions.map(f => `
            <div class="ast-card">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="ast-card-title">${f.is_async ? 'async ' : ''}def ${f.name}(${f.args.join(', ')})</span>
                <button class="small-btn btn-explain-func" data-func="${f.name}" style="padding:2px 8px; font-size:0.7rem;">⚡ Erklären</button>
              </div>
              ${f.docstring ? `<div class="ast-card-doc">"${f.docstring}"</div>` : '<div class="ast-card-doc" style="font-style:italic; color:var(--text-muted);">Kein Docstring</div>'}
              <div style="margin-top:4px; font-size:0.72rem; color:var(--text-muted);">
                Zeilen: ${f.lineno} - ${f.end_lineno}
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    astContent.innerHTML = html;

    // Attach explain button handlers
    astContent.querySelectorAll('.btn-explain-func').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const funcName = e.target.getAttribute('data-func');
        const filename = currentOpenFile.split('/').pop();
        fileModal.classList.add('hidden');
        pathModal.classList.add('hidden');
        chatInput.value = `Erkläre mir die Funktion \`${funcName}()\` in der Datei \`${filename}\` und wofür sie verwendet wird.`;
        adjustTextareaHeight();
        sendMessage();
      });
    });
  }

  function renderMermaidFlow(mermaidCode) {
    if (!mermaidCode) {
      flowContent.innerHTML = '<div style="color:var(--text-muted)">Kein Ablaufdiagramm verfügbar.</div>';
      return;
    }
    flowContent.innerHTML = `
      <div class="ast-section">
        <div class="ast-section-title">📊 Visueller Funktions-Aufrufgraph</div>
        <div class="mermaid-box">${escapeHTML(mermaidCode)}</div>
        <div style="margin-top:8px;">
          <button class="small-btn primary" id="btn-flow-ask-ai">⚡ Diagramm im Chat visualisieren & erklären</button>
        </div>
      </div>
    `;

    const btnFlowAsk = document.getElementById('btn-flow-ask-ai');
    if (btnFlowAsk) {
      btnFlowAsk.addEventListener('click', () => {
        const filename = currentOpenFile.split('/').pop();
        fileModal.classList.add('hidden');
        pathModal.classList.add('hidden');
        chatInput.value = `/analyze ${currentOpenFile}`;
        adjustTextareaHeight();
        sendMessage();
      });
    }
  }

  async function saveCurrentFile() {
    if (!currentOpenFile) return;
    btnFileSave.textContent = '⏳...';
    btnFileSave.disabled = true;
    try {
      const res = await fetch('/api/file/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: currentOpenFile,
          content: fileEditorTextarea.value
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Fehler beim Speichern');
      btnFileSave.textContent = '✅ Gespeichert!';
      setTimeout(() => {
        btnFileSave.textContent = '💾 Speichern';
        btnFileSave.disabled = false;
      }, 1500);
    } catch (err) {
      alert('Fehler beim Speichern: ' + err.message);
      btnFileSave.textContent = '💾 Speichern';
      btnFileSave.disabled = false;
    }
  }

  function runCurrentFilePython() {
    if (!currentOpenFile) return;
    const filename = currentOpenFile.split('/').pop();
    fileModal.classList.add('hidden');
    pathModal.classList.add('hidden');
    chatInput.value = `!python3 ${currentOpenFile}`;
    adjustTextareaHeight();
    sendMessage();
  }

  function askAiAboutCurrentFile() {
    if (!currentOpenFile) return;
    const filename = currentOpenFile.split('/').pop();
    fileModal.classList.add('hidden');
    pathModal.classList.add('hidden');
    chatInput.value = `Erkläre mir die Datei \`${filename}\` (${currentOpenFile}) und wie ihre Funktionen zusammenarbeiten.`;
    adjustTextareaHeight();
    sendMessage();
  }

  function renderBreadcrumb(fullPath) {
    pathBreadcrumb.innerHTML = '';
    const parts = fullPath.split('/').filter(Boolean);
    let accum = '';

    const rootBtn = document.createElement('button');
    rootBtn.className = 'cmd-chip';
    rootBtn.textContent = '/';
    rootBtn.addEventListener('click', () => loadFiles('/'));
    pathBreadcrumb.appendChild(rootBtn);

    parts.forEach(p => {
      accum += '/' + p;
      const target = accum;
      const chip = document.createElement('button');
      chip.className = 'cmd-chip';
      chip.textContent = p;
      chip.addEventListener('click', () => loadFiles(target));
      pathBreadcrumb.appendChild(chip);
    });
  }

  async function applyNewPath(path) {
    try {
      const res = await fetch('/api/cd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Fehler');
      state.currentCwd = data.cwd;
      pathModal.classList.add('hidden');
      fetchStatus();
    } catch (err) {
      alert('Fehler: ' + err.message);
    }
  }

  function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  // =========================================================================
  // SYSTEM INFO MODAL
  // =========================================================================
  async function openInfoModal() {
    infoModal.classList.remove('hidden');
    infoModalContent.innerHTML = '<div class="loading-spinner">Lade Systemstatus...</div>';
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      infoModalContent.innerHTML = `
        <table style="width:100%; border-collapse:collapse; font-size:0.82rem;">
          <tr><td style="padding:6px; color:var(--text-muted)">Plattform:</td><td style="padding:6px; font-weight:600">${data.platform}</td></tr>
          <tr><td style="padding:6px; color:var(--text-muted)">Modell:</td><td style="padding:6px; font-weight:600; color:#c084fc">${data.model}</td></tr>
          <tr><td style="padding:6px; color:var(--text-muted)">Agent Modus:</td><td style="padding:6px; font-weight:600">${data.agent_mode}</td></tr>
          <tr><td style="padding:6px; color:var(--text-muted)">Workspace Pfad:</td><td style="padding:6px; font-family:var(--font-mono)">${data.cwd}</td></tr>
          <tr><td style="padding:6px; color:var(--text-muted)">Gespeicherte Nachrichten:</td><td style="padding:6px">${data.total_messages}</td></tr>
          <tr><td style="padding:6px; color:var(--text-muted)">Erreichbare IPs:</td><td style="padding:6px; font-family:var(--font-mono)">${(data.ips || []).join(', ')}</td></tr>
        </table>
        <div class="callout tip" style="margin-top:12px;">
          <div class="callout-title">💡 Tipp</div>
          <div>Du kannst das Dashboard auf jedem Smartphone im gleichen WLAN unter <code>http://[DEINE-IP]:8080</code> öffnen.</div>
        </div>
      `;
    } catch (err) {
      infoModalContent.innerHTML = `<div style="color:var(--accent-red)">Fehler beim Abrufen: ${err.message}</div>`;
    }
  }

  // =========================================================================
  // CLEAR CHAT
  // =========================================================================
  async function clearChat() {
    if (!confirm('Möchtest du den gesamten Chatverlauf wirklich leeren?')) return;
    try {
      await fetch('/api/history', { method: 'DELETE' });
      messagesList.innerHTML = '';
      welcomeCard.classList.remove('hidden');
    } catch (err) {
      alert('Fehler beim Leeren: ' + err.message);
    }
  }

  // =========================================================================
  // SCROLL TO BOTTOM
  // =========================================================================
  function scrollToBottom(smooth = true) {
    chatContainer.scrollTo({
      top: chatContainer.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto'
    });
  }

  // =========================================================================
  // EVENT LISTENERS SETUP
  // =========================================================================
  function setupEventListeners() {
    // Send message on button click
    btnSend.addEventListener('click', sendMessage);

    // Textarea input & keyboard shortcuts
    chatInput.addEventListener('input', adjustTextareaHeight);
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Quick Command Chips
    document.querySelectorAll('.cmd-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const cmd = chip.getAttribute('data-cmd');
        chatInput.value = cmd;
        adjustTextareaHeight();
        chatInput.focus();
        if (cmd === '/status' || cmd === '/help' || cmd === '!ls' || cmd === '/clear' || cmd === '/storage downloads' || cmd === '/setup-storage') {
          sendMessage();
        }
      });
    });

    // Quick Storage Shortcut Chips in Directory Modal
    document.querySelectorAll('.storage-chip[data-path]').forEach(chip => {
      chip.addEventListener('click', () => {
        const targetPath = chip.getAttribute('data-path');
        loadFiles(targetPath);
      });
    });

    // Termux Setup Storage Trigger in Directory Modal
    const btnSetupStorage = document.getElementById('btn-setup-storage');
    if (btnSetupStorage) {
      btnSetupStorage.addEventListener('click', async () => {
        btnSetupStorage.disabled = true;
        btnSetupStorage.innerHTML = '<span class="chip-icon">⏳</span> Einrichten...';
        try {
          const res = await fetch('/api/setup-storage', { method: 'POST' });
          const data = await res.json();
          btnSetupStorage.innerHTML = '<span class="chip-icon">✅</span> Bereit!';
          if (data.status && data.status.has_downloads) {
            loadFiles('~/storage/downloads');
          } else {
            loadFiles('~/storage');
          }
          alert(data.message || 'Termux Storage wurde erfolgreich eingerichtet!');
        } catch (err) {
          alert('Fehler beim Storage Setup: ' + err.message);
        } finally {
          setTimeout(() => {
            btnSetupStorage.disabled = false;
            btnSetupStorage.innerHTML = '<span class="chip-icon">⚡</span> Setup Storage';
          }, 2000);
        }
      });
    }

    // Image Uploads
    setupImageUploads();

    // Scroll Detection for floating scroll button
    chatContainer.addEventListener('scroll', () => {
      const isNearBottom = chatContainer.scrollHeight - chatContainer.scrollTop - chatContainer.clientHeight < 120;
      if (isNearBottom) {
        scrollBottomBtn.classList.add('hidden');
      } else {
        scrollBottomBtn.classList.remove('hidden');
      }
    });
    scrollBottomBtn.addEventListener('click', () => scrollToBottom(true));

    // Top Bar Modals
    btnOpenPathModal.addEventListener('click', openPathModal);
    pathModalClose.addEventListener('click', () => pathModal.classList.add('hidden'));
    btnApplyPath.addEventListener('click', () => applyNewPath(manualPathInput.value.trim()));

    btnInfo.addEventListener('click', openInfoModal);
    infoModalClose.addEventListener('click', () => infoModal.classList.add('hidden'));

    btnClearChat.addEventListener('click', clearChat);

    // Theme Toggle
    btnTheme.addEventListener('click', () => {
      document.body.classList.toggle('theme-slate');
      const isSlate = document.body.classList.contains('theme-slate');
      btnTheme.querySelector('.btn-icon').textContent = isSlate ? '☀️' : '🌙';
    });

    // File Inspector Modal & Tabs
    fileModalClose.addEventListener('click', () => fileModal.classList.add('hidden'));
    tabBtnCode.addEventListener('click', () => switchFileTab('code'));
    tabBtnAst.addEventListener('click', () => switchFileTab('ast'));
    tabBtnFlow.addEventListener('click', () => switchFileTab('flow'));
    btnFileSave.addEventListener('click', saveCurrentFile);
    btnFileRunPython.addEventListener('click', runCurrentFilePython);
    btnFileAskAi.addEventListener('click', askAiAboutCurrentFile);

    // Lightbox Close
    lightboxClose.addEventListener('click', closeLightbox);
    lightboxBackdrop.addEventListener('click', closeLightbox);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeLightbox();
        pathModal.classList.add('hidden');
        infoModal.classList.add('hidden');
        fileModal.classList.add('hidden');
        stopVoiceCapture(false);
      }
    });
  }

  // Start app on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
