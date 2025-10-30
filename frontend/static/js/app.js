/**
 * KNS Otomotiv Dijital Asistan - Frontend JavaScript
 * Tüm API çağrıları ve UI yönetimi
 */

// ============================================
// Configuration
// ============================================

const API_BASE_URL = window.location.origin + '/api';
const API_URL = window.location.origin;

// Helper function for getting token
function getToken() {
    return localStorage.getItem('chatbot_token');
}

// Configure marked.js for markdown rendering
if (typeof marked !== 'undefined') {
    marked.setOptions({
        breaks: true,
        gfm: true,
        highlight: function(code, lang) {
            if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return code;
        }
    });
}

// ============================================
// State Management
// ============================================

const AppState = {
    token: localStorage.getItem('chatbot_token'),
    user: JSON.parse(localStorage.getItem('chatbot_user') || 'null'),
    currentScreen: 'login',
    chatHistory: [],
    currentSessionId: localStorage.getItem('chatbot_session_id') || null
};

// ============================================
// Session Management
// ============================================

function generateSessionId() {
    // Generate UUID v4
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// ============================================
// Feedback Management
// ============================================

function getFeedbackKey(messageText) {
    // Mesaj için unique key oluştur (ilk 100 karakter)
    const text = messageText.substring(0, 100);
    // Basit hash fonksiyonu
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
        const char = text.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    const key = `feedback_${AppState.currentSessionId}_${hash}`;
    console.log('[FEEDBACK DEBUG] getFeedbackKey:', {
        sessionId: AppState.currentSessionId,
        hash,
        key,
        messagePreview: text.substring(0, 50)
    });
    return key;
}

function saveFeedback(messageText, reactionType) {
    const key = getFeedbackKey(messageText);
    localStorage.setItem(key, reactionType);
    console.log('[FEEDBACK DEBUG] saveFeedback:', { key, reactionType });
    // Verify it was saved
    const saved = localStorage.getItem(key);
    console.log('[FEEDBACK DEBUG] Verification - saved value:', saved);
}

function getFeedback(messageText) {
    const key = getFeedbackKey(messageText);
    const value = localStorage.getItem(key);
    console.log('[FEEDBACK DEBUG] getFeedback:', { key, value });
    return value;
}

function clearSessionFeedbacks() {
    // Session değiştiğinde eski feedback'leri temizle
    const prefix = `feedback_${AppState.currentSessionId}_`;
    console.log('[FEEDBACK DEBUG] clearSessionFeedbacks called:', {
        currentSessionId: AppState.currentSessionId,
        prefix
    });

    const keysToRemove = [];
    const keysToKeep = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('feedback_')) {
            if (!key.startsWith(prefix)) {
                keysToRemove.push(key);
            } else {
                keysToKeep.push(key);
            }
        }
    }

    console.log('[FEEDBACK DEBUG] Feedback keys to remove:', keysToRemove);
    console.log('[FEEDBACK DEBUG] Feedback keys to keep:', keysToKeep);

    keysToRemove.forEach(key => localStorage.removeItem(key));
}

function createNewSession() {
    const sessionId = generateSessionId();
    AppState.currentSessionId = sessionId;
    localStorage.setItem('chatbot_session_id', sessionId);
    console.log('New session created:', sessionId);
    return sessionId;
}

function clearCurrentSession() {
    AppState.currentSessionId = null;
    localStorage.removeItem('chatbot_session_id');
}

// ============================================
// Utility Functions
// ============================================

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId).classList.add('active');
    AppState.currentScreen = screenId;
}

function showLoading(show = true) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
}

function showTypingIndicator(show = true) {
    const indicator = document.getElementById('typing-indicator');
    if (show) {
        indicator.classList.add('active');
    } else {
        indicator.classList.remove('active');
    }
}

// ============================================
// API Functions
// ============================================

async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (AppState.token) {
        options.headers['Authorization'] = `Bearer ${AppState.token}`;
    }

    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || 'Bir hata oluştu');
        }

        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ============================================
// Authentication
// ============================================

async function handleLogin(event) {
    event.preventDefault();

    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        showLoading();

        const result = await apiCall('/auth/login', 'POST', {
            kullanici_adi: username,
            password: password
        });

        if (result.success) {
            AppState.token = result.token;
            AppState.user = result.kullanici;

            localStorage.setItem('chatbot_token', result.token);
            localStorage.setItem('chatbot_user', JSON.stringify(result.kullanici));

            showScreen('chat-screen');
            initializeChatScreen();
        } else {
            showError('login-error', result.message || 'Giriş başarısız');
        }
    } catch (error) {
        showError('login-error', error.message || 'Giriş başarısız');
    } finally {
        showLoading(false);
    }
}

