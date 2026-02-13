// Global variables
let currentNoticeId ;

// Load templates when page loads
window.onload = function() {
    loadTemplates();
};

// ✅ 1. LOAD TEMPLATES (Fixes "Load Template" button)
async function loadTemplates() {
    try {
        const response = await fetch('https://legal-ai-pro-1.onrender.com/templates');
        const data = await response.json();
        const select = document.getElementById('templateSelect');
        select.innerHTML = '<option value="">📝 Custom (AI Generate)</option>';
        
        data.templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template;
            option.textContent = template.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Templates failed:', error);
    }
}

// ✅ 2. LOAD TEMPLATE BUTTON (Fixes template loading)
async function loadTemplate() {
    const templateName = document.getElementById('templateSelect').value;
    if (!templateName) {
        showError('Please select a template first');
        return;
    }

    setLoading(true);
    try {
        const response = await fetch(`https://legal-ai-pro-1.onrender.com/template/${templateName}`);
        if (!response.ok) throw new Error('Template not found');
        
        const data = await response.json();
        document.getElementById('dispute').value = data.template;
        showSuccess('✅ Template loaded successfully!');
    } catch (error) {
        showError(`Template failed: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

// ✅ 3. ORIGINAL GENERATE DRAFT (Your existing function - UPDATED)
async function generateDraft() {
    const party1 = document.getElementById('party1').value.trim();
    const party2 = document.getElementById('party2').value.trim();
    const dispute = document.getElementById('dispute').value.trim();
    const template = document.getElementById('templateSelect').value;

    if (!party1 || !party2 || !dispute) {
        showError('Please fill all fields');
        return;
    }

    setLoading(true);
    hideError();

    try {
        const response = await fetch('https://legal-ai-pro-1.onrender.com/generate-legal-notice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                party1_name: party1.split('\n')[0].trim(),
                party1_address: party1.split('\n').slice(1).join(', '),
                party2_name: party2.split('\n')[0].trim(),
                party2_address: party2.split('\n').slice(1).join(', '),
                issue: dispute,
                template: template
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Generation failed');
        }

        const data = await response.json();
        document.getElementById('outputDraft').value = data.draft_text;
        document.getElementById('outputSection').style.display = 'block';
        document.getElementById('outputDraft').scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        showError(`Failed to generate draft: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

// ✅ 4. SAVE NOTICE
async function saveNotice() {
    const party1 = document.getElementById('party1').value.trim();
    const party2 = document.getElementById('party2').value.trim();
    const dispute = document.getElementById('dispute').value.trim();
    const template = document.getElementById('templateSelect').value;

    if (!party1 || !party2 || !dispute) {
        showError('Please fill all fields first');
        return;
    }

    setLoading(true);
    try {
        const response = await fetch('https://legal-ai-pro-1.onrender.com/save-notice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                party1_name: party1.split('\n')[0].trim(),
                party1_address: party1.split('\n').slice(1).join(', '),
                party2_name: party2.split('\n')[0].trim(),
                party2_address: party2.split('\n').slice(1).join(', '),
                issue: dispute,
                template: template
            })
        });

        const data = await response.json();
        currentNoticeId = data.id;
        showSuccess(`✅ Notice saved! ID: ${data.id}`);
    } catch (error) {
        showError('Failed to save notice');
    } finally {
        setLoading(false);
    }
}

// ✅ 5. LOAD HISTORY
async function loadHistory() {
    setLoading(true);
    try {
        const response = await fetch('https://legal-ai-pro-1.onrender.com/history?limit=10');
        const data = await response.json();
        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '';

        if (data.history.length === 0) {
            historyList.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">No notices saved yet. Generate and save one!</p>';
            return;
        }

        data.history.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.innerHTML = `
                <div class="history-info">
                    <strong>${item.party1} vs ${item.party2}</strong><br>
                    <span class="history-meta">${item.issue.substring(0, 60)}...</span><br>
                    <small>${new Date(item.date).toLocaleDateString('en-IN')}</small>
                </div>
                <button onclick="loadNotice(${item.id})" class="btn-small">Load</button>
            `;
            historyList.appendChild(div);
        });
    } catch (error) {
        showError('Failed to load history');
    } finally {
        setLoading(false);
    }
}

// ✅ 6. LOAD NOTICE (Placeholder)
function loadNotice(id) {
    showSuccess(`Loading notice ${id}... (Full feature coming soon)`);
}

// ✅ 7. DOWNLOAD PDF (Your existing - FIXED)
async function downloadPDF() {
    const draft = document.getElementById('outputDraft').value;
    if (!draft) return showError('No draft to download');

    setLoading(true);
    try {
        const party1 = document.getElementById('party1').value;
        const party2 = document.getElementById('party2').value;
        const dispute = document.getElementById('dispute').value;

        const response = await fetch('https://legal-ai-pro-1.onrender.com/download-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                draft_text: draft,
                party1_name: party1.split('\n')[0]?.trim() || '',
                party1_address: party1.split('\n').slice(1).join(', ') || '',
                party2_name: party2.split('\n')[0]?.trim() || '',
                party2_address: party2.split('\n').slice(1).join(', ') || '',
                issue: dispute
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Legal_Notice.pdf';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showSuccess('✅ PDF Downloaded Successfully!');
        
    } catch (error) {
        showError(`PDF failed: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

// ✅ 8. SEND EMAIL
async function sendEmail() {
    const draft = document.getElementById('outputDraft').value;
    if (!draft) return showError('Generate draft first');

    const emailTo = document.getElementById('emailTo').value.trim();
    if (!emailTo.includes('@')) return showError('Enter valid email address');

    setLoading(true);
    try {
        const party1 = document.getElementById('party1').value;
        const party2 = document.getElementById('party2').value;
        const dispute = document.getElementById('dispute').value;

        const response = await fetch('https://legal-ai-pro-1.onrender.com/email-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                draft_text: draft,
                party1_name: party1.split('\n')[0]?.trim() || '',
                party1_address: party1.split('\n').slice(1).join(', ') || '',
                party2_name: party2.split('\n')[0]?.trim() || '',
                party2_address: party2.split('\n').slice(1).join(', ') || '',
                issue: dispute,
                recipient_email: emailTo
            })
        });

        const data = await response.json();
        showSuccess(`✅ Email sent to ${data.recipient}!`);
        document.getElementById('emailTo').value = '';
    } catch (error) {
        showError(`Email failed: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

// ✅ UTILITY FUNCTIONS (Keep your existing ones)
function setLoading(loading) {
    const overlay = document.getElementById('loadingOverlay');
    const btn = document.getElementById('generateBtn');
    const btnText = document.getElementById('btnText');
    const spinner = document.getElementById('btnSpinner');
    
    if (loading) {
        overlay.style.display = 'flex';
        btn.disabled = true;
        btnText.textContent = 'Generating...';
        spinner.style.display = 'inline-block';
    } else {
        overlay.style.display = 'none';
        btn.disabled = false;
        btnText.textContent = 'Generate Legal Notice';
        spinner.style.display = 'none';
    }
}

function showError(message, type = 'error') {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.className = type === 'success' ? 'success-message' : 'error-message';
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    showError(message, 'success');
}

function hideError() {
    document.getElementById('errorMessage').style.display = 'none';
}
