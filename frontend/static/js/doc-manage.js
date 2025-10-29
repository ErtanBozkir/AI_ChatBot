/**
 * Doküman Yönetimi Modülü
 * Admin doküman yükleme, silme ve listeleme işlemleri
 */

// Document Management State
const DocManage = {
    modal: null,
    uploadForm: null,
    fileInput: null,
    fileNameDisplay: null,
    uploadProgress: null,
    documentsList: null,

    init() {
        this.modal = document.getElementById('doc-manage-modal');
        this.uploadForm = document.getElementById('doc-upload-form');
        this.fileInput = document.getElementById('doc-file-input');
        this.fileNameDisplay = document.getElementById('file-name-display');
        this.uploadProgress = document.getElementById('upload-progress');
        this.documentsList = document.getElementById('admin-documents-list');

        this.setupEventListeners();
    },

    setupEventListeners() {
        // File input change
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    this.fileNameDisplay.textContent = file.name;
                }
            });
        }

        // Upload form submit
        if (this.uploadForm) {
            this.uploadForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.uploadDocument();
            });
        }
    },

    async uploadDocument() {
        const file = this.fileInput.files[0];
        if (!file) {
            this.showError('Lütfen bir dosya seçin');
            return;
        }

        // Validate file type
        const validTypes = ['.pdf', '.doc', '.docx'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        if (!validTypes.includes(fileExt)) {
            this.showError('Sadece PDF ve Word dosyaları yüklenebilir');
            return;
        }

        // Show progress
        this.uploadProgress.style.display = 'block';
        this.uploadForm.style.opacity = '0.5';
        document.getElementById('upload-btn').disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/admin/upload-document', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
                },
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess(`Dosya başarıyla yüklendi! ${data.chunks || 0} chunk oluşturuldu.`);
                this.resetForm();
                await this.loadDocuments();
            } else {
                this.showError(data.error || 'Yükleme başarısız');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showError('Yükleme sırasında bir hata oluştu');
        } finally {
            this.uploadProgress.style.display = 'none';
            this.uploadForm.style.opacity = '1';
            document.getElementById('upload-btn').disabled = false;
        }
    },

    async loadDocuments() {
        if (!this.documentsList) return;

        this.documentsList.innerHTML = '<p class="loading">Yükleniyor...</p>';

        try {
            const response = await fetch('/api/admin/documents', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
                }
            });

            const data = await response.json();

            if (data.success && data.documents) {
                this.renderDocuments(data.documents);
            } else {
                this.documentsList.innerHTML = '<p class="error">Dokümanlar yüklenemedi</p>';
            }
        } catch (error) {
            console.error('Load documents error:', error);
            this.documentsList.innerHTML = '<p class="error">Bağlantı hatası</p>';
        }
    },

    renderDocuments(documents) {
        if (!documents || documents.length === 0) {
            this.documentsList.innerHTML = '<p class="no-documents">Henüz doküman yüklenmemiş</p>';
            return;
        }

        const html = documents.map(doc => this.createDocumentCard(doc)).join('');
        this.documentsList.innerHTML = html;

        // Attach delete event listeners
        this.documentsList.querySelectorAll('.doc-delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const fileId = e.currentTarget.dataset.fileId;
                this.deleteDocument(fileId);
            });
        });
    },

    createDocumentCard(doc) {
        const statusIcon = doc.IslenmeDurumu === 1
            ? '<span class="status-badge success">✓ İşlendi</span>'
            : doc.IslenmeDurumu === 0
            ? '<span class="status-badge processing">⟳ İşleniyor</span>'
            : '<span class="status-badge error">✗ Hata</span>';

        const fileSize = this.formatFileSize(doc.Boyut);
        const uploadDate = new Date(doc.YuklenmeTarihi).toLocaleString('tr-TR');

        return `
            <div class="doc-card">
                <div class="doc-icon">
                    ${doc.DosyaTipi === '.pdf'
                        ? '<svg width="40" height="40" viewBox="0 0 24 24" fill="#d32f2f"><path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M15.5,16C15.5,17.1 14.6,18 13.5,18H11V21H9.5V14H13.5C14.6,14 15.5,14.9 15.5,16M13.5,16.5H11V16.5H13.5M13,9V3.5L18.5,9H13Z"/></svg>'
                        : '<svg width="40" height="40" viewBox="0 0 24 24" fill="#1976d2"><path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M15.5,17C15.5,18.1 14.6,19 13.5,19H11.5C10.4,19 9.5,18.1 9.5,17V16H11V17H13V15H11.5C10.4,15 9.5,14.1 9.5,13V12C9.5,10.9 10.4,10 11.5,10H13.5C14.6,10 15.5,10.9 15.5,12V13H14V12H12V14H13.5C14.6,14 15.5,14.9 15.5,16V17M13,9V3.5L18.5,9H13Z"/></svg>'
                    }
                </div>
                <div class="doc-info">
                    <h5>${doc.DosyaAdi}</h5>
                    <div class="doc-meta">
                        <span>${fileSize}</span>
                        <span>•</span>
                        <span>${doc.ChunkSayisi || 0} chunk</span>
                        <span>•</span>
                        <span>${uploadDate}</span>
                    </div>
                    ${statusIcon}
                    ${doc.IslenmeHatasi ? `<p class="error-text">${doc.IslenmeHatasi}</p>` : ''}
                </div>
                <button class="doc-delete-btn" data-file-id="${doc.DosyaId}" title="Sil">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </button>
            </div>
        `;
    },

    async deleteDocument(fileId) {
        if (!confirm('Bu dokümanı silmek istediğinizden emin misiniz?')) {
            return;
        }

        try {
            const response = await fetch(`/api/admin/documents/${fileId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('Doküman başarıyla silindi');
                await this.loadDocuments();
            } else {
                this.showError(data.error || 'Silme işlemi başarısız');
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showError('Silme sırasında bir hata oluştu');
        }
    },

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    },

    resetForm() {
        this.fileInput.value = '';
        this.fileNameDisplay.textContent = 'PDF veya Word dosyası seçin';
    },

    showSuccess(message) {
        // You can implement a toast/notification system here
        alert(message);
    },

    showError(message) {
        alert('Hata: ' + message);
    },

    open() {
        if (this.modal) {
            this.modal.classList.add('active');
            this.loadDocuments();
        }
    },

    close() {
        if (this.modal) {
            this.modal.classList.remove('active');
            this.resetForm();
        }
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => DocManage.init());
} else {
    DocManage.init();
}
