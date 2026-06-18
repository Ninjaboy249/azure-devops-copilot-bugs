// Azure DevOps Bug Tracker - Frontend Application

let currentBugs = [];

function quickQuery(prompt) {
    document.getElementById('promptInput').value = prompt;
    submitQuery();
}

async function submitQuery() {
    const prompt = document.getElementById('promptInput').value.trim();
    if (!prompt) {
        alert('Please enter a query.');
        return;
    }

    showLoading();
    hideError();
    hideResults();

    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch bugs.');
        }

        currentBugs = data.bugs;
        renderResults(data);

    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

function renderResults(data) {
    const { bugs, total, query } = data;

    // Update header
    document.getElementById('resultsTitle').textContent = `Results for: "${query}"`;
    document.getElementById('resultsCount').textContent = `${total} bug${total !== 1 ? 's' : ''}`;

    // Render stats
    renderStats(bugs);

    // Render table
    const tbody = document.getElementById('bugsTableBody');
    tbody.innerHTML = '';

    bugs.forEach(bug => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${bug.id}</strong></td>
            <td>${escapeHtml(bug.title)}</td>
            <td><span class="state-badge state-${bug.state.toLowerCase()}">${bug.state}</span></td>
            <td><span class="priority-cell priority-${bug.priority}">P${bug.priority}</span></td>
            <td>${escapeHtml(bug.severity || '-')}</td>
            <td>${escapeHtml(bug.assigned_to)}</td>
            <td>${bug.created_date}</td>
            <td>${escapeHtml(bug.iteration_path || '-')}</td>
        `;
        tbody.appendChild(row);
    });

    showResults();
}

function renderStats(bugs) {
    const stats = {
        total: bugs.length,
        p1: bugs.filter(b => b.priority === 1).length,
        p2: bugs.filter(b => b.priority === 2).length,
        active: bugs.filter(b => b.state === 'Active').length,
        resolved: bugs.filter(b => b.state === 'Resolved').length,
    };

    const container = document.getElementById('statsCards');
    container.innerHTML = `
        <div class="stat-card">
            <div class="number">${stats.total}</div>
            <div class="label">Total</div>
        </div>
        <div class="stat-card critical">
            <div class="number">${stats.p1}</div>
            <div class="label">P1 Critical</div>
        </div>
        <div class="stat-card high">
            <div class="number">${stats.p2}</div>
            <div class="label">P2 High</div>
        </div>
        <div class="stat-card active">
            <div class="number">${stats.active}</div>
            <div class="label">Active</div>
        </div>
        <div class="stat-card resolved">
            <div class="number">${stats.resolved}</div>
            <div class="label">Resolved</div>
        </div>
    `;
}

async function exportData(format) {
    if (!currentBugs.length) {
        alert('No data to export. Run a query first.');
        return;
    }

    try {
        const response = await fetch(`/export/${format}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bugs: currentBugs })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Export failed.');
        }

        // Download file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        const contentDisposition = response.headers.get('Content-Disposition');
        const filename = contentDisposition
            ? contentDisposition.split('filename=')[1].replace(/"/g, '')
            : `bugs_export.${format === 'excel' ? 'xlsx' : 'csv'}`;

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

    } catch (error) {
        alert(`Export error: ${error.message}`);
    }
}

// Utility functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading() { document.getElementById('loading').classList.remove('hidden'); }
function hideLoading() { document.getElementById('loading').classList.add('hidden'); }
function showResults() { document.getElementById('results').classList.remove('hidden'); }
function hideResults() { document.getElementById('results').classList.add('hidden'); }
function showError(msg) {
    document.getElementById('errorMessage').textContent = msg;
    document.getElementById('error').classList.remove('hidden');
}
function hideError() { document.getElementById('error').classList.add('hidden'); }

// Enter key support
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('promptInput');
    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitQuery();
            }
        });
    }
});
