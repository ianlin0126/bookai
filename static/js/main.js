// DOM Elements
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');
const popularBooks = document.getElementById('popular-books');
const bookModal = document.getElementById('book-modal');
const modalTitle = document.getElementById('modal-title');
const modalAuthor = document.getElementById('modal-author');
const modalContent = document.getElementById('modal-content');
const bookCover = document.getElementById('book-cover');
const bookButton = document.getElementById('book-button');
const bookSummary = document.getElementById('book-summary');
const bookQA = document.getElementById('book-qa');
const refreshButton = document.getElementById('refresh-button');
const loadingState = document.getElementById('loading-state');
const searchForm = document.getElementById('search-form');

let currentBookId = null;

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Helper functions
function getMediumCoverUrl(url) {
    if (!url) return null;
    return url.replace(/-[LS]\.jpg$/, '-M.jpg');
}

// Create book card HTML
function createBookCard(book, onclick) {
    return `
        <div class="book-card bg-white rounded shadow-sm overflow-hidden cursor-pointer hover:shadow-md transition-shadow duration-200 w-[180px]" 
             onclick="${onclick}">
            <div class="h-[280px] bg-white flex items-center justify-center overflow-hidden">
                ${book.cover_image_url ? 
                    `<img src="${getMediumCoverUrl(book.cover_image_url)}" 
                         alt="${book.title}" 
                         class="h-full w-auto object-contain"
                         style="min-height: 100%;">` :
                    '<div class="w-full h-full bg-gray-200 flex items-center justify-center text-gray-400 text-xs">No cover</div>'
                }
            </div>
            <div class="p-2">
                <h3 class="font-medium text-gray-900 text-sm line-clamp-1">${book.title}</h3>
                ${book.author ? `<p class="text-xs text-gray-600 line-clamp-1">${book.author}</p>` : ''}
            </div>
        </div>
    `;
}

// Search functionality
let currentSearchTimeout = null;
let selectedSearchIndex = -1;

if (searchInput && searchResults) {
    searchInput.addEventListener('keydown', handleSearchKeydown);
    searchInput.addEventListener('input', handleSearchInput);
    searchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `/api/search/books/view?q=${encodeURIComponent(query)}`;
            }
        }
    });
    searchInput.addEventListener('focus', () => {
        if (searchResults.children.length > 0) {
            searchResults.classList.remove('hidden');
        }
    });
}

function handleSearchKeydown(event) {
    const results = searchResults.children;

    switch (event.key) {
        case 'ArrowDown':
            event.preventDefault();
            if (results.length > 0) {
                selectedSearchIndex = Math.min(selectedSearchIndex + 1, results.length - 1);
                updateSearchSelection();
            }
            break;
        case 'ArrowUp':
            event.preventDefault();
            if (results.length > 0) {
                selectedSearchIndex = Math.max(selectedSearchIndex - 1, -1);
                updateSearchSelection();
            }
            break;
        case 'Enter':
            event.preventDefault();
            if (selectedSearchIndex >= 0 && results.length > 0) {
                // If a suggestion is selected, click it
                results[selectedSearchIndex].click();
            } else {
                // If no suggestion is selected, perform a full search
                const query = searchInput.value.trim();
                if (query) {
                    window.location.href = `/api/search/books/view?q=${encodeURIComponent(query)}`;
                }
            }
            break;
        case 'Escape':
            event.preventDefault();
            searchResults.classList.add('hidden');
            selectedSearchIndex = -1;
            updateSearchSelection();
            break;
    }
}

function updateSearchSelection() {
    const results = Array.from(searchResults.children);
    results.forEach((result, index) => {
        if (index === selectedSearchIndex) {
            result.classList.add('bg-indigo-50');
            result.classList.remove('hover:bg-gray-100');
            // Ensure the selected item is visible
            result.scrollIntoView({ block: 'nearest' });
        } else {
            result.classList.remove('bg-indigo-50');
            result.classList.add('hover:bg-gray-100');
        }
    });
}