async function handleRegister(event) {
    event.preventDefault();

    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    try {
        showLoading();

        const result = await apiCall('/auth/register', 'POST', {
            kullanici_adi: username,
            eposta: email,
            password: password
        });

        if (result.success) {
            showError('register-error', 'Kayıt başarılı! Giriş yapabilirsiniz.');
            // Switch to login tab
            document.getElementById('tab-login').click();
        } else {
            showError('register-error', result.message || 'Kayıt başarısız');
        }
    } catch (error) {
        showError('register-error', error.message || 'Kayıt başarısız');
    } finally {
        showLoading(false);
    }
}

function handleLogout() {
    AppState.token = null;
    AppState.user = null;
    localStorage.removeItem('chatbot_token');
    localStorage.removeItem('chatbot_user');
    showScreen('login-screen');
    clearChatMessages();
}

// ============================================
// Chat Functions
// ============================================

function initializeChatScreen() {
    // Set user info
    const user = AppState.user;
    const displayName = user.ad_soyad || user.kullanici_adi || user.tc_kimlik_no;
    const initial = displayName ? displayName.charAt(0).toUpperCase() : 'U';

    document.getElementById('user-initial').textContent = initial;
    document.getElementById('user-name').textContent = displayName;
    document.getElementById('user-email').textContent = user.eposta || 'Bilinmiyor';

    // Show/hide admin buttons based on admin status
    const dashboardBtn = document.getElementById('btn-dashboard');
    const docManageBtn = document.getElementById('btn-doc-manage');
    const isAdmin = user.AdminMi || user.admin_mi || false;

    if (dashboardBtn) {
        dashboardBtn.style.display = isAdmin ? 'flex' : 'none';
    }
    if (docManageBtn) {
        docManageBtn.style.display = isAdmin ? 'flex' : 'none';
    }
    console.log('User admin status:', isAdmin);

    // Create new session if none exists
    if (!AppState.currentSessionId) {
        createNewSession();
    }

    // Clear previous messages
    clearChatMessages();
}

