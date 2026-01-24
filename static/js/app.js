// ModaMoments - Reel-based E-commerce App

class ModaMomentsApp {
    constructor() {
        this.reels = [];
        this.filteredReels = [];
        this.currentReelIndex = 0;
        this.videos = [];
        this.searchQuery = '';
        this.init();
    }

    async init() {
        await this.loadFeed();
        this.setupEventListeners();
    }

    async loadFeed() {
        try {
            const response = await fetch('/api/feed');
            const data = await response.json();
            
            if (data.success) {
                this.reels = data.reels;
                this.filteredReels = data.reels;
                this.renderFeed();
                this.hideLoading();
            } else {
                this.showError('Failed to load feed');
            }
        } catch (error) {
            console.error('Error loading feed:', error);
            this.showError('Error loading feed. Please refresh the page.');
        }
    }

    renderFeed(reelsToRender = null) {
        const feedContainer = document.getElementById('reel-feed');
        feedContainer.innerHTML = '';
        this.videos = [];

        const reels = reelsToRender || this.filteredReels;

        reels.forEach((reel, index) => {
            const reelContainer = this.createReelElement(reel, index);
            feedContainer.appendChild(reelContainer);
        });

        // Initialize video playback for the first reel if available
        if (reels.length > 0) {
            this.setupVideoPlayback(0);
        }
    }

    createReelElement(reel, index) {
        const container = document.createElement('div');
        container.className = 'reel-container';
        container.dataset.reelId = reel.id;
        container.dataset.index = index;

        const videoWrapper = document.createElement('div');
        videoWrapper.className = 'reel-video-wrapper';

        const video = document.createElement('video');
        video.className = 'reel-video';
        video.src = reel.url;
        video.loop = true;
        video.muted = true;
        video.playsInline = true;
        video.dataset.reelIndex = index;

        const overlay = document.createElement('div');
        overlay.className = 'reel-overlay';

        // Influencer info
        const influencerInfo = document.createElement('div');
        influencerInfo.className = 'influencer-info';
        
        const avatar = document.createElement('img');
        avatar.className = 'influencer-avatar';
        avatar.src = reel.influencer?.avatar || 'https://ui-avatars.com/api/?name=Influencer&background=random';
        avatar.alt = reel.influencer?.name || 'Influencer';
        
        const influencerDetails = document.createElement('div');
        influencerDetails.className = 'influencer-details';
        influencerDetails.innerHTML = `
            <h3>${reel.influencer?.name || 'Fashion Influencer'}</h3>
            <p>${reel.influencer?.username || '@fashionista'}</p>
        `;
        
        influencerInfo.appendChild(avatar);
        influencerInfo.appendChild(influencerDetails);

        // Description
        const description = document.createElement('div');
        description.className = 'reel-description';
        description.textContent = reel.shortDescription || reel.longDescription;

        // Hashtags
        const hashtagsContainer = document.createElement('div');
        hashtagsContainer.className = 'reel-hashtags';
        if (reel.hashtags && reel.hashtags.length > 0) {
            reel.hashtags.forEach(tag => {
                const hashtag = document.createElement('span');
                hashtag.className = 'hashtag';
                hashtag.textContent = `#${tag.replace('#', '')}`;
                hashtagsContainer.appendChild(hashtag);
            });
        }

        // Shop Now Button
        const shopNowContainer = document.createElement('div');
        shopNowContainer.className = 'shop-now-container';
        const shopNowBtn = document.createElement('button');
        shopNowBtn.className = 'shop-now-btn';
        shopNowBtn.textContent = '🛍️ Shop Now';
        shopNowBtn.onclick = () => this.showProductModal(reel);
        shopNowContainer.appendChild(shopNowBtn);

        overlay.appendChild(influencerInfo);
        overlay.appendChild(description);
        overlay.appendChild(hashtagsContainer);
        overlay.appendChild(shopNowContainer);

        // Side actions
        const sideActions = document.createElement('div');
        sideActions.className = 'reel-side-actions';
        
        const likeBtn = this.createActionButton('❤️', 'like', () => this.toggleLike(index));
        const shareBtn = this.createActionButton('📤', 'share', () => this.shareReel(reel));
        
        sideActions.appendChild(likeBtn);
        sideActions.appendChild(shareBtn);

        videoWrapper.appendChild(video);
        videoWrapper.appendChild(overlay);
        videoWrapper.appendChild(sideActions);
        container.appendChild(videoWrapper);

        this.videos.push(video);
        return container;
    }

