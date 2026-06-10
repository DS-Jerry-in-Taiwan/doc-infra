/**
 * doc-infra 入口頁面 — 動態腳本
 * 讀取 config.json，偵測狀態，渲染頁面
 * 自動從 ngrok API 取得當前 URL
 */

(async function() {
    const app = document.getElementById('app');
    const lastUpdate = document.getElementById('last-update');
    const ngrokUrlEl = document.getElementById('ngrok-url');

    // 抓取 ngrok URL 並顯示在 header
    async function updateNgrokUrl() {
        try {
            const resp = await fetch('/ngrok-info');
            if (resp.ok) {
                const data = await resp.json();
                const url = data.tunnels[0].public_url;
                if (url && ngrokUrlEl) {
                    ngrokUrlEl.textContent = url;
                    ngrokUrlEl.href = url;
                    ngrokUrlEl.target = '_blank';
                    ngrokUrlEl.title = '點擊開啟外部入口';
                }
            } else {
                throw new Error('HTTP ' + resp.status);
            }
        } catch (e) {
            console.log('ngrok URL fetch failed:', e);
            if (ngrokUrlEl) {
                ngrokUrlEl.textContent = window.location.origin;
                ngrokUrlEl.href = window.location.origin;
            }
        }
    }

    // 立即執行（不等 DOMContentLoaded，因為 script 在 body 底部）
    updateNgrokUrl();

    // 讀取 config.json
    let config;
    try {
        const resp = await fetch('/config.json');
        if (!resp.ok) throw new Error('無法載入 config.json');
        config = await resp.json();
    } catch (e) {
        app.innerHTML = `<div class="error-state">載入設定失敗: ${e.message}</div>`;
        return;
    }

    // 更新最後更新時間
    if (lastUpdate) {
        lastUpdate.textContent = config.last_updated || new Date().toLocaleDateString('zh-TW');
    }

    // 按 category 分組（靜態模式不需要檢查 port）
    const groups = {};
    config.projects.forEach(p => {
        if (!groups[p.category]) groups[p.category] = [];
        groups[p.category].push(p);
    });

    // 渲染 HTML
    let html = '';

    const categoryNames = {
        'document': '📁 文件類',
        'source': '📂 原始碼類'
    };

    for (const [category, items] of Object.entries(groups)) {
        const catName = categoryNames[category] || category;
        html += `
            <section class="category">
                <h2 class="category-title">
                    ${catName}
                    <span class="count">${items.length}</span>
                </h2>
                <div class="project-grid">
        `;

        items.forEach(p => {
            const href = p.path || '#';

            html += `
                <a href="${href}" class="project-card">
                    <div class="card-header">
                        <span class="status-indicator running"></span>
                        <span class="card-title">${p.display_name}</span>
                    </div>
                    <div class="card-path">${p.path || '未設定路徑'}</div>
                    <div class="card-description">${p.description || ''}</div>
                    <div class="card-footer">
                        <span class="card-meta">
                            <span class="doc-count">${p.name}</span>
                        </span>
                        <span class="card-status-text running">📄 靜態托管</span>
                    </div>
                </a>
            `;
        });

        html += `
                </div>
            </section>
        `;
    }

    if (config.projects.length === 0) {
        html = '<div class="no-projects">目前沒有設定任何專案入口</div>';
    }

    app.innerHTML = html;
})();
