let currentEditId = null;

function showTab(tabName) {
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    if (tabName === 'pending') {
        document.querySelector('.tab-button:nth-child(1)').classList.add('active');
        document.getElementById('pending-tab').classList.add('active');
        loadPendingPosts();
    } else if (tabName === 'approved') {
        document.querySelector('.tab-button:nth-child(2)').classList.add('active');
        document.getElementById('approved-tab').classList.add('active');
        loadApprovedPosts();
    } else if (tabName === 'manual') {
        document.querySelector('.tab-button:nth-child(3)').classList.add('active');
        document.getElementById('manual-tab').classList.add('active');
        loadManualScraping();
    }
}

async function loadPendingPosts() {
    const container = document.getElementById('pending-posts');
    container.innerHTML = '<div class="loading">Chargement...</div>';
    
    try {
        const response = await fetch('/api/posts/pending');
        const data = await response.json();
        displayPosts(data.posts, container, 'pending');
    } catch (error) {
        container.innerHTML = '<div class="error">Erreur de chargement</div>';
    }
}

async function loadApprovedPosts() {
    const container = document.getElementById('approved-posts');
    container.innerHTML = '<div class="loading">Chargement...</div>';
    
    try {
        const response = await fetch('/api/posts/approved');
        const data = await response.json();
        displayPosts(data.posts, container, 'approved');
    } catch (error) {
        container.innerHTML = '<div class="error">Erreur de chargement</div>';
    }
}

function displayPosts(posts, container, type) {
    if (posts.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666;">Aucun post à afficher</p>';
        return;
    }
    
    container.innerHTML = posts.map(post => `
        <div class="post-card" data-id="${post.id}">
            <div class="post-meta">
                <span>Domaine: ${post.domain_name || post.style || 'N/A'}</span>
                <span>Sources: ${post.sources_count || 0}</span>
                <span>Généré le: ${new Date(post.generated_at).toLocaleDateString('fr-FR')}</span>
            </div>
            <div class="post-content">${formatPostContent(post.content)}</div>
            <div class="hashtags">
                ${formatHashtags(post.hashtags)}
            </div>
            <div class="post-actions">
                ${type === 'pending' ? 
                    `<button class="approve-btn" onclick="approvePost(${post.id})">Approuver</button>` :
                    `<button class="publish-btn" onclick="publishPost(${post.id})">Publier</button>`
                }
                <button class="edit-btn" onclick="editPost(${post.id})">Éditer</button>
                <button class="delete-btn" onclick="deletePost(${post.id})">Supprimer</button>
            </div>
        </div>
    `).join('');
}

async function approvePost(id) {
    try {
        const response = await fetch(`/api/posts/approve/${id}`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showMessage('Post approuvé avec succès', 'success');
            loadPendingPosts();
        } else {
            showMessage('Erreur lors de l\'approbation', 'error');
        }
    } catch (error) {
        showMessage('Erreur de connexion', 'error');
    }
}

async function publishPost(id) {
    if (!confirm('Voulez-vous vraiment publier ce post sur LinkedIn ?')) return;
    
    try {
        const response = await fetch(`/api/posts/publish/${id}`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showMessage('Post publié avec succès sur LinkedIn !', 'success');
            loadApprovedPosts();
        } else {
            showMessage(`Erreur de publication: ${data.message}`, 'error');
        }
    } catch (error) {
        showMessage('Erreur de connexion', 'error');
    }
}

async function deletePost(id) {
    if (!confirm('Voulez-vous vraiment supprimer ce post ?')) return;
    
    try {
        const response = await fetch(`/api/posts/delete/${id}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.success) {
            showMessage('Post supprimé', 'success');
            document.querySelector(`.post-card[data-id="${id}"]`).remove();
        } else {
            showMessage('Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        showMessage('Erreur de connexion', 'error');
    }
}

function editPost(id) {
    const postCard = document.querySelector(`.post-card[data-id="${id}"]`);
    const content = postCard.querySelector('.post-content').textContent;
    
    currentEditId = id;
    document.getElementById('edit-content').value = content;
    document.getElementById('edit-modal').style.display = 'block';
}

async function saveEdit() {
    const newContent = document.getElementById('edit-content').value;
    
    try {
        const response = await fetch(`/api/posts/edit/${currentEditId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: newContent })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('Post modifié avec succès', 'success');
            closeModal();
            showTab('pending');
        } else {
            showMessage('Erreur lors de la modification', 'error');
        }
    } catch (error) {
        showMessage('Erreur de connexion', 'error');
    }
}