    createActionButton(icon, action, onClick) {
        const container = document.createElement('div');
        const btn = document.createElement('button');
        btn.className = 'action-btn';
        btn.textContent = icon;
        btn.onclick = onClick;
        
        const count = document.createElement('div');
        count.className = 'action-count';
        count.textContent = '0';
        
        container.appendChild(btn);
        container.appendChild(count);
        return container;
    }

    setupVideoPlayback(index) {
        // Pause all videos
        this.videos.forEach((video, i) => {
            if (i !== index) {
                video.pause();
            }
        });

        // Play current video
        if (this.videos[index]) {
            this.videos[index].play().catch(err => {
                console.error('Error playing video:', err);
            });
        }
    }

    setupEventListeners() {
        const feedContainer = document.getElementById('reel-feed');
        
        // Handle scroll to detect which reel is in view
        feedContainer.addEventListener('scroll', () => {
            const containers = document.querySelectorAll('.reel-container');
            containers.forEach((container, index) => {
                const rect = container.getBoundingClientRect();
                if (rect.top >= 0 && rect.top < window.innerHeight / 2) {
                    this.currentReelIndex = index;
                    this.setupVideoPlayback(index);
                }
            });
        });

        // Handle intersection observer for better performance
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const index = parseInt(entry.target.dataset.index);
                    this.currentReelIndex = index;
                    this.setupVideoPlayback(index);
                }
            });
        }, {
            threshold: 0.5
        });

        // Observe all reel containers
        setTimeout(() => {
            document.querySelectorAll('.reel-container').forEach(container => {
                observer.observe(container);
            });
        }, 100);

        // Modal close
        const modal = document.getElementById('product-modal');
        const closeBtn = document.querySelector('.close-modal');
        
        closeBtn.onclick = () => {
            modal.classList.remove('active');
        };
        
        window.onclick = (event) => {
            if (event.target === modal) {
                modal.classList.remove('active');
            }
        };

        // Search functionality
        this.setupSearchListeners();
    }

    setupSearchListeners() {
        const searchInput = document.getElementById('search-input');
        const searchClear = document.getElementById('search-clear');
        const feedContainer = document.getElementById('reel-feed');

        // Search input handler
        searchInput.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.toLowerCase().trim();
            this.performSearch();
        });

        // Clear search button
        searchClear.addEventListener('click', () => {
            searchInput.value = '';
            this.searchQuery = '';
            this.performSearch();
        });

        // Show/hide clear button based on input
        searchInput.addEventListener('input', () => {
            if (searchInput.value.length > 0) {
                searchClear.style.display = 'block';
            } else {
                searchClear.style.display = 'none';
            }
        });

        // Focus search on '/' key
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && e.target.tagName !== 'INPUT') {
                e.preventDefault();
                searchInput.focus();
            }
            // Escape to clear search
            if (e.key === 'Escape' && document.activeElement === searchInput) {
                searchInput.value = '';
                this.searchQuery = '';
                this.performSearch();
                searchInput.blur();
            }
        });
    }

    performSearch() {
        if (!this.searchQuery) {
            this.filteredReels = this.reels;
            this.updateSearchResultsCount();
            this.renderFeed();
            return;
        }

        const query = this.searchQuery.toLowerCase();
        this.filteredReels = this.reels.filter(reel => {
            // Search in description
            const description = (reel.shortDescription || '').toLowerCase() + 
                              ' ' + (reel.longDescription || '').toLowerCase();
            
            // Search in hashtags
            const hashtags = (reel.hashtags || []).join(' ').toLowerCase();
            
            // Search in influencer name/username
            const influencerName = (reel.influencer?.name || '').toLowerCase();
            const influencerUsername = (reel.influencer?.username || '').toLowerCase();
            
            // Search in product names
            const productNames = (reel.products || [])
                .map(p => (p.name || '').toLowerCase())
                .join(' ');
            
            // Search in product brands
            const productBrands = (reel.products || [])
                .map(p => (p.brand || '').toLowerCase())
                .join(' ');

            return description.includes(query) ||
                   hashtags.includes(query) ||
                   influencerName.includes(query) ||
                   influencerUsername.includes(query) ||
                   productNames.includes(query) ||
                   productBrands.includes(query);
        });

        this.updateSearchResultsCount();
        this.renderFeed();
        
        // Scroll to top when searching
        const feedContainer = document.getElementById('reel-feed');
        feedContainer.scrollTo({ top: 0, behavior: 'smooth' });
    }

    updateSearchResultsCount() {
        const resultsCount = document.getElementById('search-results-count');
        if (this.searchQuery) {
            const count = this.filteredReels.length;
            resultsCount.textContent = `${count} ${count === 1 ? 'result' : 'results'} found`;
            resultsCount.style.display = 'block';
        } else {
            resultsCount.style.display = 'none';
        }
    }

    showProductModal(reel) {
        const modal = document.getElementById('product-modal');
        const detailsContainer = document.getElementById('product-details');
        
        if (!reel.products || reel.products.length === 0) {
            detailsContainer.innerHTML = '<p>No products available for this reel.</p>';
            modal.classList.add('active');
            return;
        }

        const productsHTML = `
            <h2 style="margin-bottom: 20px; font-size: 24px;">Shop This Look</h2>
            <div class="product-list">
                ${reel.products.map(product => `
                    <div class="product-item">
                        <img src="${product.imageUrl || 'https://via.placeholder.com/120'}" 
                             alt="${product.name}" 
                             class="product-image"
                             onerror="this.src='https://via.placeholder.com/120'">
                        <div class="product-info">
                            <div class="product-name">${product.name}</div>
                            ${product.brand ? `<div class="product-brand">${product.brand}</div>` : ''}
                            <div class="product-price">
                                ${product.priceInfo?.unit || '$'}${product.priceInfo?.value || 'N/A'}
                            </div>
                            ${product.size && product.size.length > 0 ? `
                                <div class="product-sizes">
                                    ${product.size.map(s => `<span class="size-tag">${s}</span>`).join('')}
                                </div>
                            ` : ''}
                            ${product.colors ? `<div style="color: #999; font-size: 13px; margin-bottom: 10px;">Color: ${product.colors}</div>` : ''}
                            <button class="buy-btn" onclick="window.open('https://www.google.com/search?q=${encodeURIComponent(product.name)}', '_blank')">
                                Buy Now
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        detailsContainer.innerHTML = productsHTML;
        modal.classList.add('active');
    }

    toggleLike(index) {
        const likeBtn = document.querySelectorAll('.reel-side-actions .action-btn')[index * 2];
        const countEl = likeBtn.nextElementSibling;
        
        if (likeBtn.classList.contains('liked')) {
            likeBtn.classList.remove('liked');
            likeBtn.textContent = '🤍';
            countEl.textContent = parseInt(countEl.textContent) - 1;
        } else {
            likeBtn.classList.add('liked');
            likeBtn.textContent = '❤️';
            countEl.textContent = parseInt(countEl.textContent) + 1;
        }
    }

    shareReel(reel) {
        if (navigator.share) {
            navigator.share({
                title: reel.shortDescription,
                text: `Check out this fashion reel on ModaMoments!`,
                url: window.location.href + `#reel-${reel.id}`
            }).catch(err => console.log('Error sharing:', err));
        } else {
            // Fallback: copy to clipboard
            const url = window.location.href + `#reel-${reel.id}`;
            navigator.clipboard.writeText(url).then(() => {
                alert('Link copied to clipboard!');
            });
        }
    }

    hideLoading() {
        const loading = document.getElementById('loading');
        const feed = document.getElementById('reel-feed');
        const searchContainer = document.getElementById('search-container');
        loading.style.display = 'none';
        feed.style.display = 'block';
        searchContainer.style.display = 'block';
    }

    showError(message) {
        const loading = document.getElementById('loading');
        loading.innerHTML = `
            <div style="text-align: center;">
                <p style="color: #ff3040; margin-bottom: 20px;">${message}</p>
                <button onclick="location.reload()" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer;">
                    Retry
                </button>
            </div>
        `;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ModaMomentsApp();
});
