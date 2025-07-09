let currentEditId = null;

function showTab(tabName) {
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    if (tabName === 'pending') {
        document.querySelector('.tab-button:first-child').classList.add('active');
        document.getElementById('pending-tab').classList.add('active');
        loadPendingPosts();
    } else {
        document.querySelector('.tab-button:last-child').classList.add('active');
        document.getElementById('approved-tab').classList.add('active');
        loadApprovedPosts();
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
                <span>Style: ${post.style || 'N/A'}</span>
                <span>Généré le: ${new Date(post.generated_at).toLocaleDateString('fr-FR')}</span>
            </div>
            <div class="post-content">${escapeHtml(post.content)}</div>
            <div class="hashtags">
                ${post.hashtags.map(tag => `<span class="hashtag">${tag}</span>`).join('')}
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

// Modal close handler
document.querySelector('.close').onclick = closeModal;
window.onclick = function(event) {
    if (event.target == document.getElementById('edit-modal')) {
        closeModal();
    }
}

// Load initial content
loadPendingPosts();