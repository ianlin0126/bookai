// DOM Elements
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');
const popularBooks = document.getElementById('popular-books');
const bookModal = document.getElementById('bookModal');
const modalTitle = document.getElementById('modalTitle');
const modalContent = document.getElementById('modalContent');

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
            
            // Update results
            searchResults.innerHTML = results.map(book => `
                <div class="cursor-pointer p-4 hover:bg-gray-100 border-b last:border-b-0" 
                     onclick="handleBookClick(${book.id})">
                    <div class="flex items-center">
                        ${book.cover_image_url ? 
                            `<img src="${book.cover_image_url}" alt="${book.title}" class="w-12 h-16 object-cover rounded mr-4">` :
                            '<div class="w-12 h-16 bg-gray-200 rounded mr-4"></div>'
                        }
                        <div>
                            <div class="font-medium text-gray-900">${book.title}</div>
                            ${book.author_name ? 
                                `<div class="text-sm text-gray-600">${book.author_name}</div>` : 
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
            <div class="book-card bg-white rounded-lg shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition-shadow duration-200" 
                 onclick="handleBookClick(${book.id})">
                ${book.cover_image_url ? 
                    `<img src="${book.cover_image_url}" alt="${book.title}" class="w-full h-48 object-cover">` :
                    '<div class="w-full h-48 bg-gray-200"></div>'
                }
                <div class="p-4">
                    <h3 class="font-medium text-gray-900">${book.title}</h3>
                    ${book.author_name ? `<p class="text-sm text-gray-600">${book.author_name}</p>` : ''}
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
        const response = await fetch(`/books/open_library/${bookId}`);
        
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
        console.log('Fetching book details for ID:', bookId);
        
        // Fetch data
        const [bookResponse, summaryResponse, qaResponse] = await Promise.all([
            fetch(`/books/${bookId}`),
            fetch(`/books/${bookId}/summary`),
            fetch(`/books/${bookId}/qa`)
        ]);

        // Check responses
        for (const response of [bookResponse, summaryResponse, qaResponse]) {
            if (!response.ok) {
                console.error('Response not OK:', await response.text());
                throw new Error(`API request failed with status ${response.status}`);
            }
        }

        // Parse JSON responses
        let book, summaryData, qaData;
        try {
            [book, summaryData, qaData] = await Promise.all([
                bookResponse.json(),
                summaryResponse.json(),
                qaResponse.json()
            ]);
        } catch (e) {
            console.error('JSON parsing error:', e);
            throw e;
        }

        console.log('Parsed book data:', book);
        console.log('Parsed summary data:', summaryData);
        console.log('Parsed QA data:', qaData);

        // Update modal content
        const modalTitle = document.querySelector('#bookModal .modal-title');
        const modalContent = document.querySelector('#bookModal .modal-content');
        
        if (modalTitle && modalContent) {
            modalTitle.textContent = book.title;
            
            modalContent.innerHTML = `
                <div class="book-details">
                    <div class="book-cover">
                        ${book.cover_image_url ? 
                            `<img src="${book.cover_image_url}" alt="${book.title} cover" class="book-cover-img">` :
                            '<div class="no-cover">No cover available</div>'
                        }
                    </div>
                    <div class="book-info">
                        <h3>${book.title}</h3>
                        <p class="author">by ${book.author_name || 'Unknown Author'}</p>
                        ${book.publication_year ? `<p class="year">Published: ${book.publication_year}</p>` : ''}
                    </div>
                </div>
            `;
        }
        
        // Show modal
        bookModal.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error showing book details:', error);
    }
}

// Close modal
function closeModal() {
    bookModal.classList.add('hidden');
    document.body.style.overflow = ''; // Restore scrolling
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
