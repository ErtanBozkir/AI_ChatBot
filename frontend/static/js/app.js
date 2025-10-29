/**
 * Firma Chatbot - Frontend JavaScript
 * Tüm API çağrıları ve UI yönetimi
 */

// ============================================
// Configuration
// ============================================

const API_BASE_URL = window.location.origin + '/api';

// ============================================
// State Management
// ============================================

const AppState = {
    token: localStorage.getItem('chatbot_token'),
    user: JSON.parse(localStorage.getItem('chatbot_user') || 'null'),
    currentScreen: 'login',
    chatHistory: []
};

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
    document.getElementById('user-initial').textContent = user.kullanici_adi.charAt(0).toUpperCase();
    document.getElementById('user-name').textContent = user.kullanici_adi;
    document.getElementById('user-email').textContent = user.eposta;

    // Clear previous messages
    clearChatMessages();
}

function clearChatMessages() {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <div class="bot-avatar-large">AI</div>
            <h2>Merhaba! Ben firma chatbot asistanınızım.</h2>
            <p>Size nasıl yardımcı olabilirim?</p>
            <div class="quick-actions">
                <button class="quick-btn" data-question="Kalan izin hakkım kaç gün?">İzin Hakkı</button>
                <button class="quick-btn" data-question="Maaşım ne zaman yatacak?">Maaş Bilgisi</button>
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

function addMessage(text, isUser = false, source = null) {
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
    avatar.textContent = isUser
        ? AppState.user.kullanici_adi.charAt(0).toUpperCase()
        : 'AI';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;

    if (!isUser && source) {
        const sourceSpan = document.createElement('span');
        sourceSpan.className = 'message-source';
        sourceSpan.textContent = `Kaynak: ${source}`;
        content.appendChild(sourceSpan);
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function handleChatSubmit(event) {
    event.preventDefault();

    const input = document.getElementById('chat-input');
    const question = input.value.trim();

    if (!question) return;

    // Add user message
    addMessage(question, true);
    input.value = '';

    // Show typing indicator
    showTypingIndicator(true);

    try {
        const result = await apiCall('/chat/ask', 'POST', {
            soru: question
        });

        showTypingIndicator(false);

        if (result.success) {
            addMessage(result.cevap, false, result.kaynak);
            AppState.chatHistory.push({
                soru: question,
                cevap: result.cevap,
                kaynak: result.kaynak
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
    clearChatMessages();
}

// ============================================
// History Modal
// ============================================

async function showHistoryModal() {
    const modal = document.getElementById('history-modal');
    const historyList = document.getElementById('history-list');

    modal.classList.add('active');
    historyList.innerHTML = '<p class="loading">Yükleniyor...</p>';

    try {
        const result = await apiCall('/chat/history?limit=20');

        if (result.success && result.history.length > 0) {
            historyList.innerHTML = '';

            result.history.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';

                const date = new Date(item.Tarih);
                const timeStr = date.toLocaleString('tr-TR');

                historyItem.innerHTML = `
                    <div class="history-item-question">${item.Soru}</div>
                    <div class="history-item-answer">${item.Cevap.substring(0, 100)}...</div>
                    <div class="history-item-time">${timeStr}</div>
                `;

                historyList.appendChild(historyItem);
            });
        } else {
            historyList.innerHTML = '<p class="loading">Henüz sohbet geçmişiniz yok.</p>';
        }
    } catch (error) {
        historyList.innerHTML = '<p class="loading">Geçmiş yüklenirken hata oluştu.</p>';
        console.error('History error:', error);
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
// Event Listeners
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Check if user is already logged in
    if (AppState.token && AppState.user) {
        showScreen('chat-screen');
        initializeChatScreen();
    } else {
        showScreen('login-screen');
    }

    // Login/Register tab switching
    document.getElementById('tab-login').addEventListener('click', () => {
        document.getElementById('tab-login').classList.add('active');
        document.getElementById('tab-register').classList.remove('active');
        document.getElementById('login-form').classList.add('active');
        document.getElementById('register-form').classList.remove('active');
    });

    document.getElementById('tab-register').addEventListener('click', () => {
        document.getElementById('tab-register').classList.add('active');
        document.getElementById('tab-login').classList.remove('active');
        document.getElementById('register-form').classList.add('active');
        document.getElementById('login-form').classList.remove('active');
    });

    // Form submissions
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    document.getElementById('chat-form').addEventListener('submit', handleChatSubmit);

    // Sidebar buttons
    document.getElementById('btn-logout').addEventListener('click', handleLogout);
    document.getElementById('btn-new-chat').addEventListener('click', handleNewChat);
    document.getElementById('btn-history').addEventListener('click', showHistoryModal);
    document.getElementById('btn-documents').addEventListener('click', showDocumentsModal);

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

    console.log('Chatbot initialized successfully');
});