async function handleSearchInput(event) {
    const query = event.target.value.trim();
    
    // Clear previous timeout
    if (currentSearchTimeout) {
        clearTimeout(currentSearchTimeout);
    }
    
    // Reset selection
    selectedSearchIndex = -1;
    
    if (!query) {
        searchResults.classList.add('hidden');
        searchResults.innerHTML = '';
        return;
    }
    
    // Debounce the search
    currentSearchTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`/api/search/typeahead?q=${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error('Search request failed');
            }
            
            const results = await response.json();
            
            if (results.length === 0) {
                searchResults.classList.add('hidden');
                searchResults.innerHTML = '';
                return;
            }
            
            // Limit to 5 results
            const limitedResults = results.slice(0, 5);
            
            // Update results
            searchResults.innerHTML = limitedResults.map(book => `
                <div class="cursor-pointer py-2 px-4 hover:bg-gray-100 border-b last:border-b-0" 
                     onclick="window.location.href = '/book?id=${book.id}'">
                    <div class="flex items-center">
                        ${book.cover_image_url ? 
                            `<img src="${book.cover_image_url}" alt="${book.title}" class="w-10 h-14 object-cover rounded mr-3">` :
                            `<div class="w-10 h-14 bg-gray-200 rounded mr-3 flex items-center justify-center text-gray-400 text-xs">No cover</div>`
                        }
                        <div>
                            <div class="font-medium text-gray-900">${book.title}</div>
                            ${book.author ? `<div class="text-sm text-gray-500">${book.author}</div>` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
            
            searchResults.classList.remove('hidden');
            updateSearchSelection();
            
        } catch (error) {
            console.error('Search error:', error);
            searchResults.classList.add('hidden');
        }
    }, 300);
}

// Close search results when clicking outside
document.addEventListener('click', (event) => {
    if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
        searchResults.classList.add('hidden');
        selectedSearchIndex = -1;
        updateSearchSelection();
    }
});

// Load popular books
let isLoadingMoreBooks = false;
let currentPage = 1;
let hasMoreBooks = true;

async function loadPopularBooks(appendToExisting = false) {
    if (isLoadingMoreBooks || (!appendToExisting && !hasMoreBooks)) return;
    
    try {
        isLoadingMoreBooks = true;
        const url = `/api/analytics/popular?page=${currentPage}&per_page=12`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Failed to load popular books');
        }
        const books = await response.json();
        
        if (!books.length) {
            hasMoreBooks = false;
            return;
        }
        
        // Get pagination info from the first book
        if (books[0]) {
            hasMoreBooks = books[0]._has_more;
            currentPage = books[0]._page;
        }
        
        const booksHtml = books.map(book => 
            createBookCard(book, `window.location.href = '/book?id=${book.id}'`)
        ).join('');
        
        if (appendToExisting) {
            popularBooks.insertAdjacentHTML('beforeend', booksHtml);
        } else {
            popularBooks.innerHTML = booksHtml;
        }
        
        if (hasMoreBooks) {
            currentPage++;
            
            // Add loading indicator at the bottom
            const loadingHtml = `
                <div id="books-loading" class="w-full text-center py-4">
                    <div class="inline-flex items-center px-4 py-2 text-sm text-sky-500">
                        <svg class="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Loading more books...
                    </div>
                </div>
            `;
            popularBooks.insertAdjacentHTML('beforeend', loadingHtml);
            
            // Remove loading indicator after a short delay
            setTimeout(() => {
                const loader = document.getElementById('books-loading');
                if (loader) loader.remove();
            }, 500);
        }
    } catch (error) {
        console.error('Error loading popular books:', error);
        if (!appendToExisting) {
            popularBooks.innerHTML = '<p class="text-red-600">Error loading popular books</p>';
        }
    } finally {
        isLoadingMoreBooks = false;
    }
}