function closeModal() {
    document.getElementById('edit-modal').style.display = 'none';
    currentEditId = null;
}

function showMessage(message, type) {
    const div = document.createElement('div');
    div.className = type;
    div.textContent = message;
    document.querySelector('.container').insertBefore(div, document.querySelector('.tabs'));
    
    setTimeout(() => div.remove(), 3000);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function formatPostContent(content) {
    if (!content) return '';
    
    // Convertir le markdown en HTML basique pour l'affichage
    let formatted = escapeHtml(content);
    
    // Convertir les sauts de ligne en <br>
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Convertir les liens markdown [text](url) en liens HTML
    formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Mettre en gras les textes entre **
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Mettre en italique les textes entre *
    formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Convertir les listes avec bullet points
    formatted = formatted.replace(/^• /gm, '&bull; ');
    formatted = formatted.replace(/^- /gm, '&bull; ');
    
    return formatted;
}

function formatHashtags(hashtags) {
    if (!hashtags) return '';
    
    // Si c'est déjà un string (nouveau format), le diviser en tags
    if (typeof hashtags === 'string') {
        return hashtags.split(' ')
            .filter(tag => tag.trim().startsWith('#'))
            .map(tag => `<span class="hashtag">${escapeHtml(tag.trim())}</span>`)
            .join(' ');
    }
    
    // Si c'est un array (ancien format), le traiter normalement
    if (Array.isArray(hashtags)) {
        return hashtags.map(tag => `<span class="hashtag">${escapeHtml(tag)}</span>`).join(' ');
    }
    
    return '';
}

// Modal close handler
document.querySelector('.close').onclick = closeModal;
window.onclick = function(event) {
    if (event.target == document.getElementById('edit-modal')) {
        closeModal();
    }
}

// Variables for manual scraping
let currentDomain = null;
let scrapedArticles = [];
let selectedArticles = [];

// Manual scraping functions
async function loadManualScraping() {
    await loadDomains();
    resetManualScraping();
}

async function loadDomains() {
    const container = document.getElementById('domains-container');
    container.innerHTML = '<div class="loading">Chargement des domaines...</div>';
    
    try {
        // Charger les domaines et les stats du cache en parallèle
        const [domainsResponse, cacheResponse] = await Promise.all([
            fetch('/api/domains'),
            fetch('/api/cache/domains')
        ]);
        
        const domainsData = await domainsResponse.json();
        const cacheData = await cacheResponse.json();
        
        container.innerHTML = Object.entries(domainsData.domains).map(([key, domain]) => {
            const cacheInfo = cacheData[key];
            const hasCachedArticles = cacheInfo && cacheInfo.cached_count > 0;
            const cacheIndicator = hasCachedArticles 
                ? `<div class="cache-indicator" title="${cacheInfo.cached_count} articles en cache">
                     <span style="color: #28a745;">● ${cacheInfo.cached_count}</span>
                   </div>` 
                : '';
            
            return `
                <div class="domain-card" onclick="selectDomain('${key}')">
                    ${cacheIndicator}
                    <div class="domain-name">${domain.name}</div>
                    <div class="domain-description">${domain.description}</div>
                    <div class="domain-color" style="background-color: ${domain.color}"></div>
                </div>
            `;
        }).join('');
    } catch (error) {
        container.innerHTML = '<div class="error">Erreur lors du chargement des domaines</div>';
    }
}

async function selectDomain(domain) {
    // Reset previous state
    resetManualScraping();
    
    // Update UI
    document.querySelectorAll('.domain-card').forEach(card => {
        card.classList.remove('selected');
    });
    event.target.closest('.domain-card').classList.add('selected');
    
    currentDomain = domain;
    
    // Start scraping
    await scrapeDomain(domain);
}

async function scrapeDomain(domain, forceRefresh = false) {
    const articlesSection = document.getElementById('articles-section');
    const container = document.getElementById('articles-container');
    
    articlesSection.style.display = 'block';
    container.innerHTML = '<div class="loading">Scraping en cours...</div>';
    
    try {
        const response = await fetch(`/api/scrape/${domain}`, { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ force_refresh: forceRefresh })
        });
        const data = await response.json();
        
        if (data.success) {
            scrapedArticles = data.articles;
            displayArticles(scrapedArticles);
            const cacheInfo = data.from_cache ? ' (depuis le cache)' : '';
            showMessage(`${data.total_count} articles trouvés pour ${domain}${cacheInfo}`, 'success');
        } else {
            container.innerHTML = `<div class="error">Erreur: ${data.message}</div>`;
        }
    } catch (error) {
        container.innerHTML = '<div class="error">Erreur lors du scraping</div>';
        console.error('Scraping error:', error);
    }
}

