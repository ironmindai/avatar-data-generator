/**
 * Image Dataset Detail Page - JavaScript
 * Handles Flickr search, URL import, sharing, and image management
 * Adheres to brandbook specifications in docs/brandbook.md
 */

(function() {
  'use strict';

  // ========================================
  // GLOBAL STATE
  // ========================================

  const state = {
    datasetId: null,
    isOwner: false,
    permissionLevel: 'view',
    currentPage: 1,
    totalPages: 1,
    currentFilter: 'all',
    selectedImages: new Set(),
    selectedFlickrResults: new Set(),
    flickrSearch: {
      keyword: '',
      excludeUsed: true,
      licenseFilter: '',
      searchMode: 'tags',
      tagMode: 'any',
      results: [],
      currentPage: 1,
      totalPages: 1,
      hasMore: false,
      isLoadingMore: false
    },
    flickrImport: {
      isImporting: false,
      pollingInterval: null,
      jobId: null
    },
    personDetection: {
      model: null,
      isInitialized: false,
      isProcessing: false,
      processedCount: 0,
      totalCount: 0
    },
    // Face detection removed - now using server-side stored face_count
    monochromeDetection: {
      analyzed: new Set(),
      monochromeImages: new Set()
    }
  };

  const elements = {
    // Dataset info
    datasetId: document.getElementById('datasetId'),
    isOwner: document.getElementById('isOwner'),
    permissionLevel: document.getElementById('permissionLevel'),
    datasetTitle: document.getElementById('datasetTitle'),
    datasetDescription: document.getElementById('datasetDescription'),
    imageCount: document.getElementById('imageCount'),

    // Actions
    addFromFlickrBtn: document.getElementById('addFromFlickrBtn'),
    addFromFlickrBtnEmpty: document.getElementById('addFromFlickrBtnEmpty'),
    importUrlsBtn: document.getElementById('importUrlsBtn'),
    importUrlsBtnEmpty: document.getElementById('importUrlsBtnEmpty'),
    shareBtn: document.getElementById('shareBtn'),
    exportBtn: document.getElementById('exportBtn'),
    exportMenu: document.getElementById('exportMenu'),
    refreshPageBtn: document.getElementById('refreshPageBtn'),
    deleteDatasetBtn: document.getElementById('deleteDatasetBtn'),

    // Filter
    filterBtns: document.querySelectorAll('.filter-btn'),
    imagesGrid: document.getElementById('imagesGrid'),

    // Pagination
    prevPage: document.getElementById('prevPage'),
    nextPage: document.getElementById('nextPage'),

    // Modals
    flickrModal: document.getElementById('flickrModal'),
    urlModal: document.getElementById('urlModal'),
    shareModal: document.getElementById('shareModal'),
    imageModal: document.getElementById('imageModal'),

    // Bulk selection
    selectAllImagesBtn: document.getElementById('selectAllImagesBtn'),
    deselectAllImagesBtn: document.getElementById('deselectAllImagesBtn'),
    selectMonochromeBtn: document.getElementById('selectMonochromeBtn'),
    selectDuplicatesBtn: document.getElementById('selectDuplicatesBtn'),
    tagSearchInput: document.getElementById('tagSearchInput'),
    selectByTagBtn: document.getElementById('selectByTagBtn'),
    faceCountSelect: document.getElementById('faceCountSelect'),
    selectByFaceCountBtn: document.getElementById('selectByFaceCountBtn'),
    bulkDeleteToolbar: document.getElementById('bulkDeleteToolbar'),
    bulkSelectedCount: document.getElementById('bulkSelectedCount'),
    bulkDeleteBtn: document.getElementById('bulkDeleteBtn')
  };

  // ========================================
  // INITIALIZATION
  // ========================================

  document.addEventListener('DOMContentLoaded', function() {
    loadInitialState();
    initializeImageSelection();
    initializeFlickrModal();
    initializeUrlModal();
    initializeShareModal();
    initializeImagePreview();
    initializeSelectionActions();
    initializePagination();
    initializeExportDropdown();
    initializeRefreshButton();
    initializeDeleteDataset();
    initializeInlineEditing();
    initializeFeatherIcons();

    // Check for action query param
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('action') === 'share' && elements.shareBtn) {
      openShareModal();
    }
  });

  function loadInitialState() {
    if (elements.datasetId) state.datasetId = elements.datasetId.value;
    if (elements.isOwner) state.isOwner = elements.isOwner.value === 'True';
    if (elements.permissionLevel) state.permissionLevel = elements.permissionLevel.value;
  }

  // ========================================
  // FLICKR SEARCH MODAL
  // ========================================

  function initializeFlickrModal() {
    if (!elements.flickrModal) return;

    // Open modal
    [elements.addFromFlickrBtn, elements.addFromFlickrBtnEmpty]
      .filter(btn => btn)
      .forEach(btn => {
        btn.addEventListener('click', openFlickrModal);
      });

    // Close modal
    const closeBtn = document.getElementById('flickrModalClose');
    const overlay = document.getElementById('flickrModalOverlay');

    [closeBtn, overlay].filter(el => el).forEach(el => {
      el.addEventListener('click', closeFlickrModal);
    });

    // Search form
    const searchForm = document.getElementById('flickrSearchForm');
    if (searchForm) {
      searchForm.addEventListener('submit', handleFlickrSearch);
    }

    // Search mode toggle - show/hide tag mode options
    const searchModeRadios = document.querySelectorAll('input[name="search_mode"]');
    const tagModeGroup = document.getElementById('tagModeGroup');
    const keywordInput = document.getElementById('flickrKeyword');

    searchModeRadios.forEach(radio => {
      radio.addEventListener('change', (e) => {
        if (tagModeGroup) {
          tagModeGroup.style.display = e.target.value === 'tags' ? 'block' : 'none';
        }
        // Update placeholder based on search mode
        if (keywordInput) {
          if (e.target.value === 'tags') {
            keywordInput.placeholder = 'e.g., portrait, landscape, nature';
          } else {
            keywordInput.placeholder = 'e.g., woman smiling, city skyline, sunset beach';
          }
        }
      });
    });

    // Select all/none buttons
    const selectAllBtn = document.getElementById('selectAllBtn');
    const selectNoneBtn = document.getElementById('selectNoneBtn');
    const selectAllWithFacesBtn = document.getElementById('selectAllWithFacesBtn');
    const selectNoneWithFacesBtn = document.getElementById('selectNoneWithFacesBtn');

    if (selectAllBtn) {
      selectAllBtn.addEventListener('click', selectAllFlickrResults);
    }

    if (selectNoneBtn) {
      selectNoneBtn.addEventListener('click', deselectAllFlickrResults);
    }

    if (selectAllWithFacesBtn) {
      selectAllWithFacesBtn.addEventListener('click', selectAllFlickrResultsWithFaces);
    }

    if (selectNoneWithFacesBtn) {
      selectNoneWithFacesBtn.addEventListener('click', deselectAllFlickrResultsWithFaces);
    }

    // Detect People button
    const detectPeopleBtn = document.getElementById('detectPeopleBtn');
    if (detectPeopleBtn) {
      detectPeopleBtn.addEventListener('click', handleDetectPeople);
    }

    // Import selected button
    const importSelectedBtn = document.getElementById('importSelectedBtn');
    if (importSelectedBtn) {
      importSelectedBtn.addEventListener('click', handleFlickrImport);
    }

    // Load More button
    const loadMoreBtn = document.getElementById('flickrLoadMoreBtn');
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener('click', loadMoreFlickrResults);
    }

    // Escape key to close
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && elements.flickrModal.classList.contains('active')) {
        closeFlickrModal();
      }
    });
  }

  function openFlickrModal() {
    elements.flickrModal.classList.add('active');
    elements.flickrModal.setAttribute('aria-hidden', 'false');

    // Focus on keyword input
    const keywordInput = document.getElementById('flickrKeyword');
    if (keywordInput) {
      setTimeout(() => keywordInput.focus(), 100);
    }
  }

  function closeFlickrModal() {
    elements.flickrModal.classList.remove('active');
    elements.flickrModal.setAttribute('aria-hidden', 'true');

    // Clear import polling if active
    if (state.flickrImport.pollingInterval) {
      clearInterval(state.flickrImport.pollingInterval);
      state.flickrImport.pollingInterval = null;
    }

    // Reset search
    const searchForm = document.getElementById('flickrSearchForm');
    const results = document.getElementById('flickrResults');
    const loadMoreContainer = document.getElementById('flickrLoadMoreContainer');

    if (searchForm) searchForm.reset();
    if (results) results.style.display = 'none';
    if (loadMoreContainer) loadMoreContainer.style.display = 'none';

    // Reset state
    state.selectedFlickrResults.clear();
    state.flickrSearch = {
      keyword: '',
      excludeUsed: true,
      licenseFilter: '',
      searchMode: 'tags',
      tagMode: 'any',
      results: [],
      currentPage: 1,
      totalPages: 1,
      hasMore: false,
      isLoadingMore: false
    };
    state.flickrImport = {
      isImporting: false,
      pollingInterval: null,
      jobId: null
    };
  }

  async function handleFlickrSearch(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const keyword = formData.get('keyword').trim();
    const excludeUsed = formData.get('exclude_used') === 'on';
    const licenseFilter = formData.get('license_filter') || '';
    const searchMode = formData.get('search_mode') || 'tags';
    const tagMode = formData.get('tag_mode') || 'any';

    if (!keyword) {
      showToast('Please enter a keyword', 'error');
      return;
    }

    // Reset state for new search
    state.flickrSearch.keyword = keyword;
    state.flickrSearch.excludeUsed = excludeUsed;
    state.flickrSearch.licenseFilter = licenseFilter;
    state.flickrSearch.searchMode = searchMode;
    state.flickrSearch.tagMode = tagMode;
    state.flickrSearch.currentPage = 1;
    state.flickrSearch.results = [];
    state.selectedFlickrResults.clear();

    // Clear results grid
    const resultsGrid = document.getElementById('flickrResultsGrid');
    if (resultsGrid) resultsGrid.innerHTML = '';

    // Perform search
    await performFlickrSearch(false);
  }

  async function performFlickrSearch(appendResults = false) {
    const { keyword, excludeUsed, licenseFilter, searchMode, tagMode, currentPage } = state.flickrSearch;

    // Show loading
    const loading = document.getElementById('flickrLoading');
    const results = document.getElementById('flickrResults');

    if (!appendResults) {
      loading.style.display = 'flex';
      results.style.display = 'none';
    }

    // Get CSRF token
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

    try {
      const response = await fetch(`/api/image-datasets/${state.datasetId}/search-flickr`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          keyword,
          exclude_used: excludeUsed,
          license_filter: licenseFilter,
          search_mode: searchMode,
          tag_mode: tagMode,
          page: currentPage
        })
      });

      const result = await response.json();

      loading.style.display = 'none';

      if (response.ok && result.success) {
        const photos = result.photos || [];

        // Update state
        state.flickrSearch.totalPages = result.pages || 1;
        state.flickrSearch.hasMore = currentPage < (result.pages || 1);

        if (appendResults) {
          // Append new results to existing
          state.flickrSearch.results = [...state.flickrSearch.results, ...photos];
          appendFlickrResults(photos);
        } else {
          // Replace results
          state.flickrSearch.results = photos;
          displayFlickrResults(photos);
        }

        // Update Load More button visibility
        updateLoadMoreButton();
      } else {
        showToast(result.message || 'Failed to search Flickr', 'error');
      }
    } catch (error) {
      console.error('Error searching Flickr:', error);
      loading.style.display = 'none';
      showToast('An error occurred while searching Flickr', 'error');
    }
  }

  function displayFlickrResults(photos) {
    const resultsGrid = document.getElementById('flickrResultsGrid');
    const results = document.getElementById('flickrResults');

    if (!photos || photos.length === 0) {
      showToast('No photos found matching your criteria', 'error');
      return;
    }

    resultsGrid.innerHTML = '';

    photos.forEach((photo, index) => {
      createFlickrResultItem(photo, index, resultsGrid);
    });

    results.style.display = 'block';
    updateSelectedCount();
    feather.replace();

    // Show the "Detect People" button when results are displayed
    showDetectPeopleButton();
  }

  function appendFlickrResults(photos) {
    const resultsGrid = document.getElementById('flickrResultsGrid');
    if (!resultsGrid) return;

    const startIndex = state.flickrSearch.results.length - photos.length;

    photos.forEach((photo, index) => {
      createFlickrResultItem(photo, startIndex + index, resultsGrid);
    });

    updateSelectedCount();
    feather.replace();

    // Show the "Detect People" button after appending new results
    showDetectPeopleButton();
  }

  function createFlickrResultItem(photo, index, container) {
    const resultItem = document.createElement('div');
    resultItem.className = 'result-item';

    // Store full photo data in the DOM for later use during import
    resultItem.dataset.photo = JSON.stringify(photo);

    // Build tags HTML if available
    let tagsHtml = '';
    if (photo.tags && photo.tags.length > 0) {
      const displayTags = photo.tags.slice(0, 3);
      tagsHtml = `
        <div class="result-tags">
          ${displayTags.map(tag => `<span class="tag-badge">${tag}</span>`).join('')}
          ${photo.tags.length > 3 ? `<span class="tag-badge">+${photo.tags.length - 3}</span>` : ''}
        </div>
      `;
    }

    // Build license HTML if available
    let licenseHtml = '';
    if (photo.license) {
      licenseHtml = `<div class="license-badge">${photo.license}</div>`;
    }

    resultItem.innerHTML = `
      <input type="checkbox"
             class="result-checkbox"
             data-photo-id="${photo.id}"
             data-photo-url="${photo.url}"
             id="photo-${index}">
      <div class="result-image-wrapper">
        <img src="${photo.url}"
             alt="${photo.title || 'Flickr photo'}"
             class="result-image"
             loading="lazy">
      </div>
      <div class="result-info">
        ${photo.title ? `<div class="result-title">${photo.title.substring(0, 40)}${photo.title.length > 40 ? '...' : ''}</div>` : ''}
        ${tagsHtml}
        ${licenseHtml}
      </div>
    `;

    const checkbox = resultItem.querySelector('.result-checkbox');
    const imageWrapper = resultItem.querySelector('.result-image-wrapper');

    // Toggle selection function
    const toggleSelection = (fromCheckbox = false) => {
      // If click came from checkbox directly, let it handle naturally
      if (fromCheckbox) {
        if (checkbox.checked) {
          state.selectedFlickrResults.add(photo.id);
          resultItem.classList.add('selected');
        } else {
          state.selectedFlickrResults.delete(photo.id);
          resultItem.classList.remove('selected');
        }
      } else {
        // Click came from image/wrapper, toggle checkbox programmatically
        checkbox.checked = !checkbox.checked;
        if (checkbox.checked) {
          state.selectedFlickrResults.add(photo.id);
          resultItem.classList.add('selected');
        } else {
          state.selectedFlickrResults.delete(photo.id);
          resultItem.classList.remove('selected');
        }
      }
      updateSelectedCount();
    };

    // Checkbox change handler
    checkbox.addEventListener('change', function() {
      toggleSelection(true);
    });

    // Make image wrapper clickable
    imageWrapper.addEventListener('click', function(e) {
      // Prevent triggering if clicking on the checkbox itself
      if (e.target === checkbox) return;
      toggleSelection(false);
    });

    container.appendChild(resultItem);
  }

  // ========================================
  // PERSON DETECTION FUNCTIONALITY
  // ========================================

  /**
   * Initialize TensorFlow.js COCO-SSD model for person detection
   * Lazy initialization - only loads when first needed
   */
  async function initializePersonDetection() {
    if (state.personDetection.isInitialized) return true;

    try {
      // Check if TensorFlow.js and COCO-SSD are loaded
      if (typeof cocoSsd === 'undefined') {
        console.error('COCO-SSD library not loaded');
        return false;
      }

      // Load the COCO-SSD model
      state.personDetection.model = await cocoSsd.load();
      state.personDetection.isInitialized = true;
      return true;
    } catch (error) {
      console.error('Failed to initialize person detection:', error);
      return false;
    }
  }

  /**
   * Detect people in a single image using COCO-SSD
   * Returns the number of people detected
   * Uses proxy endpoint to avoid CORS issues with Flickr images
   */
  async function detectPeopleInImage(imageUrl) {
    if (!state.personDetection.isInitialized) {
      await initializePersonDetection();
    }

    if (!state.personDetection.model) return 0;

    try {
      // Create proxied URL to avoid CORS issues
      const proxyUrl = `/api/proxy-image?url=${encodeURIComponent(imageUrl)}`;

      // Create new image element with proxy URL
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.src = proxyUrl;

      // Wait for image to load
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = () => reject(new Error('Failed to load image'));
      });

      // Detect objects in the image
      const predictions = await state.personDetection.model.detect(img);

      // Count only 'person' class detections
      const personCount = predictions.filter(p => p.class === 'person').length;
      return personCount;
    } catch (error) {
      console.error('Error detecting people:', error);
      return 0;
    }
  }

  /**
   * Process person detection for all Flickr results in batches
   */
  async function detectPeopleInFlickrResults() {
    // Prevent multiple simultaneous detection runs
    if (state.personDetection.isProcessing) return;

    state.personDetection.isProcessing = true;

    // Show detection status
    const statusElement = document.getElementById('faceDetectionStatus');
    const statusText = document.getElementById('faceDetectionStatusText');
    if (statusElement) {
      statusElement.style.display = 'flex';
      feather.replace();
    }

    try {
      // Initialize person detection
      const personInitialized = await initializePersonDetection();

      if (!personInitialized) {
        if (statusElement) statusElement.style.display = 'none';
        state.personDetection.isProcessing = false;
        return;
      }

      // Get all result items that don't have person count yet
      const resultsGrid = document.getElementById('flickrResultsGrid');
      if (!resultsGrid) {
        state.personDetection.isProcessing = false;
        return;
      }

      const resultItems = Array.from(resultsGrid.querySelectorAll('.result-item'));
      const itemsToProcess = resultItems.filter(item => {
        const photoData = JSON.parse(item.dataset.photo);
        return photoData.personCount === undefined;
      });

      if (itemsToProcess.length === 0) {
        if (statusElement) statusElement.style.display = 'none';
        state.personDetection.isProcessing = false;
        return;
      }

      state.personDetection.totalCount = itemsToProcess.length;
      state.personDetection.processedCount = 0;

      // Process images in batches of 8-10 for performance
      const BATCH_SIZE = 10;

      for (let i = 0; i < itemsToProcess.length; i += BATCH_SIZE) {
        const batch = itemsToProcess.slice(i, i + BATCH_SIZE);

        // Process batch in parallel
        await Promise.all(batch.map(async (item) => {
          const photoData = JSON.parse(item.dataset.photo);

          // Detect people in the image
          const personCount = await detectPeopleInImage(photoData.url);

          // Update photo data with person count
          photoData.personCount = personCount;
          item.dataset.photo = JSON.stringify(photoData);

          // Update the photo in state
          const photoInState = state.flickrSearch.results.find(p => p.id === photoData.id);
          if (photoInState) {
            photoInState.personCount = personCount;
          }

          // Add badge if people detected
          if (personCount > 0) {
            addDetectionBadge(item, personCount);
          }

          // Update progress
          state.personDetection.processedCount++;
          if (statusText) {
            statusText.textContent = `Detecting people in ${state.personDetection.processedCount}/${state.personDetection.totalCount} images...`;
          }
        }));
      }

      // Hide status after completion
      if (statusElement) {
        statusElement.style.display = 'none';
      }

    } catch (error) {
      console.error('Error in person detection process:', error);
      if (statusElement) statusElement.style.display = 'none';
    } finally {
      state.personDetection.isProcessing = false;
    }
  }

  /**
   * Add detection badge to result item as green dot indicator
   */
  function addDetectionBadge(resultItem, personCount) {
    const imageWrapper = resultItem.querySelector('.result-image-wrapper');
    if (!imageWrapper) return;

    // Check if badge already exists
    if (imageWrapper.querySelector('.face-count-badge')) return;

    const badge = document.createElement('div');
    badge.className = 'face-count-badge';
    // No text content - just a visual indicator dot
    badge.setAttribute('data-tooltip', `${personCount} person${personCount !== 1 ? 's' : ''} detected`);

    imageWrapper.appendChild(badge);
  }

  /**
   * Show the "Detect People" button when results are available
   */
  function showDetectPeopleButton() {
    const detectPeopleBtn = document.getElementById('detectPeopleBtn');
    if (!detectPeopleBtn) return;

    // Show the button
    detectPeopleBtn.style.display = 'inline-flex';
    detectPeopleBtn.disabled = false;

    // Update button state based on whether detection has already run
    const resultsGrid = document.getElementById('flickrResultsGrid');
    if (resultsGrid) {
      const resultItems = Array.from(resultsGrid.querySelectorAll('.result-item'));
      const itemsNeedingDetection = resultItems.filter(item => {
        const photoData = JSON.parse(item.dataset.photo);
        return photoData.personCount === undefined;
      });

      if (itemsNeedingDetection.length === 0 && resultItems.length > 0) {
        // All items have been detected - hide button or change text
        detectPeopleBtn.querySelector('span').textContent = 'Re-detect People';
      } else {
        detectPeopleBtn.querySelector('span').textContent = 'Detect People';
      }
    }

    feather.replace();
  }

  /**
   * Handle manual person detection trigger
   */
  async function handleDetectPeople() {
    const detectPeopleBtn = document.getElementById('detectPeopleBtn');
    const selectAllWithFacesBtn = document.getElementById('selectAllWithFacesBtn');
    const selectNoneWithFacesBtn = document.getElementById('selectNoneWithFacesBtn');

    if (!detectPeopleBtn) return;

    // Disable button and show loading state
    detectPeopleBtn.disabled = true;
    const buttonText = detectPeopleBtn.querySelector('span');
    const originalText = buttonText.textContent;
    buttonText.textContent = 'Detecting...';

    try {
      // Run person detection
      await detectPeopleInFlickrResults();

      // Enable the "with People" selection buttons after detection
      if (selectAllWithFacesBtn) {
        selectAllWithFacesBtn.disabled = false;
        selectAllWithFacesBtn.removeAttribute('title');
      }
      if (selectNoneWithFacesBtn) {
        selectNoneWithFacesBtn.disabled = false;
        selectNoneWithFacesBtn.removeAttribute('title');
      }

      // Update button text to "Re-detect People"
      buttonText.textContent = 'Re-detect People';
      detectPeopleBtn.disabled = false;

    } catch (error) {
      console.error('Error during person detection:', error);
      buttonText.textContent = originalText;
      detectPeopleBtn.disabled = false;
      showToast('Person detection failed. Please try again.', 'error');
    }
  }

  /**
   * Select all Flickr results that have people
   */
  function selectAllFlickrResultsWithFaces() {
    state.flickrSearch.results.forEach((photo) => {
      const hasPeople = photo.personCount && photo.personCount > 0;

      if (hasPeople) {
        state.selectedFlickrResults.add(photo.id);

        // Update UI
        const checkbox = document.querySelector(`input[data-photo-id="${photo.id}"]`);
        if (checkbox) {
          checkbox.checked = true;
          const resultItem = checkbox.closest('.result-item');
          if (resultItem) {
            resultItem.classList.add('selected');
          }
        }
      }
    });

    updateSelectedCount();
  }

  /**
   * Deselect all Flickr results that have people
   */
  function deselectAllFlickrResultsWithFaces() {
    state.flickrSearch.results.forEach((photo) => {
      const hasPeople = photo.personCount && photo.personCount > 0;

      if (hasPeople) {
        state.selectedFlickrResults.delete(photo.id);

        // Update UI
        const checkbox = document.querySelector(`input[data-photo-id="${photo.id}"]`);
        if (checkbox) {
          checkbox.checked = false;
          const resultItem = checkbox.closest('.result-item');
          if (resultItem) {
            resultItem.classList.remove('selected');
          }
        }
      }
    });

    updateSelectedCount();
  }

  async function loadMoreFlickrResults() {
    if (state.flickrSearch.isLoadingMore || !state.flickrSearch.hasMore) return;

    // Set loading state
    state.flickrSearch.isLoadingMore = true;
    state.flickrSearch.currentPage += 1;

    // Update button to show loading state
    const loadMoreBtn = document.getElementById('flickrLoadMoreBtn');
    if (loadMoreBtn) {
      loadMoreBtn.disabled = true;
      loadMoreBtn.innerHTML = `
        <i data-feather="loader" class="spin-animation"></i>
        Loading...
      `;
      feather.replace();
    }

    try {
      await performFlickrSearch(true);
    } catch (error) {
      console.error('Error loading more results:', error);
      showToast('Failed to load more results', 'error');
      // Revert page increment on error
      state.flickrSearch.currentPage -= 1;
    } finally {
      state.flickrSearch.isLoadingMore = false;
      updateLoadMoreButton();
    }
  }

  function updateLoadMoreButton() {
    const loadMoreContainer = document.getElementById('flickrLoadMoreContainer');
    const loadMoreBtn = document.getElementById('flickrLoadMoreBtn');

    if (!loadMoreContainer || !loadMoreBtn) return;

    const { currentPage, totalPages, hasMore, isLoadingMore } = state.flickrSearch;

    if (hasMore) {
      loadMoreContainer.style.display = 'block';
      loadMoreBtn.disabled = isLoadingMore;
      loadMoreBtn.innerHTML = `
        <i data-feather="chevron-down"></i>
        Load More Results
        <span class="page-info">(Page ${currentPage} of ${totalPages})</span>
      `;
      feather.replace();
    } else {
      loadMoreContainer.style.display = 'none';
    }
  }

  function selectAllFlickrResults() {
    const checkboxes = document.querySelectorAll('.result-checkbox');
    checkboxes.forEach(checkbox => {
      checkbox.checked = true;
      checkbox.dispatchEvent(new Event('change'));
    });
  }

  function deselectAllFlickrResults() {
    const checkboxes = document.querySelectorAll('.result-checkbox');
    checkboxes.forEach(checkbox => {
      checkbox.checked = false;
      checkbox.dispatchEvent(new Event('change'));
    });
  }

  function updateSelectedCount() {
    const selectedCount = document.getElementById('selectedCount');
    const importBtn = document.getElementById('importSelectedBtn');

    if (selectedCount) {
      selectedCount.textContent = state.selectedFlickrResults.size;
    }

    if (importBtn) {
      importBtn.disabled = state.selectedFlickrResults.size === 0;
    }
  }

  async function handleFlickrImport() {
    if (state.selectedFlickrResults.size === 0) return;
    if (state.flickrImport.isImporting) return; // Prevent multiple imports

    const selectedPhotoIds = Array.from(state.selectedFlickrResults);
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

    // Gather full photo data for selected photos
    const selectedPhotos = selectedPhotoIds.map(photoId => {
      const checkbox = document.querySelector(`input[data-photo-id="${photoId}"]`);
      const photoCard = checkbox?.closest('.result-item');
      const photoDataStr = photoCard?.dataset.photo;

      if (photoDataStr) {
        try {
          return JSON.parse(photoDataStr);
        } catch (e) {
          console.error(`Failed to parse photo data for ${photoId}:`, e);
          return { id: photoId }; // Fallback to just ID
        }
      }
      return { id: photoId }; // Fallback if data not found
    });

    // Disable button and show initial state
    const importBtn = document.getElementById('importSelectedBtn');
    importBtn.disabled = true;
    const originalText = importBtn.innerHTML;
    importBtn.innerHTML = '<i data-feather="loader"></i> Starting import...';
    feather.replace();

    state.flickrImport.isImporting = true;

    try {
      // Start the import job
      const response = await fetch(`/api/image-datasets/${state.datasetId}/import-flickr`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          photos: selectedPhotos
        })
      });

      const result = await response.json();

      if (response.ok && result.success && result.job_id) {
        // Store job ID and start polling
        state.flickrImport.jobId = result.job_id;
        startImportProgressPolling(importBtn, originalText);
      } else {
        // Handle immediate error (job didn't start)
        showToast(result.message || 'Failed to start import', 'error');
        resetImportButton(importBtn, originalText);
      }
    } catch (error) {
      console.error('Error starting Flickr import:', error);
      showToast('An error occurred while starting import', 'error');
      resetImportButton(importBtn, originalText);
    }
  }

  function startImportProgressPolling(importBtn, originalText) {
    // Poll every 1.5 seconds
    state.flickrImport.pollingInterval = setInterval(async () => {
      try {
        await pollImportProgress(importBtn, originalText);
      } catch (error) {
        console.error('Error polling import progress:', error);
        // Continue polling despite errors (backend might be temporarily busy)
      }
    }, 1500);

    // Also poll immediately
    pollImportProgress(importBtn, originalText);
  }

  async function pollImportProgress(importBtn, originalText) {
    if (!state.flickrImport.jobId) return;

    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

    try {
      const response = await fetch(
        `/api/image-datasets/${state.datasetId}/import-flickr/${state.flickrImport.jobId}/progress`,
        {
          method: 'GET',
          headers: {
            'X-CSRFToken': csrfToken
          }
        }
      );

      const progress = await response.json();

      if (!response.ok) {
        throw new Error(progress.message || 'Failed to get progress');
      }

      // Update button text with progress
      updateImportButtonProgress(importBtn, progress);

      // Check if completed or failed
      if (progress.status === 'completed') {
        handleImportComplete(importBtn, originalText, progress);
      } else if (progress.status === 'failed') {
        handleImportFailed(importBtn, originalText, progress);
      }
    } catch (error) {
      console.error('Error fetching import progress:', error);
      // Don't stop polling on network errors - backend might recover
    }
  }

  function updateImportButtonProgress(importBtn, progress) {
    const { current, total, imported, failed } = progress;

    let progressText = '';
    if (total && total > 0) {
      progressText = `Importing... ${current}/${total}`;
      if (imported !== undefined || failed !== undefined) {
        const parts = [];
        if (imported > 0) parts.push(`${imported} imported`);
        if (failed > 0) parts.push(`${failed} failed`);
        if (parts.length > 0) {
          progressText += ` (${parts.join(', ')})`;
        }
      }
    } else {
      progressText = 'Importing...';
    }

    importBtn.innerHTML = `<i data-feather="loader"></i> ${progressText}`;
    feather.replace();
  }

  function handleImportComplete(importBtn, originalText, progress) {
    // Stop polling
    if (state.flickrImport.pollingInterval) {
      clearInterval(state.flickrImport.pollingInterval);
      state.flickrImport.pollingInterval = null;
    }

    const importedCount = progress.imported || 0;
    const failedCount = progress.failed || 0;

    // Show success message
    let message = `Successfully imported ${importedCount} image${importedCount !== 1 ? 's' : ''}`;
    if (failedCount > 0) {
      message += `. ${failedCount} failed`;
    }
    showToast(message, 'success');

    // Close modal and reload
    closeFlickrModal();
    setTimeout(() => window.location.reload(), 500);
  }

  function handleImportFailed(importBtn, originalText, progress) {
    // Stop polling
    if (state.flickrImport.pollingInterval) {
      clearInterval(state.flickrImport.pollingInterval);
      state.flickrImport.pollingInterval = null;
    }

    const errorMessage = progress.error || 'Import failed';
    showToast(errorMessage, 'error');
    resetImportButton(importBtn, originalText);
  }

  function resetImportButton(importBtn, originalText) {
    state.flickrImport.isImporting = false;
    state.flickrImport.jobId = null;
    importBtn.disabled = false;
    importBtn.innerHTML = originalText;
    feather.replace();
  }

  // ========================================
  // URL IMPORT MODAL
  // ========================================

  function initializeUrlModal() {
    if (!elements.urlModal) return;

    // Open modal
    [elements.importUrlsBtn, elements.importUrlsBtnEmpty]
      .filter(btn => btn)
      .forEach(btn => {
        btn.addEventListener('click', openUrlModal);
      });

    // Close modal
    const closeBtn = document.getElementById('urlModalClose');
    const overlay = document.getElementById('urlModalOverlay');

    [closeBtn, overlay].filter(el => el).forEach(el => {
      el.addEventListener('click', closeUrlModal);
    });

    // URL validation
    const urlList = document.getElementById('urlList');
    if (urlList) {
      urlList.addEventListener('input', validateUrls);
    }

    // Import form
    const importForm = document.getElementById('urlImportForm');
    if (importForm) {
      importForm.addEventListener('submit', handleUrlImport);
    }

    // Escape key to close
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && elements.urlModal.classList.contains('active')) {
        closeUrlModal();
      }
    });
  }

  function openUrlModal() {
    elements.urlModal.classList.add('active');
    elements.urlModal.setAttribute('aria-hidden', 'false');

    // Focus on URL textarea
    const urlList = document.getElementById('urlList');
    if (urlList) {
      setTimeout(() => urlList.focus(), 100);
    }
  }

  function closeUrlModal() {
    elements.urlModal.classList.remove('active');
    elements.urlModal.setAttribute('aria-hidden', 'true');

    // Reset form
    const importForm = document.getElementById('urlImportForm');
    const urlPreview = document.getElementById('urlPreview');
    const importProgress = document.getElementById('urlImportProgress');

    if (importForm) importForm.reset();
    if (urlPreview) urlPreview.style.display = 'none';
    if (importProgress) importProgress.style.display = 'none';
  }

  function validateUrls() {
    const urlList = document.getElementById('urlList');
    const validUrlCount = document.getElementById('validUrlCount');
    const urlPreview = document.getElementById('urlPreview');
    const urlPreviewList = document.getElementById('urlPreviewList');

    if (!urlList) return;

    const urls = urlList.value
      .split('\n')
      .map(url => url.trim())
      .filter(url => url.length > 0);

    // Validate URLs
    const validUrls = urls.filter(url => {
      try {
        const urlObj = new URL(url);
        return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
      } catch {
        return false;
      }
    });

    // Update count
    if (validUrlCount) {
      validUrlCount.textContent = validUrls.length;
    }

    // Update preview
    if (validUrls.length > 0 && urlPreview && urlPreviewList) {
      urlPreviewList.innerHTML = validUrls
        .slice(0, 10)
        .map(url => `<div class="preview-url">${url}</div>`)
        .join('');

      if (validUrls.length > 10) {
        urlPreviewList.innerHTML += `<div class="preview-url text-muted">... and ${validUrls.length - 10} more</div>`;
      }

      urlPreview.style.display = 'block';
    } else if (urlPreview) {
      urlPreview.style.display = 'none';
    }
  }

  async function handleUrlImport(e) {
    e.preventDefault();

    const urlList = document.getElementById('urlList');
    if (!urlList) return;

    const urls = urlList.value
      .split('\n')
      .map(url => url.trim())
      .filter(url => url.length > 0);

    // Validate URLs
    const validUrls = urls.filter(url => {
      try {
        const urlObj = new URL(url);
        return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
      } catch {
        return false;
      }
    });

    if (validUrls.length === 0) {
      showToast('Please enter at least one valid URL', 'error');
      return;
    }

    // Show progress
    const importForm = document.getElementById('urlImportForm');
    const importProgress = document.getElementById('urlImportProgress');
    const progressBar = document.getElementById('urlProgressBar');
    const progressCurrent = document.getElementById('urlProgressCurrent');
    const progressTotal = document.getElementById('urlProgressTotal');
    const submitBtn = document.getElementById('importUrlsSubmitBtn');

    importForm.style.display = 'none';
    importProgress.style.display = 'block';

    if (progressTotal) progressTotal.textContent = validUrls.length;
    if (progressCurrent) progressCurrent.textContent = '0';
    if (progressBar) progressBar.style.width = '0%';

    // Get CSRF token
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

    try {
      const response = await fetch(`/api/image-datasets/${state.datasetId}/import-urls`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ urls: validUrls })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        if (progressBar) progressBar.style.width = '100%';
        if (progressCurrent) progressCurrent.textContent = result.imported_count;

        // Check if any images were actually imported
        if (result.imported_count > 0) {
          showToast(`Successfully imported ${result.imported_count} image(s)`, 'success');
          closeUrlModal();

          // Reload page to show new images
          setTimeout(() => window.location.reload(), 500);
        } else if (result.failed_count > 0 && result.failed_urls && result.failed_urls.length > 0) {
          // All URLs failed - show detailed error messages
          let errorMsg = `Failed to import ${result.failed_count} URL(s): `;
          const firstError = result.failed_urls[0];
          errorMsg += firstError.error;
          if (result.failed_urls.length > 1) {
            errorMsg += ` (and ${result.failed_urls.length - 1} more)`;
          }

          showToast(errorMsg, 'error');
          importForm.style.display = 'block';
          importProgress.style.display = 'none';
        } else {
          // Shouldn't happen, but handle it
          showToast('No images were imported. Please check your URLs.', 'error');
          importForm.style.display = 'block';
          importProgress.style.display = 'none';
        }
      } else {
        showToast(result.message || 'Failed to import URLs', 'error');
        importForm.style.display = 'block';
        importProgress.style.display = 'none';
      }
    } catch (error) {
      console.error('Error importing URLs:', error);
      showToast('An error occurred while importing URLs', 'error');
      importForm.style.display = 'block';
      importProgress.style.display = 'none';
    }
  }

  // ========================================
  // SHARE MODAL (Placeholder - Backend Required)
  // ========================================

  function initializeShareModal() {
    if (!elements.shareModal || !elements.shareBtn) return;

    elements.shareBtn.addEventListener('click', openShareModal);

    const closeBtn = document.getElementById('shareModalClose');
    const overlay = document.getElementById('shareModalOverlay');

    [closeBtn, overlay].filter(el => el).forEach(el => {
      el.addEventListener('click', closeShareModal);
    });

    // Grant access form
    const grantForm = document.getElementById('grantAccessForm');
    if (grantForm) {
      grantForm.addEventListener('submit', handleGrantAccess);
    }

    // Escape key to close
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && elements.shareModal.classList.contains('active')) {
        closeShareModal();
      }
    });

    // Load current users
    loadSharedUsers();
  }

  function openShareModal() {
    if (!elements.shareModal) return;
    elements.shareModal.classList.add('active');
    elements.shareModal.setAttribute('aria-hidden', 'false');
  }

  function closeShareModal() {
    if (!elements.shareModal) return;
    elements.shareModal.classList.remove('active');
    elements.shareModal.setAttribute('aria-hidden', 'true');
  }

  async function loadSharedUsers() {
    const sharedUsersList = document.getElementById('shareUsersList');
    if (!sharedUsersList) return;

    // Show loading state
    sharedUsersList.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: var(--color-text-secondary);">
        <i data-feather="loader" style="animation: spin 1s linear infinite;"></i>
        <p>Loading shared users...</p>
      </div>
    `;
    feather.replace();

    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

    try {
      const response = await fetch(`/api/image-datasets/${state.datasetId}/permissions`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        }
      });

      const result = await response.json();

      if (response.ok && result.success) {
        displaySharedUsers(result.permissions || []);
      } else {
        sharedUsersList.innerHTML = `
          <div class="empty-state-small">
            <i data-feather="alert-circle"></i>
            <p>${result.message || 'Failed to load shared users'}</p>
          </div>
        `;
        feather.replace();
      }
    } catch (error) {
      console.error('Error loading shared users:', error);
      sharedUsersList.innerHTML = `
        <div class="empty-state-small">
          <i data-feather="alert-circle"></i>
          <p>An error occurred while loading shared users</p>
        </div>
      `;
      feather.replace();
    }
  }

  function displaySharedUsers(permissions) {
    const sharedUsersList = document.getElementById('shareUsersList');
    if (!sharedUsersList) return;

    // Empty state
    if (!permissions || permissions.length === 0) {
      sharedUsersList.innerHTML = `
        <div class="empty-state-small">
          <i data-feather="users"></i>
          <p>No users have been granted access yet</p>
        </div>
      `;
      feather.replace();
      return;
    }

    // Display users
    sharedUsersList.innerHTML = permissions.map(permission => `
      <div class="share-user-item">
        <div class="share-user-info">
          <span class="share-user-email">${permission.email}</span>
          <span class="share-user-permission ${permission.permission_level === 'edit' ? 'badge-primary' : ''}">
            ${permission.permission_level === 'edit' ? 'Edit' : 'View'}
          </span>
        </div>
        <button type="button"
                class="share-user-remove btn-remove-access"
                data-user-id="${permission.user_id}"
                title="Remove access">
          <i data-feather="trash-2"></i>
        </button>
      </div>
    `).join('');

    feather.replace();

    // Add event listeners to remove buttons
    const removeButtons = sharedUsersList.querySelectorAll('.btn-remove-access');
    removeButtons.forEach(btn => {
      btn.addEventListener('click', handleRemoveAccess);
    });
  }

  async function handleRemoveAccess(e) {
    e.preventDefault();
    const button = e.currentTarget;
    const userId = button.getAttribute('data-user-id');

    const confirmed = confirm('Are you sure you want to remove this user\'s access?');
    if (!confirmed) return;

    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

    // Disable button
    button.disabled = true;

    try {
      const response = await fetch(`/api/image-datasets/${state.datasetId}/permissions/${userId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        }
      });

      const result = await response.json();

      if (response.ok && result.success) {
        showToast('User access removed successfully', 'success');
        // Reload the shared users list
        loadSharedUsers();
      } else {
        showToast(result.message || 'Failed to remove user access', 'error');
        button.disabled = false;
      }
    } catch (error) {
      console.error('Error removing user access:', error);
      showToast('An error occurred while removing user access', 'error');
      button.disabled = false;
    }
  }

  async function handleGrantAccess(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const userEmail = formData.get('email').trim();
    const permissionLevel = formData.get('permission');

    if (!userEmail) {
      showToast('Please enter a user email', 'error');
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(userEmail)) {
      showToast('Please enter a valid email address', 'error');
      return;
    }

    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
    const submitBtn = e.target.querySelector('button[type="submit"]');

    // Disable button
    if (submitBtn) {
      submitBtn.disabled = true;
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = '<i data-feather="loader"></i> Granting...';
      feather.replace();
    }

    try {
      const response = await fetch(`/api/image-datasets/${state.datasetId}/permissions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          user_email: userEmail,
          permission_level: permissionLevel
        })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        showToast('Access granted successfully', 'success');

        // Reset form
        e.target.reset();

        // Reload the shared users list
        loadSharedUsers();
      } else {
        showToast(result.message || 'Failed to grant access', 'error');
      }
    } catch (error) {
      console.error('Error granting access:', error);
      showToast('An error occurred while granting access', 'error');
    } finally {
      // Re-enable button
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i data-feather="user-plus"></i> Grant Access';
        feather.replace();
      }
    }
  }

  // ========================================
  // IMAGE PREVIEW MODAL
  // ========================================

  function initializeImagePreview() {
    if (!elements.imageModal) return;

    // Add click handlers to all view buttons
    document.addEventListener('click', function(e) {
      if (e.target.closest('[data-action="view"]')) {
        e.preventDefault();
        const button = e.target.closest('[data-action="view"]');
        const imageUrl = button.getAttribute('data-image-url');
        const imageId = button.getAttribute('data-image-id');
        const sourceType = button.getAttribute('data-source-type');
        const sourceMetadataStr = button.getAttribute('data-source-metadata');

        let sourceMetadata = null;
        if (sourceMetadataStr) {
          try {
            sourceMetadata = JSON.parse(sourceMetadataStr);
          } catch (e) {
            console.error('Failed to parse source metadata:', e);
          }
        }

        openImagePreview(imageUrl, sourceType, sourceMetadata);
      }

      if (e.target.closest('[data-action="remove"]')) {
        e.preventDefault();
        const button = e.target.closest('[data-action="remove"]');
        const imageId = button.getAttribute('data-image-id');
        handleRemoveImage(imageId, button);
      }
    });

    // Close modal
    const closeBtn = document.getElementById('imageModalClose');
    const overlay = document.getElementById('imageModalOverlay');

    [closeBtn, overlay].filter(el => el).forEach(el => {
      el.addEventListener('click', closeImagePreview);
    });

    // Escape key to close
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && elements.imageModal.classList.contains('active')) {
        closeImagePreview();
      }
    });
  }

  function openImagePreview(imageUrl, sourceType, sourceMetadata) {
    const imageModalImg = document.getElementById('imageModalImg');
    if (imageModalImg) {
      imageModalImg.src = imageUrl;
    }

    // Populate metadata panel
    populateMetadataPanel(sourceType, sourceMetadata);

    elements.imageModal.classList.add('active');
    elements.imageModal.setAttribute('aria-hidden', 'false');

    // Reinitialize feather icons for metadata panel
    if (typeof feather !== 'undefined') {
      feather.replace();
    }
  }

  function populateMetadataPanel(sourceType, metadata) {
    const metadataPanel = document.getElementById('imageMetadataPanel');
    const metadataSource = document.getElementById('metadataSource');
    const metadataTitle = document.getElementById('metadataTitle');
    const metadataTags = document.getElementById('metadataTags');
    const metadataTagsList = document.getElementById('metadataTagsList');
    const metadataLicense = document.getElementById('metadataLicense');
    const metadataOwner = document.getElementById('metadataOwner');

    if (!metadataPanel) return;

    // Reset all sections
    metadataTitle.style.display = 'none';
    metadataTags.style.display = 'none';
    metadataLicense.style.display = 'none';
    metadataOwner.style.display = 'none';

    // Populate source badge
    if (sourceType === 'flickr') {
      metadataSource.innerHTML = '<span class="source-badge source-flickr"><i data-feather="image"></i> Flickr</span>';
    } else {
      metadataSource.innerHTML = '<span class="source-badge source-url"><i data-feather="link"></i> URL</span>';
    }

    // Only show metadata panel if we have metadata
    if (!metadata) {
      metadataPanel.style.display = 'none';
      return;
    }

    metadataPanel.style.display = 'block';

    // Populate title
    if (metadata.title && metadata.title.trim()) {
      metadataTitle.textContent = metadata.title;
      metadataTitle.style.display = 'block';
    }

    // Populate tags
    if (metadata.tags && metadata.tags.length > 0) {
      metadataTagsList.innerHTML = '';
      metadata.tags.forEach(tag => {
        const tagBadge = document.createElement('span');
        tagBadge.className = 'tag-badge';
        tagBadge.textContent = tag;
        tagBadge.title = tag;
        metadataTagsList.appendChild(tagBadge);
      });
      metadataTags.style.display = 'block';
    }

    // Populate license
    if (metadata.license && metadata.license.trim()) {
      metadataLicense.innerHTML = `<strong>License:</strong> ${metadata.license}`;
      metadataLicense.style.display = 'block';
    }

    // Populate owner
    if (metadata.owner_name && metadata.owner_name.trim()) {
      metadataOwner.innerHTML = `Photo by <strong>${metadata.owner_name}</strong>`;
      metadataOwner.style.display = 'block';
    }
  }

  function closeImagePreview() {
    elements.imageModal.classList.remove('active');
    elements.imageModal.setAttribute('aria-hidden', 'true');
  }

  async function handleRemoveImage(imageId, button) {
    const confirmed = confirm('Are you sure you want to remove this image from the dataset?');
    if (!confirmed) return;

    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

    // Disable button
    button.disabled = true;

    try {
      const response = await fetch(`/api/image-datasets/${state.datasetId}/images/${imageId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        }
      });

      const result = await response.json();

      if (response.ok && result.success) {
        showToast('Image removed successfully', 'success');

        // Remove card from DOM
        const card = document.querySelector(`.image-card[data-image-id="${imageId}"]`);
        if (card) {
          card.style.transition = 'opacity 0.3s ease-out';
          card.style.opacity = '0';
          setTimeout(() => {
            card.remove();
            updateImageCount();
          }, 300);
        }
      } else {
        showToast(result.message || 'Failed to remove image', 'error');
        button.disabled = false;
      }
    } catch (error) {
      console.error('Error removing image:', error);
      showToast('An error occurred while removing the image', 'error');
      button.disabled = false;
    }
  }

  // ========================================
  // SELECTION ACTIONS
  // ========================================

  function initializeSelectionActions() {
    // Select All
    if (elements.selectAllImagesBtn) {
      elements.selectAllImagesBtn.addEventListener('click', selectAllImages);
    }

    // Deselect All
    if (elements.deselectAllImagesBtn) {
      elements.deselectAllImagesBtn.addEventListener('click', deselectAllImages);
    }

    // Select Monochrome
    if (elements.selectMonochromeBtn) {
      elements.selectMonochromeBtn.addEventListener('click', handleMonochromeDetection);
    }

    // Select Duplicates
    if (elements.selectDuplicatesBtn) {
      elements.selectDuplicatesBtn.addEventListener('click', handleSelectDuplicates);
    }

    // Select by Tag
    if (elements.selectByTagBtn) {
      elements.selectByTagBtn.addEventListener('click', handleSelectByTag);
    }

    // Also allow pressing Enter in the tag search input
    if (elements.tagSearchInput) {
      elements.tagSearchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          handleSelectByTag();
        }
      });
    }

    // Select by Face Count
    if (elements.selectByFaceCountBtn) {
      elements.selectByFaceCountBtn.addEventListener('click', handleSelectByFaceCount);
    }
  }

  function selectAllImages() {
    const imageCards = document.querySelectorAll('.image-card');
    imageCards.forEach(card => {
      const imageId = card.getAttribute('data-image-id');
      const checkbox = card.querySelector('.image-checkbox');

      if (checkbox) {
        state.selectedImages.add(imageId);
        checkbox.checked = true;
        card.classList.add('selected');
      }
    });

    updateBulkDeleteToolbar();
  }

  function deselectAllImages() {
    state.selectedImages.clear();

    document.querySelectorAll('.image-checkbox').forEach(checkbox => {
      checkbox.checked = false;
      checkbox.closest('.image-card').classList.remove('selected');
    });

    updateBulkDeleteToolbar();
  }

  // ========================================
  // IMAGE SELECTION & BULK DELETE
  // ========================================

  function initializeImageSelection() {
    if (state.permissionLevel !== 'edit' && !state.isOwner) return;

    // Select all / Deselect all buttons
    if (elements.selectAllImagesBtn) {
      elements.selectAllImagesBtn.addEventListener('click', selectAllImages);
    }

    if (elements.deselectAllImagesBtn) {
      elements.deselectAllImagesBtn.addEventListener('click', deselectAllImages);
    }

    // Bulk delete button
    if (elements.bulkDeleteBtn) {
      elements.bulkDeleteBtn.addEventListener('click', handleBulkDelete);
    }

    // Image card click handlers
    initializeImageCardSelectors();
  }

  function initializeImageCardSelectors() {
    const imageCards = document.querySelectorAll('.image-card');

    imageCards.forEach(card => {
      const checkbox = card.querySelector('.image-checkbox');
      const container = card.querySelector('.image-container');

      if (!checkbox || !container) return;

      // Checkbox change event
      checkbox.addEventListener('change', function(e) {
        e.stopPropagation();
        handleImageSelection(card, checkbox.checked);
      });

      // Click on thumbnail to toggle (but not on action buttons)
      container.addEventListener('click', function(e) {
        // Ignore clicks on action buttons
        if (e.target.closest('.image-action-btn')) {
          return;
        }

        // Ignore clicks on checkbox itself (it has its own handler)
        if (e.target.closest('.image-checkbox-wrapper')) {
          return;
        }

        // Toggle checkbox
        checkbox.checked = !checkbox.checked;
        handleImageSelection(card, checkbox.checked);
      });
    });
  }

  function handleImageSelection(card, isSelected) {
    const imageId = card.getAttribute('data-image-id');

    if (isSelected) {
      state.selectedImages.add(imageId);
      card.classList.add('selected');
    } else {
      state.selectedImages.delete(imageId);
      card.classList.remove('selected');
    }

    updateBulkDeleteToolbar();
  }

  function updateBulkDeleteToolbar() {
    const count = state.selectedImages.size;

    if (elements.bulkSelectedCount) {
      elements.bulkSelectedCount.textContent = count;
    }

    if (elements.bulkDeleteToolbar) {
      if (count > 0) {
        elements.bulkDeleteToolbar.classList.add('active');
      } else {
        elements.bulkDeleteToolbar.classList.remove('active');
      }
    }
  }

  function selectAllImages() {
    const imageCards = document.querySelectorAll('.image-card:not(.hidden)');

    imageCards.forEach(card => {
      const checkbox = card.querySelector('.image-checkbox');
      if (checkbox) {
        checkbox.checked = true;
        const imageId = card.getAttribute('data-image-id');
        state.selectedImages.add(imageId);
        card.classList.add('selected');
      }
    });

    updateBulkDeleteToolbar();
  }

  function deselectAllImages() {
    const imageCards = document.querySelectorAll('.image-card');

    imageCards.forEach(card => {
      const checkbox = card.querySelector('.image-checkbox');
      if (checkbox) {
        checkbox.checked = false;
        card.classList.remove('selected');
      }
    });

    state.selectedImages.clear();
    updateBulkDeleteToolbar();
  }

  async function handleBulkDelete() {
    const count = state.selectedImages.size;

    if (count === 0) {
      showToast('No images selected', 'error');
      return;
    }

    // Confirmation dialog
    const confirmed = confirm(`Are you sure you want to delete ${count} selected image${count > 1 ? 's' : ''}? This action cannot be undone.`);

    if (!confirmed) return;

    // Disable button and show loading
    if (elements.bulkDeleteBtn) {
      elements.bulkDeleteBtn.disabled = true;
      elements.bulkDeleteBtn.innerHTML = '<i data-feather="loader"></i> Deleting...';
      feather.replace();
    }

    // Get CSRF token
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

    // Convert Set to Array for iteration
    const imageIds = Array.from(state.selectedImages);
    let successCount = 0;
    let errorCount = 0;

    // Delete images one by one
    for (const imageId of imageIds) {
      try {
        const response = await fetch(`/api/image-datasets/${state.datasetId}/images/${imageId}`, {
          method: 'DELETE',
          headers: {
            'X-CSRFToken': csrfToken
          }
        });

        if (response.ok) {
          successCount++;
          // Remove image card from DOM
          const card = document.querySelector(`.image-card[data-image-id="${imageId}"]`);
          if (card) {
            card.remove();
          }
        } else {
          errorCount++;
        }
      } catch (error) {
        console.error('Error deleting image:', imageId, error);
        errorCount++;
      }
    }

    // Clear selection
    state.selectedImages.clear();
    updateBulkDeleteToolbar();

    // Re-enable button
    if (elements.bulkDeleteBtn) {
      elements.bulkDeleteBtn.disabled = false;
      elements.bulkDeleteBtn.innerHTML = '<i data-feather="trash-2"></i> Delete Selected';
      feather.replace();
    }

    // Update counts
    updateImageCount();

    // Show result
    if (errorCount === 0) {
      showToast(`Successfully deleted ${successCount} image${successCount > 1 ? 's' : ''}`, 'success');
    } else {
      showToast(`Deleted ${successCount} image${successCount > 1 ? 's' : ''}, ${errorCount} failed`, 'warning');
    }

    // Re-initialize selectors for remaining images
    initializeImageCardSelectors();
  }

  // ========================================
  // IMAGE COUNT UPDATE
  // ========================================

  function updateImageCount() {
    const imageCards = document.querySelectorAll('.image-card');
    if (elements.imageCount) {
      elements.imageCount.textContent = imageCards.length;
    }
  }

  // ========================================
  // PAGINATION (Placeholder)
  // ========================================

  function initializePagination() {
    if (elements.prevPage) {
      elements.prevPage.addEventListener('click', () => changePage(state.currentPage - 1));
    }

    if (elements.nextPage) {
      elements.nextPage.addEventListener('click', () => changePage(state.currentPage + 1));
    }
  }

  function changePage(page) {
    window.location.href = `?page=${page}`;
  }

  // ========================================
  // EXPORT DROPDOWN
  // ========================================

  function initializeExportDropdown() {
    if (!elements.exportBtn || !elements.exportMenu) return;

    elements.exportBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      elements.exportMenu.classList.toggle('active');
    });

    // Close on outside click
    document.addEventListener('click', function() {
      if (elements.exportMenu) {
        elements.exportMenu.classList.remove('active');
      }
    });

    // Export buttons
    const exportItems = document.querySelectorAll('.dropdown-item[data-export-type]');
    exportItems.forEach(item => {
      item.addEventListener('click', function(e) {
        e.preventDefault();
        const exportType = this.getAttribute('data-export-type');
        handleExport(exportType);
      });
    });
  }

  async function handleExport(exportType) {
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

    try {
      const response = await fetch(`/api/image-datasets/${state.datasetId}/export/${exportType}`, {
        method: 'GET',
        headers: {
          'X-CSRFToken': csrfToken
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dataset_${state.datasetId}.${exportType === 'json' ? 'json' : 'zip'}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

        showToast('Export started successfully', 'success');
      } else {
        showToast('Failed to export dataset', 'error');
      }
    } catch (error) {
      console.error('Error exporting:', error);
      showToast('An error occurred while exporting', 'error');
    }
  }

  // ========================================
  // REFRESH PAGE
  // ========================================

  function initializeRefreshButton() {
    if (!elements.refreshPageBtn) return;

    elements.refreshPageBtn.addEventListener('click', function() {
      window.location.reload();
    });
  }

  // ========================================
  // DELETE DATASET
  // ========================================

  function initializeDeleteDataset() {
    if (!elements.deleteDatasetBtn) return;

    elements.deleteDatasetBtn.addEventListener('click', async function() {
      const confirmed = confirm(
        'Are you sure you want to delete this entire dataset?\n\n' +
        'This action cannot be undone. All images and permissions will be permanently deleted.'
      );

      if (!confirmed) return;

      const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

      try {
        const response = await fetch(`/api/image-datasets/${state.datasetId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          }
        });

        const result = await response.json();

        if (response.ok && result.success) {
          showToast('Dataset deleted successfully', 'success');
          setTimeout(() => {
            window.location.href = '/image-datasets';
          }, 500);
        } else {
          showToast(result.message || 'Failed to delete dataset', 'error');
        }
      } catch (error) {
        console.error('Error deleting dataset:', error);
        showToast('An error occurred while deleting the dataset', 'error');
      }
    });
  }

  // ========================================
  // INLINE EDITING
  // ========================================

  function initializeInlineEditing() {
    if (!state.isOwner) return;

    if (elements.datasetTitle) {
      elements.datasetTitle.addEventListener('blur', saveDatasetTitle);
      elements.datasetTitle.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.blur();
        }
      });
    }

    if (elements.datasetDescription) {
      elements.datasetDescription.addEventListener('blur', saveDatasetDescription);
    }
  }

  async function saveDatasetTitle() {
    const newTitle = elements.datasetTitle.textContent.trim();
    if (!newTitle) {
      elements.datasetTitle.textContent = 'Untitled Dataset';
      return;
    }

    await updateDataset({ name: newTitle });
  }

  async function saveDatasetDescription() {
    const newDescription = elements.datasetDescription.textContent.trim();
    await updateDataset({ description: newDescription || null });
  }

  async function updateDataset(data) {
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

    try {
      const response = await fetch(`/api/image-datasets/${state.datasetId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (response.ok && result.success) {
        showToast('Dataset updated successfully', 'success');
      } else {
        showToast(result.message || 'Failed to update dataset', 'error');
      }
    } catch (error) {
      console.error('Error updating dataset:', error);
      showToast('An error occurred while updating the dataset', 'error');
    }
  }

  // ========================================
  // TOAST NOTIFICATIONS
  // ========================================

  function showToast(message, type = 'info') {
    // Remove existing toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
      existingToast.remove();
    }

    // Create toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <i data-feather="${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info'}"></i>
      <span>${message}</span>
    `;

    // Add styles
    Object.assign(toast.style, {
      position: 'fixed',
      bottom: '2rem',
      right: '2rem',
      zIndex: '9999',
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      padding: '0.75rem 1rem',
      backgroundColor: 'var(--color-bg-elevated)',
      border: '1px solid',
      borderLeft: '3px solid',
      borderRadius: '0',
      color: type === 'success' ? 'var(--color-success)' : type === 'error' ? 'var(--color-error)' : 'var(--color-info)',
      borderColor: type === 'success' ? 'rgba(0, 255, 136, 0.3)' : type === 'error' ? 'rgba(255, 68, 102, 0.3)' : 'rgba(0, 217, 255, 0.3)',
      borderLeftColor: type === 'success' ? 'var(--color-success)' : type === 'error' ? 'var(--color-error)' : 'var(--color-info)',
      boxShadow: type === 'success' ? '0 0 30px rgba(0, 255, 136, 0.3)' : type === 'error' ? '0 0 30px rgba(255, 68, 102, 0.3)' : '0 0 30px rgba(0, 217, 255, 0.3)',
      fontSize: 'var(--font-size-body)',
      fontWeight: 'var(--font-weight-medium)',
      animation: 'slideIn 0.3s ease-out'
    });

    // Add animation
    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideIn {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
    `;
    document.head.appendChild(style);

    // Add to page
    document.body.appendChild(toast);
    feather.replace();

    // Auto-remove after 4 seconds
    setTimeout(() => {
      toast.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // ========================================
  // FACE DETECTION
  // ========================================

  // Face detection functions removed - now using server-side stored face_count

  /**
   * Handle face count selection using server-side stored face_count values
   */
  function handleSelectByFaceCount() {
    const faceCountFilter = elements.faceCountSelect?.value;

    if (!faceCountFilter) {
      showToast('Please select a face count filter', 'error');
      return;
    }

    // Deselect all first
    state.selectedImages.clear();
    document.querySelectorAll('.image-checkbox').forEach(checkbox => {
      checkbox.checked = false;
      checkbox.closest('.image-card').classList.remove('selected');
    });

    // Track how many we matched
    let matchCount = 0;

    // Get all image cards and filter by stored face_count data attribute
    const imageCards = document.querySelectorAll('.image-card');

    imageCards.forEach(card => {
      const imageId = card.getAttribute('data-image-id');
      const faceCountAttr = card.getAttribute('data-face-count');

      // Parse face count (handle 'null' string for unanalyzed images)
      const faceCount = faceCountAttr === 'null' ? null : parseInt(faceCountAttr, 10);

      let shouldSelect = false;

      // Apply filter logic
      switch(faceCountFilter) {
        case '0':
          shouldSelect = faceCount === 0;
          break;
        case '1':
          shouldSelect = faceCount === 1;
          break;
        case '2':
          shouldSelect = faceCount === 2;
          break;
        case '3':
          shouldSelect = faceCount !== null && faceCount >= 3;
          break;
      }

      if (shouldSelect) {
        matchCount++;
        state.selectedImages.add(imageId);

        const checkbox = document.querySelector(`.image-checkbox[data-image-id="${imageId}"]`);
        if (checkbox) {
          checkbox.checked = true;
          checkbox.closest('.image-card').classList.add('selected');
        }
      }
    });

    // Update UI
    updateBulkDeleteToolbar();

    // Show result
    const filterText = {
      '0': 'no faces',
      '1': '1 face',
      '2': '2 faces',
      '3': '3+ faces'
    }[faceCountFilter];

    if (matchCount > 0) {
      showToast(`Selected ${matchCount} image${matchCount > 1 ? 's' : ''} with ${filterText}`, 'success');
    } else {
      showToast(`No images found with ${filterText}`, 'info');
    }
  }

  // ========================================
  // DUPLICATE DETECTION
  // ========================================

  /**
   * Handle duplicate/similar image detection
   * Uses perceptual hashing to find visually similar images
   */
  function handleSelectDuplicates() {
    // Deselect all first
    state.selectedImages.clear();
    document.querySelectorAll('.image-checkbox').forEach(checkbox => {
      checkbox.checked = false;
      checkbox.closest('.image-card').classList.remove('selected');
    });

    showToast('Detecting duplicate and similar images...', 'info');

    detectDuplicateImages()
      .then(result => {
        const { duplicates, debugInfo } = result;

        // Select all duplicates (keeping the first of each group)
        duplicates.forEach(imageId => {
          state.selectedImages.add(imageId);
          const checkbox = document.querySelector(`.image-checkbox[data-image-id="${imageId}"]`);
          if (checkbox) {
            checkbox.checked = true;
            checkbox.closest('.image-card').classList.add('selected');
          }
        });

        // Update UI
        updateBulkDeleteToolbar();

        // Show result
        if (duplicates.length > 0) {
          showToast(`Selected ${duplicates.length} duplicate/similar image${duplicates.length > 1 ? 's' : ''} for deletion`, 'success');
        } else {
          showToast('No duplicate or similar images detected', 'info');
        }
      });
  }

  /**
   * Generate image fingerprint using color histogram and structure
   * More robust than simple perceptual hash for detecting similar images
   */
  function generateImageFingerprint(img) {
    return new Promise((resolve) => {
      const corsImg = new Image();
      corsImg.crossOrigin = 'anonymous';

      corsImg.onload = () => {
        try {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');

          // Use 32x32 for better detail
          const size = 32;
          canvas.width = size;
          canvas.height = size;

          ctx.imageSmoothingEnabled = true;
          ctx.imageSmoothingQuality = 'high';
          ctx.drawImage(corsImg, 0, 0, size, size);

          const imageData = ctx.getImageData(0, 0, size, size);
          const data = imageData.data;

          // Create color histogram (8 bins per channel = 512 total bins)
          const histogramBins = 8;
          const histogram = new Array(histogramBins * histogramBins * histogramBins).fill(0);

          // Build histogram
          for (let i = 0; i < data.length; i += 4) {
            const r = Math.floor(data[i] / 256 * histogramBins);
            const g = Math.floor(data[i + 1] / 256 * histogramBins);
            const b = Math.floor(data[i + 2] / 256 * histogramBins);
            const binIndex = r * histogramBins * histogramBins + g * histogramBins + b;
            histogram[binIndex]++;
          }

          // Normalize histogram
          const total = size * size;
          const normalizedHistogram = histogram.map(count => count / total);

          // Also get average color per quadrant for spatial information
          const quadrants = [];
          const quadSize = size / 4;
          for (let qy = 0; qy < 4; qy++) {
            for (let qx = 0; qx < 4; qx++) {
              let rSum = 0, gSum = 0, bSum = 0, count = 0;

              for (let y = qy * quadSize; y < (qy + 1) * quadSize; y++) {
                for (let x = qx * quadSize; x < (qx + 1) * quadSize; x++) {
                  const idx = (Math.floor(y) * size + Math.floor(x)) * 4;
                  rSum += data[idx];
                  gSum += data[idx + 1];
                  bSum += data[idx + 2];
                  count++;
                }
              }

              quadrants.push({
                r: Math.round(rSum / count),
                g: Math.round(gSum / count),
                b: Math.round(bSum / count)
              });
            }
          }

          resolve({
            histogram: normalizedHistogram,
            quadrants: quadrants
          });
        } catch (error) {
          console.warn('Could not generate fingerprint for image:', error);
          resolve(null);
        }
      };

      corsImg.onerror = () => {
        console.warn('CORS error loading image:', img.src);
        resolve(null);
      };

      corsImg.src = img.src;
    });
  }

  /**
   * Calculate similarity between two image fingerprints
   * Returns a score from 0 (identical) to 1 (completely different)
   */
  function calculateImageSimilarity(fingerprint1, fingerprint2) {
    if (!fingerprint1 || !fingerprint2) return 1.0;

    // Calculate histogram distance (Chi-square distance)
    let histogramDistance = 0;
    for (let i = 0; i < fingerprint1.histogram.length; i++) {
      const sum = fingerprint1.histogram[i] + fingerprint2.histogram[i];
      if (sum > 0) {
        const diff = fingerprint1.histogram[i] - fingerprint2.histogram[i];
        histogramDistance += (diff * diff) / sum;
      }
    }
    histogramDistance = histogramDistance / 2; // Normalize

    // Calculate quadrant color difference (structural similarity)
    let quadrantDistance = 0;
    for (let i = 0; i < fingerprint1.quadrants.length; i++) {
      const q1 = fingerprint1.quadrants[i];
      const q2 = fingerprint2.quadrants[i];

      // Euclidean distance in RGB space
      const colorDiff = Math.sqrt(
        Math.pow(q1.r - q2.r, 2) +
        Math.pow(q1.g - q2.g, 2) +
        Math.pow(q1.b - q2.b, 2)
      );
      quadrantDistance += colorDiff;
    }
    quadrantDistance = quadrantDistance / (fingerprint1.quadrants.length * 441.67); // Normalize (max is sqrt(255^2*3))

    // Weighted combination: 70% histogram, 30% structure
    const combinedDistance = (histogramDistance * 0.7) + (quadrantDistance * 0.3);

    return combinedDistance;
  }

  /**
   * Detect duplicate and similar images
   * Returns array of image IDs to delete (keeps first of each duplicate group)
   */
  async function detectDuplicateImages() {
    const imageCards = document.querySelectorAll('.image-card');
    const imageData = []; // Array of {imageId, fingerprint, card}
    const promises = [];

    // Generate fingerprints for all images
    imageCards.forEach(card => {
      const imageId = card.getAttribute('data-image-id');
      const img = card.querySelector('.image-thumbnail');

      if (!img) return;

      const promise = generateImageFingerprint(img).then(fingerprint => {
        if (fingerprint) {
          imageData.push({ imageId, fingerprint, card });
        }
      });

      promises.push(promise);
    });

    await Promise.all(promises);

    // Find duplicates/similar images
    const duplicatesToDelete = new Set();
    const kept = new Set(); // Track which images we're keeping
    const allPairs = []; // Track all comparisons for debugging

    // Similarity threshold: 0.0-0.15 = very similar (lower is more similar)
    // This is based on normalized histogram + quadrant color distance
    const SIMILARITY_THRESHOLD = 0.15;

    // Compare each image with all others
    for (let i = 0; i < imageData.length; i++) {
      // Skip if this image is already marked for deletion
      if (duplicatesToDelete.has(imageData[i].imageId)) continue;

      // This image will be kept
      kept.add(imageData[i].imageId);

      // Compare with all subsequent images
      for (let j = i + 1; j < imageData.length; j++) {
        // Skip if already marked for deletion
        if (duplicatesToDelete.has(imageData[j].imageId)) continue;

        const similarity = calculateImageSimilarity(imageData[i].fingerprint, imageData[j].fingerprint);

        // Store all pairs for debugging (limit to first 50 to avoid spam)
        if (allPairs.length < 50 && similarity < 0.5) {
          allPairs.push({
            id1: imageData[i].imageId,
            id2: imageData[j].imageId,
            distance: Math.round(similarity * 100) / 100 // Round to 2 decimals
          });
        }

        if (similarity <= SIMILARITY_THRESHOLD) {
          // Mark as duplicate
          duplicatesToDelete.add(imageData[j].imageId);
        }
      }
    }

    return {
      duplicates: Array.from(duplicatesToDelete),
      debugInfo: {
        totalImages: imageData.length,
        uniqueImages: kept.size,
        duplicatesFound: duplicatesToDelete.size,
        pairs: allPairs.sort((a, b) => a.distance - b.distance) // Sort by similarity
      }
    };
  }

  // ========================================
  // SELECT BY TAG
  // ========================================

  /**
   * Handle tag-based selection
   * Searches all images for the specified tag and selects matches
   */
  function handleSelectByTag() {
    const searchTag = elements.tagSearchInput?.value?.trim().toLowerCase();

    if (!searchTag) {
      showToast('Please enter a tag to search for', 'error');
      return;
    }

    // Deselect all first
    state.selectedImages.clear();
    document.querySelectorAll('.image-checkbox').forEach(checkbox => {
      checkbox.checked = false;
      checkbox.closest('.image-card').classList.remove('selected');
    });

    let matchCount = 0;
    const imageCards = document.querySelectorAll('.image-card');

    imageCards.forEach(card => {
      const imageId = card.getAttribute('data-image-id');

      // Get metadata from the view button
      const viewBtn = card.querySelector('[data-action="view"]');
      if (!viewBtn) return;

      const metadataStr = viewBtn.getAttribute('data-source-metadata');
      if (!metadataStr) return;

      try {
        const metadata = JSON.parse(metadataStr);
        const tags = metadata.tags || [];

        // Check if any tag matches (case-insensitive, partial match)
        const hasMatchingTag = tags.some(tag =>
          tag.toLowerCase().includes(searchTag)
        );

        if (hasMatchingTag) {
          matchCount++;
          state.selectedImages.add(imageId);

          const checkbox = card.querySelector('.image-checkbox');
          if (checkbox) {
            checkbox.checked = true;
            card.classList.add('selected');
          }
        }
      } catch (error) {
        console.warn('Error parsing metadata for image:', imageId, error);
      }
    });

    // Update UI
    updateBulkDeleteToolbar();

    // Show result
    if (matchCount > 0) {
      showToast(`Selected ${matchCount} image${matchCount > 1 ? 's' : ''} with tag "${searchTag}"`, 'success');
    } else {
      showToast(`No images found with tag "${searchTag}"`, 'info');
    }
  }

  // ========================================
  // MONOCHROME DETECTION
  // ========================================

  /**
   * Handle monochrome detection button click
   * Detects B&W images and selects them
   */
  function handleMonochromeDetection() {
    // Deselect all first
    state.selectedImages.clear();
    document.querySelectorAll('.image-checkbox').forEach(checkbox => {
      checkbox.checked = false;
    });

    // Show processing message
    showToast('Detecting black & white images...', 'info');

    // Start detection
    state.monochromeDetection.analyzed.clear();
    state.monochromeDetection.monochromeImages.clear();

    detectMonochromeImages()
      .then(count => {
        // Select all detected monochrome images
        state.monochromeDetection.monochromeImages.forEach(imageId => {
          state.selectedImages.add(imageId);
          const checkbox = document.querySelector(`.image-checkbox[data-image-id="${imageId}"]`);
          if (checkbox) {
            checkbox.checked = true;
            checkbox.closest('.image-card').classList.add('selected');
          }
        });

        // Update UI
        updateBulkDeleteToolbar();

        // Show result
        if (count > 0) {
          showToast(`Detected and selected ${count} black & white image${count > 1 ? 's' : ''}`, 'success');
        } else {
          showToast('No black & white images detected', 'info');
        }
      });
  }

  /**
   * Detect if an image is monochrome (black & white / grayscale)
   * Uses Canvas API to sample pixels and check color variance
   */
  function isImageMonochrome(img) {
    return new Promise((resolve) => {
      // Create a new image with CORS enabled
      const corsImg = new Image();
      corsImg.crossOrigin = 'anonymous';

      corsImg.onload = () => {
        try {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');

          // Use a smaller sample size for performance (max 200x200)
          const maxSize = 200;
          const scale = Math.min(maxSize / corsImg.width, maxSize / corsImg.height, 1);
          canvas.width = corsImg.width * scale;
          canvas.height = corsImg.height * scale;

          ctx.drawImage(corsImg, 0, 0, canvas.width, canvas.height);

          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const data = imageData.data;

          // Sample every nth pixel for performance (sample ~1000 pixels)
          const totalPixels = data.length / 4;
          const sampleRate = Math.max(1, Math.floor(totalPixels / 1000));

          let colorVariance = 0;
          let sampledPixels = 0;

          for (let i = 0; i < data.length; i += 4 * sampleRate) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];

            // Calculate variance between RGB channels
            const avg = (r + g + b) / 3;
            const variance = Math.abs(r - avg) + Math.abs(g - avg) + Math.abs(b - avg);

            colorVariance += variance;
            sampledPixels++;
          }

          // Average variance per pixel
          const avgVariance = colorVariance / sampledPixels;

          // Threshold: if average variance is less than 8, consider it monochrome
          // Slightly higher threshold to account for JPEG compression artifacts
          resolve(avgVariance < 8);
        } catch (error) {
          console.warn('Could not analyze image for monochrome detection:', error);
          resolve(false);
        }
      };

      corsImg.onerror = () => {
        // If CORS fails, try without and catch the error
        console.warn('CORS error loading image, skipping:', img.src);
        resolve(false);
      };

      corsImg.src = img.src;
    });
  }

  /**
   * Detect monochrome images in the current page
   * Returns a promise that resolves with the count
   */
  async function detectMonochromeImages() {
    const imageCards = document.querySelectorAll('.image-card');
    const promises = [];

    imageCards.forEach(card => {
      const imageId = card.getAttribute('data-image-id');
      const img = card.querySelector('.image-thumbnail');

      if (!img) return;

      const promise = isImageMonochrome(img).then(isMono => {
        if (isMono) {
          state.monochromeDetection.monochromeImages.add(imageId);
        }
        state.monochromeDetection.analyzed.add(imageId);
      });

      promises.push(promise);
    });

    await Promise.all(promises);
    return state.monochromeDetection.monochromeImages.size;
  }

  // ========================================
  // FEATHER ICONS
  // ========================================

  function initializeFeatherIcons() {
    if (typeof feather !== 'undefined') {
      feather.replace();
    }
  }

})();
