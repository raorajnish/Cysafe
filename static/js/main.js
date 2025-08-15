// Chatbot functionality
class Chatbot {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.init();
    }

    init() {
        this.createChatbotElements();
        this.bindEvents();
        this.addWelcomeMessage();
    }

    createChatbotElements() {
        // Create chatbot toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'chatbot-toggle';
        toggleBtn.innerHTML = '<i class="fas fa-comments"></i>';
        toggleBtn.id = 'chatbot-toggle';
        document.body.appendChild(toggleBtn);

        // Create chatbot widget
        const widget = document.createElement('div');
        widget.className = 'chatbot-widget';
        widget.id = 'chatbot-widget';
        widget.innerHTML = `
            <div class="chatbot-header d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-0">CyberSafe AI Assistant</h6>
                    <small>Powered by DeepCytes</small>
                </div>
                <button class="btn-close btn-close-white" id="chatbot-close"></button>
            </div>
            <div class="chatbot-messages" id="chatbot-messages"></div>
            <div class="chatbot-input">
                <div class="input-group">
                    <input type="text" class="form-control" id="chatbot-input" placeholder="Ask about cybercrimes, reporting, or safety...">
                    <button class="btn btn-primary" id="chatbot-send">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
                <div class="mt-2 text-center">
                    <small class="text-muted">Emergency: 1930</small>
                </div>
            </div>
        `;
        document.body.appendChild(widget);
    }

    bindEvents() {
        // Toggle chatbot
        document.getElementById('chatbot-toggle').addEventListener('click', () => {
            this.toggleChatbot();
        });

        // Close chatbot
        document.getElementById('chatbot-close').addEventListener('click', () => {
            this.closeChatbot();
        });

        // Send message
        document.getElementById('chatbot-send').addEventListener('click', () => {
            this.sendMessage();
        });

        // Enter key to send
        document.getElementById('chatbot-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    addWelcomeMessage() {
        const welcomeMessage = {
            type: 'bot',
            text: `Hello! I'm CyberSafe AI Assistant powered by DeepCytes intelligence. I can help you with:

🛡️ **Cybercrime Information** - Learn about different types of cyber threats
📞 **Report Assistance** - Guide you through reporting procedures
⚖️ **Legal Guidance** - Information about Indian cyber laws
🔒 **Safety Tips** - Best practices for cyber security
🏢 **DeepCytes Services** - Our AI-enabled cyber intelligence solutions

How can I assist you today?`,
            timestamp: new Date()
        };
        this.addMessage(welcomeMessage);
    }

    toggleChatbot() {
        const widget = document.getElementById('chatbot-widget');
        if (this.isOpen) {
            this.closeChatbot();
        } else {
            this.openChatbot();
        }
    }

    openChatbot() {
        const widget = document.getElementById('chatbot-widget');
        widget.style.display = 'flex';
        this.isOpen = true;
        widget.classList.add('fade-in-up');
        document.getElementById('chatbot-input').focus();
    }

    closeChatbot() {
        const widget = document.getElementById('chatbot-widget');
        widget.style.display = 'none';
        this.isOpen = false;
    }

    sendMessage() {
        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message
        this.addMessage({
            type: 'user',
            text: message,
            timestamp: new Date()
        });

        input.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        // Send to backend
        this.sendToBackend(message);
    }

    async sendToBackend(message) {
        try {
            const response = await fetch('/api/chatbot/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator();

            // Add bot response
            this.addMessage({
                type: 'bot',
                text: data.response,
                timestamp: new Date()
            });

        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator();
            this.addMessage({
                type: 'bot',
                text: 'Sorry, I encountered an error. Please try again.',
                timestamp: new Date()
            });
        }
    }

    addMessage(message) {
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }

    renderMessage(message) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.type}`;
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        if (message.type === 'bot') {
            content.innerHTML = this.formatBotMessage(message.text);
        } else {
            content.textContent = message.text;
        }
        
        messageDiv.appendChild(content);
        messagesContainer.appendChild(messageDiv);
    }

    formatBotMessage(text) {
        // Convert markdown-like formatting to HTML
        let formatted = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
        
        // Convert URLs to clickable links - simplified regex
        formatted = formatted.replace(/(https?:\/\/[^\s]+)/g, function(match) {
            return '<a href="' + match + '" target="_blank" rel="noopener noreferrer" style="color: #2563eb; text-decoration: underline;">' + match + '</a>';
        });
        
        return formatted;
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatbot-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="d-flex align-items-center">
                    <div class="spinner-border spinner-border-sm me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <span>Typing...</span>
                </div>
            </div>
        `;
        messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chatbot-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Utility functions
function incrementClicks(crimeId) {
    // Prevent multiple rapid clicks
    if (window.clickInProgress && window.clickInProgress === crimeId) {
        return;
    }
    
    window.clickInProgress = crimeId;
    
    fetch('/api/increment-clicks/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ crime_id: crimeId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Clicks incremented successfully');
        }
    })
    .catch(error => {
        console.error('Error incrementing clicks:', error);
    })
    .finally(() => {
        // Reset after a short delay to prevent rapid clicking
        setTimeout(() => {
            window.clickInProgress = null;
        }, 1000);
    });
}

function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// Dynamic form fields for admin
function addFormField(containerId, fieldType, placeholder) {
    const container = document.getElementById(containerId);
    const fieldDiv = document.createElement('div');
    fieldDiv.className = 'input-group mb-2';
    fieldDiv.innerHTML = `
        <input type="text" class="form-control" name="${fieldType}[]" placeholder="${placeholder}" required>
        <button class="btn btn-outline-danger" type="button" onclick="removeFormField(this)">
            <i class="fas fa-trash"></i>
        </button>
    `;
    container.appendChild(fieldDiv);
}

function removeFormField(button) {
    button.closest('.input-group').remove();
}

// Search and filter functionality
function filterCrimes() {
    const searchQuery = document.getElementById('search-input')?.value.toLowerCase();
    const categoryFilter = document.getElementById('category-filter')?.value;
    const crimeCards = document.querySelectorAll('.crime-card');

    crimeCards.forEach(card => {
        const title = card.querySelector('.crime-title')?.textContent.toLowerCase();
        const description = card.querySelector('.crime-description')?.textContent.toLowerCase();
        const category = card.dataset.category;

        const matchesSearch = !searchQuery || 
            title.includes(searchQuery) || 
            description.includes(searchQuery);
        
        const matchesCategory = !categoryFilter || category === categoryFilter;

        if (matchesSearch && matchesCategory) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chatbot
    const chatbot = new Chatbot();

    // Initialize search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', filterCrimes);
    }

    const categoryFilter = document.getElementById('category-filter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', filterCrimes);
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading states to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
            }
        });
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Export functions for global access
window.incrementClicks = incrementClicks;
window.addFormField = addFormField;
window.removeFormField = removeFormField;
window.filterCrimes = filterCrimes; 