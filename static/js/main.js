// DOM Elements
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');
const popularBooks = document.getElementById('popular-books');
const bookModal = document.getElementById('book-modal');
const modalTitle = document.getElementById('modal-title');
const modalAuthor = document.getElementById('modal-author');
const modalContent = document.getElementById('modal-content');
const bookCover = document.getElementById('book-cover');
const bookSummary = document.getElementById('book-summary');
const bookQA = document.getElementById('book-qa');
const loadingState = document.getElementById('loading-state');
const refreshButton = document.getElementById('refresh-button');

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
                    window.location.href = `/search/books?q=${encodeURIComponent(query)}`;
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
async function loadPopularBooks() {
    try {
        const response = await fetch('/analytics/popular');
        if (!response.ok) {
            throw new Error('Failed to load popular books');
        }
        const books = await response.json();
        
        popularBooks.innerHTML = books.map(book => `
            <div class="book-card bg-white rounded shadow-sm overflow-hidden cursor-pointer hover:shadow-md transition-shadow duration-200" 
                 onclick="handleBookClick(${book.id})">
                <div class="h-[180px] bg-white flex items-center justify-center overflow-hidden">
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
        `).join('');
    } catch (error) {
        console.error('Error loading popular books:', error);
    }
}

// Handle book click
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

// Show book details
async function showBookDetails(bookId) {
    try {
        currentBookId = bookId;
        console.log('Fetching book details for ID:', bookId);
        
        // Show loading state
        loadingState.classList.remove('hidden');
        
        // Fetch book data
        const response = await fetch(`/books/${bookId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch book details: ${response.status}`);
        }
        
        const book = await response.json();
        console.log('Book data:', book);
        
        // Update modal content
        modalTitle.textContent = book.title;
        modalAuthor.textContent = `by ${book.author || 'Unknown Author'}`;
        
        // Update book cover
        bookCover.innerHTML = book.cover_image_url 
            ? `<img src="${book.cover_image_url}" alt="${book.title} cover" class="w-full h-full object-cover">` 
            : '<div class="w-full h-full flex items-center justify-center bg-gray-100 text-gray-400">No cover available</div>';
        
        // Update summary
        bookSummary.innerHTML = book.summary 
            ? `<p>${book.summary}</p>`
            : '<p class="text-gray-500">No summary available. Click refresh to generate one.</p>';
        
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
            bookQA.innerHTML = '<p class="text-gray-500">No questions and answers available. Click refresh to generate them.</p>';
        }
        
        // Show modal
        bookModal.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error showing book details:', error);
        // Show error in modal
        modalContent.innerHTML = `
            <div class="text-red-600 p-4">
                Error loading book details: ${error.message}
            </div>
        `;
    } finally {
        loadingState.classList.add('hidden');
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
        const response = await fetch(`/api/llm/books/${currentBookId}/refresh?provider=gemini`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to refresh book digest: ${response.status}`);
        }
        
        const book = await response.json();
        console.log('Refreshed book data:', book);
        
        // Update summary and Q&A sections
        bookSummary.innerHTML = book.summary 
            ? `<p>${book.summary}</p>`
            : '<p class="text-gray-500">No summary available.</p>';
        
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

// Load popular books on page load
loadPopularBooks();

// Event listeners
if (refreshButton) {
    refreshButton.addEventListener('click', refreshBookDigest);
}