// Initialize infinite scroll
const observeLastBook = () => {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && hasMoreBooks && !isLoadingMoreBooks) {
                loadPopularBooks(true);
            }
        });
    }, { threshold: 0.1 });
    
    // Update observed element when content changes
    const updateObserver = () => {
        const bookCards = popularBooks.querySelectorAll('.book-card');
        if (bookCards.length > 0) {
            observer.disconnect();
            observer.observe(bookCards[bookCards.length - 1]);
        }
    };
    
    // Watch for DOM changes
    const mutationObserver = new MutationObserver(updateObserver);
    mutationObserver.observe(popularBooks, { childList: true });
    
    // Initial observation
    updateObserver();
};

// Load popular books on page load
if (popularBooks) {
    loadPopularBooks();
    observeLastBook();
}

// Handle book click for popular books
async function handleBookClick(bookId) {
    window.location.href = `/book?id=${bookId}`;
}

// Handle Open Library book click
async function handleOpenLibraryBookClick(openLibraryKey) {
    window.location.href = `/book?key=${openLibraryKey}`;
}

// Show book details
async function showBookDetails(bookId) {
    try {
        // Show loading state
        document.getElementById('book-cover').innerHTML = '<div class="w-full h-full bg-gray-100 animate-pulse"></div>';
        if (document.getElementById('book-button')) document.getElementById('book-button').innerHTML = '';
        document.getElementById('book-summary').innerHTML = `
            <div class="space-y-3">
                <div class="h-4 bg-gray-100 rounded animate-pulse w-3/4"></div>
                <div class="h-4 bg-gray-100 rounded animate-pulse"></div>
                <div class="h-4 bg-gray-100 rounded animate-pulse w-5/6"></div>
            </div>`;
        document.getElementById('book-qa').innerHTML = `
            <div class="space-y-4">
                <div class="border rounded p-3">
                    <div class="h-4 bg-gray-100 rounded animate-pulse w-2/3 mb-2"></div>
                    <div class="space-y-2">
                        <div class="h-3 bg-gray-100 rounded animate-pulse"></div>
                        <div class="h-3 bg-gray-100 rounded animate-pulse w-5/6"></div>
                    </div>
                </div>
            </div>`;
        
        const response = await fetch(`/api/books/${bookId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch book details');
        }

        const book = await response.json();
        
        // Update book details
        document.getElementById('book-title').textContent = book.title;
        document.getElementById('book-author').textContent = book.author || 'Unknown Author';
        
        // Update cover image
        if (book.cover_image_url) {
            document.getElementById('book-cover').innerHTML = `
                <img src="${book.cover_image_url}" 
                     alt="${book.title}" 
                     class="w-full h-full object-contain">`;
        } else {
            document.getElementById('book-cover').innerHTML = `
                <div class="w-full h-full bg-gray-200 flex items-center justify-center text-gray-400">
                    No cover available
                </div>`;
        }
        
        // Update Amazon button if affiliate link exists
        if (book.affiliate_links && book.affiliate_links.amazon) {
            document.getElementById('book-button').innerHTML = `
                <a href="${book.affiliate_links}" 
                   target="_blank" 
                   rel="noopener noreferrer" 
                   class="inline-flex items-center px-4 py-2 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    <img src="/assets/buy-on-amazon-button-png-3-300x111.png" alt="Buy on Amazon" class="h-6">
                </a>`;
        }
        
        // Update summary
        if (book.summary) {
            document.getElementById('book-summary').innerHTML = `<p>${book.summary}</p>`;
        } else {
            document.getElementById('book-summary').innerHTML = '<p class="text-gray-500">No summary available.</p>';
        }
        
        // Update Q&A
        if (book.qa && book.qa.length > 0) {
            document.getElementById('book-qa').innerHTML = book.qa.map(qa => `
                <div class="qa-item bg-gray-50 p-4 rounded-lg">
                    <h5 class="font-medium text-gray-900 mb-2">Q${qa.index + 1}: ${qa.question}</h5>
                    <p class="text-gray-600">${qa.answer}</p>
                </div>
            `).join('');
        } else {
            document.getElementById('book-qa').innerHTML = '<p class="text-gray-500">No Q&A available.</p>';
        }
        
    } catch (error) {
        console.error('Error showing book details:', error);
        document.getElementById('book-title').textContent = 'Error';
        document.getElementById('book-author').textContent = '';
        document.getElementById('book-summary').innerHTML = `
            <div class="text-red-600">
                Failed to load book details. Please try again later.
            </div>`;
        document.getElementById('book-qa').innerHTML = '';
    }
};

// Record a book visit
async function recordVisit(bookId) {
    try {
        const response = await fetch(`/api/analytics/visit/${bookId}`, {
            method: 'POST'
        });
        if (!response.ok) {
            console.error('Failed to record visit:', await response.text());
        }
    } catch (error) {
        console.error('Error recording visit:', error);
    }
}

// Refresh book digest
async function refreshBookDigest() {
    if (!currentBookId) return;
    
    try {
        // Show loading state
        loadingState.classList.remove('hidden');
        refreshButton.disabled = true;
        refreshButton.classList.add('opacity-50', 'cursor-not-allowed');
        
        // Call refresh endpoint
        const response = await fetch(`/api/llm/books/${currentBookId}/refresh`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const errorData = await response.text();
            console.error('Error response:', errorData);
            
            // Check if it's a metadata validation error
            if (response.status === 400 && (errorData.includes('Title mismatch') || errorData.includes('Author mismatch'))) {
                bookSummary.innerHTML = '<p class="text-gray-500 italic">AI is not able to summarize this book.</p>';
                bookQA.innerHTML = '<p class="text-gray-500 italic">No questions and answers available.</p>';
                return;
            }
            
            throw new Error(`Failed to refresh book digest: ${response.status}`);
        }
        
        const book = await response.json();
        console.log('Refreshed book data:', book);
        
        // Update summary and hide refresh button
        bookSummary.innerHTML = book.summary 
            ? `<p>${book.summary}</p>`
            : '<p class="text-gray-500">No summary available.</p>';
            
        // Hide refresh button if summary was generated
        if (book.summary) {
            refreshButton.classList.add('hidden');
        }
        
        // Update Q&A
        if (book.questions_and_answers) {
            try {
                const qa = JSON.parse(book.questions_and_answers);
                bookQA.innerHTML = qa.map((item, index) => `
                    <div class="qa-item bg-gray-50 p-4 rounded-lg">
                        <h5 class="font-medium text-gray-900 mb-2">Q${index + 1}: ${item.question}</h5>
                        <p class="text-gray-600">${item.answer}</p>
                    </div>
                `).join('');
            } catch (e) {
                console.error('Error parsing Q&A:', e);
                bookQA.innerHTML = '<p class="text-gray-500">Error loading questions and answers.</p>';
            }
        } else {
            bookQA.innerHTML = '<p class="text-gray-500">No questions and answers available.</p>';
        }
        
    } catch (error) {
        console.error('Error refreshing book digest:', error);
        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed bottom-4 right-4 bg-red-100 border-l-4 border-red-500 text-red-700 p-4';
        errorDiv.textContent = `Error refreshing book digest: ${error.message}`;
        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    } finally {
        loadingState.classList.add('hidden');
        refreshButton.disabled = false;
        refreshButton.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

// Close modal
function closeModal() {
    bookModal.classList.add('hidden');
    currentBookId = null;
}

// Event listeners
document.addEventListener('click', e => {
    if (!searchResults.contains(e.target) && e.target !== searchInput) {
        searchResults.classList.add('hidden');
    }
});

// Close modal when clicking outside
bookModal.addEventListener('click', (e) => {
    if (e.target === bookModal) {
        closeModal();
    }
});

// Close modal with escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !bookModal.classList.contains('hidden')) {
        closeModal();
    }
});

// Event listeners
if (refreshButton) {
    refreshButton.addEventListener('click', refreshBookDigest);
}

// Handle search form submission
if (searchForm) {
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (query) {
            window.location.href = `/api/search/books/view?q=${encodeURIComponent(query)}`;
        }
    });
}
