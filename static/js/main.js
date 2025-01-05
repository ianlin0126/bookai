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
    searchInput.addEventListener('input', handleSearchInput);
    searchInput.addEventListener('keydown', handleSearchKeydown);
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
                    window.location.href = `/search/books/view?q=${encodeURIComponent(query)}`;
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
            const response = await fetch(`/search/typeahead?q=${encodeURIComponent(query)}`);
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
                     onclick="handleBookClick(${book.id})">
                    <div class="flex items-center">
                        ${book.cover_image_url ? 
                            `<img src="${book.cover_image_url}" alt="${book.title}" class="w-10 h-14 object-cover rounded mr-3">` :
                            '<div class="w-10 h-14 bg-gray-200 rounded mr-3"></div>'
                        }
                        <div class="flex flex-col">
                            <div class="font-medium text-gray-900 text-sm">${book.title}</div>
                            ${book.author ? 
                                `<div class="text-xs text-gray-500">${book.author}</div>` : 
                                ''
                            }
                        </div>
                    </div>
                </div>
            `).join('');
            
            searchResults.classList.remove('hidden');
            
        } catch (error) {
            console.error('Search error:', error);
        }
    }, 300); // 300ms debounce
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
        const url = `/analytics/popular?page=${currentPage}&per_page=12`;
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
            createBookCard(book, `handleBookClick(${book.id})`)
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
    try {
        searchResults.classList.add('hidden');
        
        // First check if book exists in our database
        const response = await fetch(`/books/${bookId}`);
        
        let ourBookId;
        if (response.ok) {
            // Book exists, get its ID
            const book = await response.json();
            ourBookId = book.id;
        } else if (response.status === 404) {
            // Book doesn't exist, create it first
            const createResponse = await fetch(`/books/open_library/${bookId}`, {
                method: 'POST'
            });
            
            if (createResponse.ok) {
                const newBook = await createResponse.json();
                ourBookId = newBook.id;
            } else {
                console.error('Failed to create book:', await createResponse.text());
                return;
            }
        } else {
            console.error('Error checking book:', await response.text());
            return;
        }
        
        // Now show details using our database ID
        await showBookDetails(ourBookId);
    } catch (error) {
        console.error('Error handling book click:', error);
    }
}

// Make the function globally available for onclick handlers
window.handleOpenLibraryBookClick = async function(openLibraryKey) {
    try {
        if (searchResults) {
            searchResults.classList.add('hidden');
        }

        // Show modal and loading state
        bookModal.classList.remove('hidden');
        
        // Clear old content and show loading placeholders
        modalTitle.textContent = '';
        modalAuthor.textContent = '';
        bookCover.innerHTML = '<div class="w-full h-full bg-gray-100 animate-pulse"></div>';
        if (bookButton) bookButton.innerHTML = '';
        bookSummary.innerHTML = `
            <div class="space-y-3">
                <div class="h-4 bg-gray-100 rounded animate-pulse w-3/4"></div>
                <div class="h-4 bg-gray-100 rounded animate-pulse"></div>
                <div class="h-4 bg-gray-100 rounded animate-pulse w-5/6"></div>
            </div>`;
        bookQA.innerHTML = `
            <div class="space-y-4">
                <div class="border rounded p-3">
                    <div class="h-4 bg-gray-100 rounded animate-pulse w-2/3 mb-2"></div>
                    <div class="space-y-2">
                        <div class="h-3 bg-gray-100 rounded animate-pulse"></div>
                        <div class="h-3 bg-gray-100 rounded animate-pulse w-5/6"></div>
                    </div>
                </div>
                <div class="border rounded p-3">
                    <div class="h-4 bg-gray-100 rounded animate-pulse w-2/3 mb-2"></div>
                    <div class="space-y-2">
                        <div class="h-3 bg-gray-100 rounded animate-pulse"></div>
                        <div class="h-3 bg-gray-100 rounded animate-pulse w-5/6"></div>
                    </div>
                </div>
            </div>`;
        
        // First check if book exists in our database
        const response = await fetch(`/books/db/open_library/${openLibraryKey}`);
        
        let book;
        if (response.ok) {            
            // Book exists
            book = await response.json();
            if (!book) {
                // Book not found in our database, create it
                const createResponse = await fetch(`/books/open_library/${openLibraryKey}`, {
                    method: 'POST'
                });
                
                if (createResponse.ok) {
                    book = await createResponse.json();
                } else {
                    console.error('Failed to create book:', await createResponse.text());
                    modalContent.innerHTML = `
                        <div class="text-red-600 p-4">
                            Failed to load book details. Please try again later.
                        </div>`;
                    return;
                }
            }
        } else {
            console.error('Failed to check book:', await response.text());
            modalContent.innerHTML = `
                <div class="text-red-600 p-4">
                    Failed to load book details. Please try again later.
                </div>`;
            return;
        }
        
        // Show book details
        if (book && book.id) {
            await showBookDetails(book.id);
        } else {
            console.error('Invalid book data:', book);
            modalContent.innerHTML = `
                <div class="text-red-600 p-4">
                    Failed to load book details. Please try again later.
                </div>`;
        }
    } catch (error) {
        console.error('Error handling Open Library book click:', error);
        modalContent.innerHTML = `
            <div class="text-red-600 p-4">
                Error loading book details: ${error.message}
            </div>`;
    }
};

// Record a book visit
async function recordVisit(bookId) {
    try {
        const response = await fetch(`/analytics/visit/${bookId}`, {
            method: 'POST'
        });
        if (!response.ok) {
            console.error('Failed to record visit:', await response.text());
        }
    } catch (error) {
        console.error('Error recording visit:', error);
    }
}

// Show book details
async function showBookDetails(bookId) {
    try {
        if (!bookModal) {
            console.error('Modal elements not found');
            return;
        }

        currentBookId = bookId;
        console.log('Fetching book details for ID:', bookId);
        
        // Show loading state
        if (loadingState) loadingState.classList.remove('hidden');
        
        // Record the visit first
        await recordVisit(bookId);
        
        // Fetch book data
        const response = await fetch(`/books/${bookId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch book details: ${response.status}`);
        }
        
        const book = await response.json();
        console.log('Book data:', book);
        
        // Update modal content
        if (modalTitle) modalTitle.textContent = book.title;
        if (modalAuthor) modalAuthor.textContent = `by ${book.author || 'Unknown Author'}`;
        
        // Update book cover and button
        if (bookCover) {
            bookCover.innerHTML = book.cover_image_url 
                ? `<img src="${book.cover_image_url}" alt="${book.title} cover" class="w-full h-full object-cover">` 
                : '<div class="w-full h-full flex items-center justify-center bg-gray-100 text-gray-400">No cover available</div>';
        }
        
        if (bookButton) {
            if (book.affiliate_links) {
                bookButton.innerHTML = `
                    <a href="${book.affiliate_links}" target="_blank" rel="noopener noreferrer" class="inline-block">
                        <img src="/assets/buy-on-amazon-button-png-3-300x111.png" 
                             alt="Buy on Amazon" 
                             class="w-full max-w-[125px] hover:opacity-90 transition-opacity">
                    </a>`;
            } else {
                bookButton.innerHTML = '';
            }
        }
        
        // Update summary and hide refresh button if summary exists
        if (bookSummary) {
            bookSummary.innerHTML = book.summary 
                ? `<p>${book.summary}</p>`
                : '<p class="text-gray-500">No summary available yet.</p>';
        }
            
        // Show refresh button only if no summary exists
        if (refreshButton) {
            if (book.summary) {
                refreshButton.classList.add('hidden');
            } else {
                refreshButton.classList.remove('hidden');
                refreshButton.textContent = 'AI Summarize';
            }
        }
        
        // Update Q&A
        if (bookQA) {
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
                bookQA.innerHTML = '<p class="text-gray-500">No questions and answers available yet.</p>';
            }
        }
        
        // Show modal
        bookModal.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error showing book details:', error);
        // Show error in modal
        if (modalContent) {
            modalContent.innerHTML = `
                <div class="text-red-600 p-4">
                    Error loading book details: ${error.message}
                </div>
            `;
        }
    } finally {
        if (loadingState) loadingState.classList.add('hidden');
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
        const response = await fetch(`/llm/books/${currentBookId}/refresh`, {
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
            window.location.href = `/search/books/view?q=${encodeURIComponent(query)}`;
        }
    });
}
