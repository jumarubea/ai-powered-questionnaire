class QuestionnaireApp {
    constructor() {
        this.sessionId = null;
        this.currentQuestion = null;
        this.totalQuestions = 0;
        this.answeredCount = 0;

        this.messagesEl = document.getElementById('messages');
        this.inputAreaEl = document.getElementById('input-area');
        this.startScreenEl = document.getElementById('start-screen');
        this.startBtn = document.getElementById('start-btn');
        this.progressEl = document.getElementById('progress');
        this.progressBarEl = document.getElementById('progress-bar');

        this.startBtn.addEventListener('click', () => this.start());
    }

    async start() {
        this.startScreenEl.classList.add('hidden');
        this.addLoadingMessage();

        try {
            const response = await fetch('/api/start', { method: 'POST' });
            const data = await response.json();

            this.removeLoadingMessage();
            this.sessionId = data.session_id;
            this.currentQuestion = data.question;

            this.addMessage(data.message, 'ai');

            if (!data.is_complete && data.question) {
                this.showInput(data.question);
                this.progressEl.classList.remove('hidden');
            }
        } catch (error) {
            this.removeLoadingMessage();
            this.addMessage('Sorry, something went wrong. Please refresh and try again.', 'ai');
        }
    }

    async submitResponse(value) {
        // Add user message
        this.addUserMessage(value);
        this.inputAreaEl.classList.add('hidden');
        this.addLoadingMessage();

        try {
            const response = await fetch('/api/respond', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    value: value
                })
            });

            const data = await response.json();
            this.removeLoadingMessage();

            this.addMessage(data.message, 'ai');

            if (data.is_complete) {
                this.showCompletion();
            } else if (data.question) {
                this.currentQuestion = data.question;
                if (!data.needs_clarification) {
                    this.answeredCount++;
                    this.updateProgress();
                }
                this.showInput(data.question);
            }
        } catch (error) {
            this.removeLoadingMessage();
            this.addMessage('Sorry, something went wrong. Please try again.', 'ai');
            this.showInput(this.currentQuestion);
        }
    }

    addMessage(text, type) {
        const div = document.createElement('div');
        div.className = `message ${type}`;
        div.textContent = text;
        this.messagesEl.appendChild(div);
        this.scrollToBottom();
    }

    addUserMessage(value) {
        let displayValue = value;
        if (Array.isArray(value)) {
            displayValue = value.join(', ');
        } else if (typeof value === 'boolean') {
            displayValue = value ? 'Yes' : 'No';
        }
        this.addMessage(displayValue, 'user');
    }

    addLoadingMessage() {
        const div = document.createElement('div');
        div.className = 'message ai loading';
        div.id = 'loading-message';
        div.innerHTML = '<span></span><span></span><span></span>';
        this.messagesEl.appendChild(div);
        this.scrollToBottom();
    }

    removeLoadingMessage() {
        const loading = document.getElementById('loading-message');
        if (loading) loading.remove();
    }

    scrollToBottom() {
        this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    }

    showInput(question) {
        this.inputAreaEl.innerHTML = '';
        this.inputAreaEl.classList.remove('hidden');

        switch (question.type) {
            case 'text':
                this.showTextInput(question);
                break;
            case 'numeric':
                this.showNumericInput(question);
                break;
            case 'radio':
                this.showRadioInput(question);
                break;
            case 'checkbox':
                this.showCheckboxInput(question);
                break;
            case 'yes_no':
                this.showYesNoInput(question);
                break;
            case 'date':
                this.showDateInput(question);
                break;
            default:
                this.showTextInput(question);
        }

        this.scrollToBottom();
    }

    showTextInput(question) {
        const html = `
            <div class="input-group">
                <input type="text" class="text-input" id="text-response"
                       placeholder="${question.placeholder || 'Type your response...'}"
                       autocomplete="off">
                <button class="btn-primary" id="submit-btn">Send</button>
            </div>
        `;
        this.inputAreaEl.innerHTML = html;

        const input = document.getElementById('text-response');
        const btn = document.getElementById('submit-btn');

        btn.addEventListener('click', () => this.submitResponse(input.value));
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.submitResponse(input.value);
        });
        input.focus();
    }

    showNumericInput(question) {
        const min = question.min_value !== null ? `min="${question.min_value}"` : '';
        const max = question.max_value !== null ? `max="${question.max_value}"` : '';

        const html = `
            <input type="number" class="number-input" id="number-response"
                   ${min} ${max} placeholder="${question.placeholder || 'Enter a number'}">
            <button class="btn-primary" id="submit-btn">Send</button>
        `;
        this.inputAreaEl.innerHTML = html;

        const input = document.getElementById('number-response');
        const btn = document.getElementById('submit-btn');

        btn.addEventListener('click', () => this.submitResponse(Number(input.value)));
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.submitResponse(Number(input.value));
        });
        input.focus();
    }

    showRadioInput(question) {
        let optionsHtml = question.options.map((opt, i) => `
            <div class="option-item">
                <input type="radio" name="radio-response" id="opt-${i}" value="${opt}">
                <label for="opt-${i}">${opt}</label>
            </div>
        `).join('');

        if (question.allow_other) {
            const otherIdx = question.options.length;
            optionsHtml += `
                <div class="option-item">
                    <input type="radio" name="radio-response" id="opt-${otherIdx}" value="__other__">
                    <label for="opt-${otherIdx}">Other</label>
                </div>
            `;
        }

        const otherInputHtml = question.allow_other ? `
            <div class="other-input-wrapper hidden" id="other-wrapper">
                <input type="text" class="other-text-input" id="other-text"
                       placeholder="Please specify your answer..." autocomplete="off">
            </div>
        ` : '';

        const html = `
            <div class="options-group">${optionsHtml}</div>
            ${otherInputHtml}
            <button class="btn-primary" id="submit-btn">Send</button>
        `;
        this.inputAreaEl.innerHTML = html;

        // Show/hide "Other" text input based on radio selection
        if (question.allow_other) {
            const radios = document.querySelectorAll('input[name="radio-response"]');
            const otherWrapper = document.getElementById('other-wrapper');
            const otherText = document.getElementById('other-text');
            radios.forEach(radio => {
                radio.addEventListener('change', () => {
                    const isOther = document.querySelector('input[name="radio-response"]:checked')?.value === '__other__';
                    otherWrapper.classList.toggle('hidden', !isOther);
                    if (isOther) otherText.focus();
                });
            });
        }

        const btn = document.getElementById('submit-btn');
        btn.addEventListener('click', () => {
            const selected = document.querySelector('input[name="radio-response"]:checked');
            if (selected) {
                if (selected.value === '__other__') {
                    const otherVal = document.getElementById('other-text').value.trim();
                    if (otherVal) this.submitResponse(otherVal);
                } else {
                    this.submitResponse(selected.value);
                }
            }
        });
    }

    showCheckboxInput(question) {
        let optionsHtml = question.options.map((opt, i) => `
            <div class="option-item">
                <input type="checkbox" name="checkbox-response" id="chk-${i}" value="${opt}">
                <label for="chk-${i}">${opt}</label>
            </div>
        `).join('');

        if (question.allow_other) {
            const otherIdx = question.options.length;
            optionsHtml += `
                <div class="option-item">
                    <input type="checkbox" name="checkbox-response" id="chk-${otherIdx}" value="__other__">
                    <label for="chk-${otherIdx}">Other</label>
                </div>
            `;
        }

        const otherInputHtml = question.allow_other ? `
            <div class="other-input-wrapper hidden" id="other-wrapper">
                <input type="text" class="other-text-input" id="other-text"
                       placeholder="Please specify your answer..." autocomplete="off">
            </div>
        ` : '';

        const html = `
            <div class="options-group">${optionsHtml}</div>
            ${otherInputHtml}
            <button class="btn-primary" id="submit-btn">Send</button>
        `;
        this.inputAreaEl.innerHTML = html;

        // Show/hide "Other" text input based on checkbox state
        if (question.allow_other) {
            const otherCheckbox = document.getElementById(`chk-${question.options.length}`);
            const otherWrapper = document.getElementById('other-wrapper');
            const otherText = document.getElementById('other-text');
            otherCheckbox.addEventListener('change', () => {
                otherWrapper.classList.toggle('hidden', !otherCheckbox.checked);
                if (otherCheckbox.checked) otherText.focus();
            });
        }

        const btn = document.getElementById('submit-btn');
        btn.addEventListener('click', () => {
            const checked = document.querySelectorAll('input[name="checkbox-response"]:checked');
            const values = Array.from(checked).map(el => {
                if (el.value === '__other__') {
                    const otherVal = document.getElementById('other-text').value.trim();
                    return otherVal || null;
                }
                return el.value;
            }).filter(v => v !== null);
            this.submitResponse(values);
        });
    }

    showYesNoInput(question) {
        const html = `
            <div class="yes-no-group">
                <button class="yes-no-btn" data-value="true">Yes</button>
                <button class="yes-no-btn" data-value="false">No</button>
            </div>
        `;
        this.inputAreaEl.innerHTML = html;

        const buttons = document.querySelectorAll('.yes-no-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                buttons.forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                setTimeout(() => {
                    this.submitResponse(btn.dataset.value === 'true');
                }, 200);
            });
        });
    }

    showDateInput(question) {
        const html = `
            <input type="date" class="date-input" id="date-response">
            <button class="btn-primary" id="submit-btn">Send</button>
        `;
        this.inputAreaEl.innerHTML = html;

        const input = document.getElementById('date-response');
        const btn = document.getElementById('submit-btn');

        btn.addEventListener('click', () => this.submitResponse(input.value));
        input.focus();
    }

    updateProgress() {
        // Fetch status to get total questions
        fetch(`/api/status/${this.sessionId}`)
            .then(res => res.json())
            .then(data => {
                const percent = (data.response_count / data.total_questions) * 100;
                this.progressBarEl.style.width = `${percent}%`;
            });
    }

    showCompletion() {
        this.inputAreaEl.classList.add('hidden');
        this.progressBarEl.style.width = '100%';

        const div = document.createElement('div');
        div.className = 'completion-message';
        div.innerHTML = `
            <div class="checkmark">✓</div>
            <p>Your responses have been saved.</p>
            <button class="share-link" id="share-btn">Share with friends</button>
        `;
        this.messagesEl.appendChild(div);
        this.scrollToBottom();

        document.getElementById('share-btn').addEventListener('click', () => this.showSharePopup());
    }

    showSharePopup() {
        const shareUrl = 'https://form.powerconnect.me';

        // Remove existing popup if any
        const existing = document.getElementById('share-popup-overlay');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.id = 'share-popup-overlay';
        overlay.className = 'share-overlay';
        overlay.innerHTML = `
            <div class="share-popup">
                <button class="share-close" id="share-close">&times;</button>
                <h3>Share with friends</h3>
                <p>Copy the link below and send it to your friends:</p>
                <div class="share-url-group">
                    <input type="text" class="share-url-input" id="share-url" value="${shareUrl}" readonly>
                    <button class="btn-primary share-copy-btn" id="share-copy">Copy</button>
                </div>
                <p class="share-copied hidden" id="share-copied">Copied to clipboard!</p>
            </div>
        `;
        document.body.appendChild(overlay);

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.remove();
        });

        // Close button
        document.getElementById('share-close').addEventListener('click', () => overlay.remove());

        // Copy button
        document.getElementById('share-copy').addEventListener('click', () => {
            const urlInput = document.getElementById('share-url');
            urlInput.select();
            urlInput.setSelectionRange(0, 99999);
            document.execCommand('copy');

            const copiedMsg = document.getElementById('share-copied');
            copiedMsg.classList.remove('hidden');
            const copyBtn = document.getElementById('share-copy');
            copyBtn.textContent = 'Copied!';
            setTimeout(() => {
                copiedMsg.classList.add('hidden');
                copyBtn.textContent = 'Copy';
            }, 2000);
        });
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    window.app = new QuestionnaireApp();
});