function clearChatMessages() {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <div class="bot-avatar-large">AI</div>
            <h2>Merhaba! Ben KNS Otomotiv Dijital Asistanınızım.</h2>
            <p>Size nasıl yardımcı olabilirim?</p>
            <div class="quick-actions">
                <button class="quick-btn" data-question="Kalan izin hakkım kaç gün?">İzin Hakkı</button>
                <button class="quick-btn" data-question="Üzerimdeki zimmetler neler?">Zimmet Bilgisi</button>
                <button class="quick-btn" data-question="Eğitim almak istiyorum">Eğitim Talebi</button>
            </div>
        </div>
    `;
    AppState.chatHistory = [];

    // Re-attach quick button listeners
    attachQuickButtonListeners();
}

function attachQuickButtonListeners() {
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const question = btn.getAttribute('data-question');
            document.getElementById('chat-input').value = question;
            document.getElementById('chat-form').dispatchEvent(new Event('submit'));
        });
    });
}

function addMessage(text, isUser = false, source = null, confidence = null) {
    const messagesContainer = document.getElementById('chat-messages');

    // Remove welcome message if exists
    const welcomeMessage = messagesContainer.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    if (isUser) {
        const displayName = AppState.user.ad_soyad || AppState.user.kullanici_adi || AppState.user.tc_kimlik_no;
        avatar.textContent = displayName ? displayName.charAt(0).toUpperCase() : 'U';
    } else {
        avatar.textContent = 'AI';
    }

    const content = document.createElement('div');
    content.className = 'message-content';

    // Create text container
    const textContainer = document.createElement('div');
    textContainer.className = 'message-text';

    // Render markdown for bot messages
    if (!isUser && typeof marked !== 'undefined') {
        textContainer.innerHTML = marked.parse(text);
        // Highlight code blocks
        if (typeof hljs !== 'undefined') {
            textContainer.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
    } else {
        textContainer.textContent = text;
    }

    content.appendChild(textContainer);

    // Add metadata container
    const metaContainer = document.createElement('div');
    metaContainer.className = 'message-meta';

    if (!isUser && source) {
        const sourceSpan = document.createElement('span');
        sourceSpan.className = 'message-source';

        // Check if source contains document names (starts with "Dokümanlar:")
        if (source.includes('Dokümanlar:')) {
            const parts = source.split('Dokümanlar:');
            sourceSpan.innerHTML = `Kaynak: Dokümanlar: `;

            // Extract document names and make them clickable
            const docNames = parts[1].split(',').map(name => name.trim());

            docNames.forEach((docName, index) => {
                const docLink = document.createElement('a');
                docLink.href = '#';
                docLink.className = 'doc-link';
                docLink.textContent = docName;
                docLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    showDocumentDetails(docName);
                });

                sourceSpan.appendChild(docLink);

                // Add comma if not last item
                if (index < docNames.length - 1) {
                    sourceSpan.appendChild(document.createTextNode(', '));
                }
            });
        } else {
            sourceSpan.textContent = `Kaynak: ${source}`;
        }

        metaContainer.appendChild(sourceSpan);
    }

    // Add confidence badge for bot messages
    if (!isUser && confidence && confidence > 0) {
        const confidencePercent = Math.round(confidence * 100);
        const confidenceBadge = document.createElement('span');
        confidenceBadge.className = 'confidence-badge';

        // Color based on confidence level
        if (confidencePercent >= 80) {
            confidenceBadge.classList.add('high');
        } else if (confidencePercent >= 50) {
            confidenceBadge.classList.add('medium');
        } else {
            confidenceBadge.classList.add('low');
        }

        confidenceBadge.textContent = `Güven: %${confidencePercent}`;
        confidenceBadge.title = `AI bu cevaptan %${confidencePercent} emin`;
        metaContainer.appendChild(confidenceBadge);
    }

    if (metaContainer.children.length > 0) {
        content.appendChild(metaContainer);
    }

    // Add reaction buttons for bot messages
    if (!isUser) {
        const reactionsDiv = document.createElement('div');
        reactionsDiv.className = 'message-reactions';

        const likeBtn = document.createElement('button');
        likeBtn.className = 'reaction-btn positive';
        likeBtn.innerHTML = '👍';
        likeBtn.title = 'Faydalı';
        likeBtn.onclick = (e) => {
            e.preventDefault();
            console.log('Like button clicked!');
            handleReaction(messageDiv, 'positive', text);
        };

        const dislikeBtn = document.createElement('button');
        dislikeBtn.className = 'reaction-btn negative';
        dislikeBtn.innerHTML = '👎';
        dislikeBtn.title = 'Faydalı değil';
        dislikeBtn.onclick = (e) => {
            e.preventDefault();
            console.log('Dislike button clicked!');
            handleReaction(messageDiv, 'negative', text);
        };

        // Check if feedback already exists and restore state
        const existingFeedback = getFeedback(text);
        if (existingFeedback === 'positive') {
            likeBtn.classList.add('active');
        } else if (existingFeedback === 'negative') {
            dislikeBtn.classList.add('active');
        }

        reactionsDiv.appendChild(likeBtn);
        reactionsDiv.appendChild(dislikeBtn);
        content.appendChild(reactionsDiv);
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function handleReaction(messageDiv, reactionType, messageText) {
    const reactions = messageDiv.querySelectorAll('.reaction-btn');

    // Check if feedback already exists
    const existingFeedback = getFeedback(messageText);
    if (existingFeedback) {
        console.log('Feedback already submitted:', existingFeedback);
        // If user clicks the same button again, allow toggle-off
        if (existingFeedback === reactionType) {
            // Remove from localStorage
            const key = getFeedbackKey(messageText);
            localStorage.removeItem(key);
            reactions.forEach(btn => btn.classList.remove('active'));
            console.log('Feedback removed');
        }
        return; // Prevent duplicate submission
    }

    // Toggle active state
    reactions.forEach(btn => {
        if (btn.classList.contains(reactionType)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Send feedback to backend
    try {
        console.log('Sending feedback:', { reactionType, messageText: messageText.substring(0, 100) });

        const result = await apiCall('/chat/feedback', 'POST', {
            message: messageText.substring(0, 500), // Limit length
            reaction: reactionType,
            timestamp: new Date().toISOString()
        });

        console.log('Feedback sent successfully:', result);

        // Save feedback state to localStorage after successful submission
        saveFeedback(messageText, reactionType);
    } catch (error) {
        console.error('Feedback error:', error);
        // Revert active state if API call failed
        reactions.forEach(btn => btn.classList.remove('active'));
    }
}

async function handleChatSubmit(event) {
    event.preventDefault();

    const input = document.getElementById('chat-input');
    const question = input.value.trim();

    if (!question) return;

    // Ensure we have a session ID
    if (!AppState.currentSessionId) {
        createNewSession();
    }

    // Add user message
    addMessage(question, true);
    input.value = '';

    // Show typing indicator
    showTypingIndicator(true);

    try {
        const result = await apiCall('/chat/ask', 'POST', {
            soru: question,
            session_id: AppState.currentSessionId
        });

        showTypingIndicator(false);

        if (result.success) {
            addMessage(result.cevap, false, result.kaynak, result.guven_skoru);
            AppState.chatHistory.push({
                soru: question,
                cevap: result.cevap,
                kaynak: result.kaynak,
                guven_skoru: result.guven_skoru
            });
        } else {
            addMessage('Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.', false);
        }
    } catch (error) {
        showTypingIndicator(false);
        addMessage('Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.', false);
        console.error('Chat error:', error);
    }
}

function handleNewChat() {
    // Create a new session
    createNewSession();
    // Clear chat messages
    clearChatMessages();
    console.log('Started new chat session');
}

// ============================================
// History Modal
// ============================================

async function showHistoryModal() {
    const modal = document.getElementById('history-modal');
    const historyList = document.getElementById('history-list');

    console.log('[DEBUG] showHistoryModal called');
    console.log('[DEBUG] Modal element:', modal);
    console.log('[DEBUG] History list element:', historyList);

    modal.classList.add('active');
    historyList.innerHTML = '<p class="loading">Yükleniyor...</p>';

    try {
        console.log('[DEBUG] Calling /chat/sessions API...');
        const result = await apiCall('/chat/sessions?limit=20');
        console.log('[DEBUG] API Response:', result);

        if (result.success && result.sessions.length > 0) {
            historyList.innerHTML = '';

            result.sessions.forEach(session => {
                const sessionItem = document.createElement('div');
                sessionItem.className = 'history-item session-item';
                sessionItem.style.cursor = 'pointer';

                const startDate = new Date(session.IlkMesajTarihi);
                const endDate = new Date(session.SonMesajTarihi);
                const startTimeStr = startDate.toLocaleString('tr-TR');
                const endTimeStr = endDate.toLocaleString('tr-TR');

                // Truncate first question if too long
                const firstQuestion = session.IlkSoru ? session.IlkSoru.substring(0, 80) : 'Sohbet';
                const truncated = session.IlkSoru && session.IlkSoru.length > 80 ? '...' : '';

                sessionItem.innerHTML = `
                    <div class="history-item-question">${firstQuestion}${truncated}</div>
                    <div class="history-item-answer">
                        ${session.MesajSayisi} mesaj • ${startTimeStr}
                    </div>
                    <div class="history-item-time">Son mesaj: ${endTimeStr}</div>
                `;

                // Add click handler to load session
                sessionItem.addEventListener('click', () => {
                    loadSession(session.SessionId);
                    closeModals();
                });

                historyList.appendChild(sessionItem);
            });
        } else {
            historyList.innerHTML = '<p class="loading">Henüz sohbet geçmişiniz yok.</p>';
        }
    } catch (error) {
        historyList.innerHTML = '<p class="loading">Geçmiş yüklenirken hata oluştu.</p>';
        console.error('History error:', error);
    }
}

async function loadSession(sessionId) {
    console.log('[FEEDBACK DEBUG] ========================================');
    console.log('[FEEDBACK DEBUG] loadSession called:', sessionId);
    console.log('[FEEDBACK DEBUG] Current sessionId before load:', AppState.currentSessionId);

    try {
        showLoading(true);

        // Get all messages for this session
        const result = await apiCall(`/chat/sessions/${sessionId}`);

        if (result.success && result.messages.length > 0) {
            // Set current session
            console.log('[FEEDBACK DEBUG] Setting currentSessionId to:', sessionId);
            AppState.currentSessionId = sessionId;
            localStorage.setItem('chatbot_session_id', sessionId);
            console.log('[FEEDBACK DEBUG] localStorage chatbot_session_id set to:', sessionId);

            // DON'T clear feedback states - keep all sessions' feedback
            // clearSessionFeedbacks(); // REMOVED - this was deleting other sessions' feedback!
            console.log('[FEEDBACK DEBUG] Keeping all feedback states (not clearing)');

            // Clear current messages
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = '';
            AppState.chatHistory = [];

            console.log('[FEEDBACK DEBUG] Loading', result.messages.length, 'messages...');

            // Display all messages from the session
            result.messages.forEach((msg, index) => {
                console.log(`[FEEDBACK DEBUG] Loading message ${index + 1}/${result.messages.length}`);
                // Add question (user message)
                addMessage(msg.Soru, true);

                // Add answer (bot message)
                addMessage(msg.Cevap, false);

                AppState.chatHistory.push({
                    soru: msg.Soru,
                    cevap: msg.Cevap
                });
            });

            console.log(`[FEEDBACK DEBUG] Loaded ${result.messages.length} messages from session ${sessionId}`);
            console.log('[FEEDBACK DEBUG] ========================================');
        }
    } catch (error) {
        console.error('Error loading session:', error);
        addMessage('Sohbet yüklenirken hata oluştu.', false);
    } finally {
        showLoading(false);
    }
}

// ============================================
// Documents Modal
// ============================================

async function showDocumentsModal() {
    const modal = document.getElementById('documents-modal');
    const documentsList = document.getElementById('documents-list');

    modal.classList.add('active');
    documentsList.innerHTML = '<p class="loading">Yükleniyor...</p>';

    try {
        const result = await apiCall('/documents');

        if (result.success && result.documents.length > 0) {
            documentsList.innerHTML = '';

            result.documents.forEach(doc => {
                const docItem = document.createElement('div');
                docItem.className = 'document-item';

                const sizeKB = (doc.size / 1024).toFixed(2);

                docItem.innerHTML = `
                    <div class="history-item-question">${doc.name}</div>
                    <div class="history-item-answer">Boyut: ${sizeKB} KB | Tür: ${doc.extension}</div>
                `;

                documentsList.appendChild(docItem);
            });
        } else {
            documentsList.innerHTML = '<p class="loading">Henüz doküman yüklenmemiş.</p>';
        }
    } catch (error) {
        documentsList.innerHTML = '<p class="loading">Dokümanlar yüklenirken hata oluştu.</p>';
        console.error('Documents error:', error);
    }
}

// ============================================
// Modal Management
// ============================================

function closeModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
}

// ============================================
// Mobile Menu Management
// ============================================

function toggleMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('mobile-overlay');

    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
}

function closeMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('mobile-overlay');

    sidebar.classList.remove('active');
    overlay.classList.remove('active');
}

function handleResize() {
    // Close mobile sidebar if window is resized to desktop size
    if (window.innerWidth > 768) {
        closeMobileSidebar();
    }
}

// ============================================
// Document Details Modal
// ============================================

async function showDocumentDetails(fileName) {
    // Find document by name
    try {
        const response = await apiCall('/admin/documents');

        if (response.success && response.documents) {
            const doc = response.documents.find(d => d.DosyaAdi === fileName);

            if (doc) {
                // Use DocManage's showChunksModal if available
                if (typeof DocManage !== 'undefined' && DocManage.showChunksModal) {
                    DocManage.showChunksModal(doc.DosyaId, doc.DosyaAdi);
                } else {
                    // Fallback: create simple modal
                    showSimpleChunksModal(doc.DosyaId, doc.DosyaAdi);
                }
            } else {
                alert('Doküman bulunamadı');
            }
        }
    } catch (error) {
        console.error('Document details error:', error);
        alert('Doküman bilgileri alınırken bir hata oluştu');
    }
}

async function showSimpleChunksModal(fileId, fileName) {
    // Create or get chunks modal
    let chunksModal = document.getElementById('chunks-modal');

    if (!chunksModal) {
        // Create modal if it doesn't exist
        chunksModal = document.createElement('div');
        chunksModal.id = 'chunks-modal';
        chunksModal.className = 'modal';
        chunksModal.innerHTML = `
            <div class="modal-content chunks-modal-content">
                <div class="modal-header">
                    <h3 id="chunks-modal-title">Doküman Chunk'ları</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div id="chunks-list" class="chunks-list"></div>
                </div>
            </div>
        `;
        document.body.appendChild(chunksModal);

        // Add close button listener
        chunksModal.querySelector('.modal-close').addEventListener('click', () => {
            chunksModal.classList.remove('active');
        });

        // Close on outside click
        chunksModal.addEventListener('click', (e) => {
            if (e.target === chunksModal) {
                chunksModal.classList.remove('active');
            }
        });
    }

    // Update title
    document.getElementById('chunks-modal-title').textContent = `Chunk'lar: ${fileName}`;

    // Show modal
    chunksModal.classList.add('active');

    // Load chunks
    const chunksList = document.getElementById('chunks-list');
    chunksList.innerHTML = '<p class="loading">Yükleniyor...</p>';

    try {
        const response = await fetch(`/api/admin/documents/${fileId}/chunks`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
            }
        });

        const data = await response.json();

        if (data.success && data.chunks && data.chunks.length > 0) {
            chunksList.innerHTML = data.chunks.map((chunk, index) => `
                <div class="chunk-item">
                    <div class="chunk-header">
                        <span class="chunk-number">Chunk #${chunk.ChunkSirasi}</span>
                        <span class="chunk-date">${new Date(chunk.OlusturmaTarihi).toLocaleString('tr-TR')}</span>
                    </div>
                    <div class="chunk-text">${chunk.ChunkMetni}</div>
                </div>
            `).join('');
        } else {
            chunksList.innerHTML = '<p class="no-documents">Bu doküman için chunk bulunamadı</p>';
        }
    } catch (error) {
        console.error('Chunks loading error:', error);
        chunksList.innerHTML = '<p class="error">Chunk\'lar yüklenirken bir hata oluştu</p>';
    }
}