function displayArticles(articles) {
    const container = document.getElementById('articles-container');
    
    if (articles.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666;">Aucun article trouvé</p>';
        return;
    }
    
    container.innerHTML = articles.map((article, index) => `
        <div class="article-card" data-index="${index}" onclick="toggleArticle(${index})">
            <input type="checkbox" class="article-checkbox" ${selectedArticles.includes(index) ? 'checked' : ''}>
            <div class="article-meta">
                <span class="article-source">${article.source}</span>
                <span class="article-score">Score: ${Math.round(article.relevance_score || 0)}</span>
            </div>
            <div class="article-title">${article.title}</div>
            <div class="article-summary">${(article.summary || '').substring(0, 150)}...</div>
        </div>
    `).join('');
    
    updateSelectionCount();
}

function toggleArticle(index) {
    const checkbox = document.querySelector(`[data-index="${index}"] .article-checkbox`);
    const card = document.querySelector(`[data-index="${index}"]`);
    
    if (selectedArticles.includes(index)) {
        selectedArticles = selectedArticles.filter(i => i !== index);
        checkbox.checked = false;
        card.classList.remove('selected');
    } else {
        selectedArticles.push(index);
        checkbox.checked = true;
        card.classList.add('selected');
    }
    
    updateSelectionCount();
    updateGenerateButton();
}

function selectAllArticles() {
    selectedArticles = scrapedArticles.map((_, index) => index);
    document.querySelectorAll('.article-card').forEach((card, index) => {
        card.classList.add('selected');
        card.querySelector('.article-checkbox').checked = true;
    });
    updateSelectionCount();
    updateGenerateButton();
}

function deselectAllArticles() {
    selectedArticles = [];
    document.querySelectorAll('.article-card').forEach(card => {
        card.classList.remove('selected');
        card.querySelector('.article-checkbox').checked = false;
    });
    updateSelectionCount();
    updateGenerateButton();
}

function updateSelectionCount() {
    const count = selectedArticles.length;
    document.getElementById('selection-count').textContent = `${count} article${count !== 1 ? 's' : ''} sélectionné${count !== 1 ? 's' : ''}`;
}

function updateGenerateButton() {
    const button = document.getElementById('generate-btn');
    const generationSection = document.getElementById('generation-section');
    
    if (selectedArticles.length >= 2) {
        button.disabled = false;
        generationSection.style.display = 'block';
    } else {
        button.disabled = true;
        if (selectedArticles.length === 0) {
            generationSection.style.display = 'none';
        }
    }
}

async function generateFromSelection() {
    const button = document.getElementById('generate-btn');
    const status = document.getElementById('generation-status');
    
    if (selectedArticles.length < 2) {
        showMessage('Sélectionnez au moins 2 articles', 'error');
        return;
    }
    
    button.disabled = true;
    status.innerHTML = 'Génération en cours...';
    status.className = 'generation-status loading';
    
    try {
        const articlesToGenerate = selectedArticles.map(index => scrapedArticles[index]);
        
        const response = await fetch('/api/generate-from-selection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                articles: articlesToGenerate,
                domain: currentDomain
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            status.innerHTML = `✅ ${data.message}`;
            status.className = 'generation-status success';
            
            // Reset and show success
            setTimeout(() => {
                showMessage('Post généré avec succès ! Consultez l\'onglet "Posts en attente"', 'success');
                showTab('pending');
            }, 2000);
        } else {
            status.innerHTML = `❌ ${data.message}`;
            status.className = 'generation-status error';
            button.disabled = false;
        }
    } catch (error) {
        status.innerHTML = '❌ Erreur lors de la génération';
        status.className = 'generation-status error';
        button.disabled = false;
        console.error('Generation error:', error);
    }
}

function resetManualScraping() {
    selectedArticles = [];
    scrapedArticles = [];
    
    document.getElementById('articles-section').style.display = 'none';
    document.getElementById('generation-section').style.display = 'none';
    document.getElementById('articles-container').innerHTML = '';
    document.getElementById('generation-status').innerHTML = '';
    document.getElementById('selection-count').textContent = '0 articles sélectionnés';
}

// Load initial content
loadPendingPosts();