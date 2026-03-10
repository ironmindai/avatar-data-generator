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
    selectedFlickrResults: new Set(),
    flickrSearch: {
      keyword: '',
      excludeUsed: true,
      licenseFilter: '',
      results: [],
      currentPage: 1,
      totalPages: 1,
      hasMore: false,
      isLoadingMore: false
    },
    personDetection: {
      model: null,
      isInitialized: false,
      isProcessing: false,
      processedCount: 0,
      totalCount: 0
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
    imageModal: document.getElementById('imageModal')
  };

  // ========================================
  // INITIALIZATION
  // ========================================

  document.addEventListener('DOMContentLoaded', function() {
    loadInitialState();
    initializeFlickrModal();
    initializeUrlModal();
    initializeShareModal();
    initializeImagePreview();
    initializeFilters();
    initializePagination();
    initializeExportDropdown();
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

    // Update filter counts
    updateFilterCounts();
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
      results: [],
      currentPage: 1,
      totalPages: 1,
      hasMore: false,
      isLoadingMore: false
    };
  }

  async function handleFlickrSearch(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const keyword = formData.get('keyword').trim();
    const excludeUsed = formData.get('exclude_used') === 'on';
    const licenseFilter = formData.get('license_filter') || '';

    if (!keyword) {
      showToast('Please enter a keyword', 'error');
      return;
    }

    // Reset state for new search
    state.flickrSearch.keyword = keyword;
    state.flickrSearch.excludeUsed = excludeUsed;
    state.flickrSearch.licenseFilter = licenseFilter;
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
    const { keyword, excludeUsed, licenseFilter, currentPage } = state.flickrSearch;

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

    // Trigger person detection after displaying results
    detectPeopleInFlickrResults();
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

    // Trigger person detection for newly appended results
    detectPeopleInFlickrResults();
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

    // Disable button
    const importBtn = document.getElementById('importSelectedBtn');
    importBtn.disabled = true;
    const originalText = importBtn.innerHTML;
    importBtn.innerHTML = '<i data-feather="loader"></i> Importing...';
    feather.replace();

    try {
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

      if (response.ok && result.success) {
        showToast(`Successfully imported ${result.imported_count} images`, 'success');
        closeFlickrModal();

        // Reload page to show new images
        setTimeout(() => window.location.reload(), 500);
      } else {
        showToast(result.message || 'Failed to import images', 'error');
        importBtn.disabled = false;
        importBtn.innerHTML = originalText;
        feather.replace();
      }
    } catch (error) {
      console.error('Error importing from Flickr:', error);
      showToast('An error occurred while importing images', 'error');
      importBtn.disabled = false;
      importBtn.innerHTML = originalText;
      feather.replace();
    }
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
        openImagePreview(imageUrl);
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

  function openImagePreview(imageUrl) {
    const imageModalImg = document.getElementById('imageModalImg');
    if (imageModalImg) {
      imageModalImg.src = imageUrl;
    }

    elements.imageModal.classList.add('active');
    elements.imageModal.setAttribute('aria-hidden', 'false');
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
            updateFilterCounts();
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
  // FILTERS
  // ========================================

  function initializeFilters() {
    elements.filterBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        const filter = this.getAttribute('data-filter');
        setFilter(filter);
      });
    });
  }

  function setFilter(filter) {
    state.currentFilter = filter;

    // Update active button
    elements.filterBtns.forEach(btn => {
      if (btn.getAttribute('data-filter') === filter) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // Filter images
    const imageCards = document.querySelectorAll('.image-card');
    imageCards.forEach(card => {
      const sourceType = card.getAttribute('data-source-type');

      if (filter === 'all' || sourceType === filter) {
        card.classList.remove('hidden');
      } else {
        card.classList.add('hidden');
      }
    });
  }

  function updateFilterCounts() {
    const imageCards = document.querySelectorAll('.image-card');
    let flickrCount = 0;
    let urlCount = 0;

    imageCards.forEach(card => {
      const sourceType = card.getAttribute('data-source-type');
      if (sourceType === 'flickr') flickrCount++;
      if (sourceType === 'url') urlCount++;
    });

    const filterCountAll = document.getElementById('filterCountAll');
    const filterCountFlickr = document.getElementById('filterCountFlickr');
    const filterCountUrl = document.getElementById('filterCountUrl');

    if (filterCountAll) filterCountAll.textContent = imageCards.length;
    if (filterCountFlickr) filterCountFlickr.textContent = flickrCount;
    if (filterCountUrl) filterCountUrl.textContent = urlCount;
  }

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
  // FEATHER ICONS
  // ========================================

  function initializeFeatherIcons() {
    if (typeof feather !== 'undefined') {
      feather.replace();
    }
  }

})();