// ============================================
// Dark Mode Toggle
// ============================================

function initializeTheme() {
    // Check saved theme preference or default to light
    const savedTheme = localStorage.getItem('chatbot_theme') || 'light';
    setTheme(savedTheme);
}

function setTheme(theme) {
    const html = document.documentElement;
    const themeIcon = document.getElementById('theme-icon');

    if (theme === 'dark') {
        html.setAttribute('data-theme', 'dark');
        if (themeIcon) themeIcon.textContent = '☀️';
        localStorage.setItem('chatbot_theme', 'dark');
    } else {
        html.setAttribute('data-theme', 'light');
        if (themeIcon) themeIcon.textContent = '🌙';
        localStorage.setItem('chatbot_theme', 'light');
    }
}

function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

// ============================================
// Event Listeners
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    initializeTheme();

    // Check if user is already logged in
    if (AppState.token && AppState.user) {
        showScreen('chat-screen');
        initializeChatScreen();
    } else {
        showScreen('login-screen');
    }

    // Form submissions
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('chat-form').addEventListener('submit', handleChatSubmit);

    // Sidebar buttons
    document.getElementById('btn-logout').addEventListener('click', handleLogout);
    document.getElementById('btn-new-chat').addEventListener('click', handleNewChat);
    document.getElementById('btn-history').addEventListener('click', showHistoryModal);
    document.getElementById('btn-documents').addEventListener('click', showDocumentsModal);

    // Dashboard button (only if exists, admin only)
    const dashboardBtn = document.getElementById('btn-dashboard');
    if (dashboardBtn) {
        dashboardBtn.addEventListener('click', openDashboard);
    }

    // Document Management button (only if exists, admin only)
    const docManageBtn = document.getElementById('btn-doc-manage');
    if (docManageBtn) {
        docManageBtn.addEventListener('click', () => {
            if (typeof DocManage !== 'undefined') {
                DocManage.open();
            }
        });
    }

    // Modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', closeModals);
    });

    // Close modal when clicking outside
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModals();
            }
        });
    });

    // Quick buttons (initial attach)
    attachQuickButtonListeners();

    // Enter key in chat input
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('chat-form').dispatchEvent(new Event('submit'));
        }
    });

    // Mobile menu button
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', toggleMobileSidebar);
    }

    // Mobile overlay
    const mobileOverlay = document.getElementById('mobile-overlay');
    if (mobileOverlay) {
        mobileOverlay.addEventListener('click', closeMobileSidebar);
    }

    // Close mobile sidebar when clicking on menu items
    document.querySelectorAll('.sidebar .menu-item').forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                closeMobileSidebar();
            }
        });
    });

    // Handle window resize
    window.addEventListener('resize', handleResize);

    // Theme toggle button
    const themeToggleBtn = document.getElementById('theme-toggle');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', toggleTheme);
    }

    console.log('Chatbot initialized successfully');
});
