// SREF Search Frontend JavaScript

class SREFSearch {
  constructor() {
    this.searchInput = document.getElementById("searchInput");
    this.searchButton = document.getElementById("searchButton");
    this.loadingIndicator = document.getElementById("loadingIndicator");
    this.resultsSection = document.getElementById("resultsSection");
    this.resultsContainer = document.getElementById("resultsContainer");
    this.resultsTitle = document.getElementById("resultsTitle");
    this.resultsCount = document.getElementById("resultsCount");
    this.errorMessage = document.getElementById("errorMessage");
    this.errorText = document.getElementById("errorText");
    this.pagination = document.getElementById("pagination");
    this.prevButton = document.getElementById("prevButton");
    this.nextButton = document.getElementById("nextButton");
    this.paginationInfo = document.getElementById("paginationInfo");

    // Pagination state
    this.currentPage = 1;
    this.resultsPerPage = 9;
    this.allResults = [];
    this.currentResults = [];

    // Dynamic tags
    this.availableTags = [];
    this.displayedTags = [];

    // Auto-advance functionality
    this.autoAdvanceIntervals = new Map();
    this.autoAdvanceTimeouts = new Map();

    this.initializeEventListeners();
    this.loadTags();
  }

  initializeEventListeners() {
    // Search button click
    this.searchButton.addEventListener("click", () => this.performSearch());

    // Enter key in search input
    this.searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        this.performSearch();
      }
    });

    // Search input focus
    this.searchInput.addEventListener("focus", () => {
      this.hideError();
    });

    // Pagination buttons
    this.prevButton.addEventListener("click", () => this.previousPage());
    this.nextButton.addEventListener("click", () => this.nextPage());

    // Shuffle button
    const shuffleButton = document.getElementById("shuffleButton");
    if (shuffleButton) {
      shuffleButton.addEventListener("click", () => this.shuffleExamples());
    }
  }

  async performSearch(query = null) {
    const searchQuery = query || this.searchInput.value.trim();

    if (!searchQuery) {
      this.showError("Please enter a search term");
      return;
    }

    this.showLoading();
    this.hideError();
    this.hideResults();

    try {
      const response = await fetch("/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: searchQuery }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Search failed");
      }

      this.allResults = data.results;
      this.currentPage = 1;
      this.displayResults(data);
    } catch (error) {
      console.error("Search error:", error);
      this.showError(`Search failed: ${error.message}`);
    } finally {
      this.hideLoading();
    }
  }

  displayResults(data) {
    this.resultsTitle.textContent = `Results for "${data.query}"`;
    // Hide results count
    this.resultsCount.style.display = "none";

    this.resultsContainer.innerHTML = "";

    if (this.allResults.length === 0) {
      this.resultsContainer.innerHTML = `
                <div class="no-results">
                    <p>No SREF styles found matching your search. Try different keywords or check the examples above.</p>
                </div>
            `;
    } else {
      this.updatePagination();
      this.displayCurrentPage();
    }

    this.showResults();
  }

  displaySimilarResults(data) {
    this.resultsTitle.textContent = `Similar to ${data.reference_sref}`;
    // Hide results count
    this.resultsCount.style.display = "none";

    this.resultsContainer.innerHTML = "";

    if (this.allResults.length === 0) {
      this.resultsContainer.innerHTML = `
                <div class="no-results">
                    <p>No similar SREF styles found.</p>
                </div>
            `;
    } else {
      this.updatePagination();
      this.displayCurrentPage();
    }

    this.showResults();
  }

  displayCurrentPage() {
    this.resultsContainer.innerHTML = "";

    const startIndex = (this.currentPage - 1) * this.resultsPerPage;
    const endIndex = startIndex + this.resultsPerPage;
    this.currentResults = this.allResults.slice(startIndex, endIndex);

    this.currentResults.forEach((result, index) => {
      const globalIndex = startIndex + index + 1;
      const resultCard = this.createResultCard(result, globalIndex);
      this.resultsContainer.appendChild(resultCard);

      // Start auto-advance for this card (no progressive delay)
      this.startAutoAdvance(resultCard, result.sref_code);
    });
  }

  updatePagination() {
    const totalPages = Math.ceil(this.allResults.length / this.resultsPerPage);

    if (totalPages <= 1) {
      this.pagination.classList.add("hidden");
      return;
    }

    this.pagination.classList.remove("hidden");
    this.prevButton.disabled = this.currentPage === 1;
    this.nextButton.disabled = this.currentPage === totalPages;

    this.paginationInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
  }

  previousPage() {
    if (this.currentPage > 1) {
      this.stopAllAutoAdvance();
      this.currentPage--;
      this.displayCurrentPage();
      this.updatePagination();
    }
  }

  nextPage() {
    const totalPages = Math.ceil(this.allResults.length / this.resultsPerPage);
    if (this.currentPage < totalPages) {
      this.stopAllAutoAdvance();
      this.currentPage++;
      this.displayCurrentPage();
      this.updatePagination();
    }
  }

  createResultCard(result, rank) {
    const card = document.createElement("div");
    card.className = "sref-card";

    // Extract tags from summary
    const tags = this.extractTags(result.summary);
    const tagsHtml = tags
      .map(
        (tag) =>
          `<span class="tag" onclick="searchByTag('${tag}')">${tag}</span>`
      )
      .join("");

    // Create carousel images HTML
    const carouselImagesHtml = result.thumbnails
      .map(
        (thumb, index) =>
          `<img src="/static/images/${thumb}" alt="SREF ${
            result.sref_code
          } image ${
            index + 1
          }" class="carousel-image" onclick="openImageModal('${
            result.sref_code
          }', ${index})">`
      )
      .join("");

    // Create carousel dots HTML
    const dotsHtml = result.thumbnails
      .map(
        (_, index) =>
          `<span class="carousel-dot ${
            index === 0 ? "active" : ""
          }" data-index="${index}"></span>`
      )
      .join("");

    card.innerHTML = `
       <div class="carousel-container">
         <div class="carousel-images" data-current="0">
           ${carouselImagesHtml}
         </div>
         <button class="carousel-nav prev" onclick="navigateCarousel(this, -1)">‹</button>
         <button class="carousel-nav next" onclick="navigateCarousel(this, 1)">›</button>
         <div class="carousel-dots">
           ${dotsHtml}
         </div>
       </div>
       
       <!-- Top action buttons -->
       <div class="card-top-actions">
         <button class="copy-button" onclick="copySREF('${result.sref_code}', this)" title="Copy SREF Code">
           <span class="copy-icon">📋</span>
         </button>
         <button class="similar-button" onclick="findSimilarSREFs('${result.sref_code}')" title="Find Similar">
           <span class="similar-icon">🔍</span>
         </button>
       </div>
       
       <!-- Copy feedback (hidden by default) -->
       <div class="copy-feedback">Copied!</div>
       
       <!-- Tags at bottom -->
       <div class="card-bottom-tags">
         <div class="sref-tags">
           ${tagsHtml}
         </div>
       </div>
     `;

    return card;
  }

  extractTags(summary) {
    // Extract key themes from summary text
    const match = summary.match(/Key themes: (.+)/);
    if (match) {
      return match[1]
        .split(",")
        .map((tag) => tag.trim().split(" ")[0]) // Get first word before count
        .filter((tag) => tag.length > 2)
        .slice(0, 5); // Limit to 5 tags
    }
    return ["visual", "style"];
  }

  showLoading() {
    this.loadingIndicator.classList.remove("hidden");
  }

  hideLoading() {
    this.loadingIndicator.classList.add("hidden");
  }

  showResults() {
    this.resultsSection.classList.remove("hidden");
  }

  hideResults() {
    this.resultsSection.classList.add("hidden");
    this.stopAllAutoAdvance();
  }

  showError(message) {
    this.errorText.textContent = message;
    this.errorMessage.classList.remove("hidden");
  }

  hideError() {
    this.errorMessage.classList.add("hidden");
  }

  async loadTags() {
    try {
      const response = await fetch("/tags");
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to load tags");
      }

      this.availableTags = data.tags;
      this.displayTags();
    } catch (error) {
      console.error("Error loading tags:", error);
      // Fallback to hardcoded tags if API fails
      this.availableTags = [
        "abstract",
        "art",
        "photorealistic",
        "portrait",
        "minimalist",
        "design",
        "nature",
        "landscape",
        "geometric",
        "patterns",
        "colorful",
        "painting",
        "dark",
        "moody",
        "atmosphere",
      ];
      this.displayTags();
    }
  }

  displayTags() {
    const exampleTags = document.getElementById("exampleTags");

    // Show first 6 tags initially
    this.displayedTags = this.availableTags.slice(0, 6);

    exampleTags.innerHTML = this.displayedTags
      .map(
        (tag) =>
          `<span class="example-tag" onclick="searchExample('${tag}')">${tag}</span>`
      )
      .join("");
  }

  shuffleExamples() {
    if (this.availableTags.length === 0) {
      return;
    }

    // Shuffle the available tags array
    const shuffled = [...this.availableTags];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }

    // Take first 6 shuffled tags
    this.displayedTags = shuffled.slice(0, 6);

    // Update the display
    const exampleTags = document.getElementById("exampleTags");
    exampleTags.innerHTML = this.displayedTags
      .map(
        (tag) =>
          `<span class="example-tag" onclick="searchExample('${tag}')">${tag}</span>`
      )
      .join("");
  }

  startAutoAdvance(card, srefCode) {
    const carouselImages = card.querySelector(".carousel-images");
    const dots = card.querySelectorAll(".carousel-dot");

    if (!carouselImages || dots.length <= 1) {
      return; // No need to auto-advance if there's only one image
    }

    let currentIndex = 0;
    const totalImages = dots.length;
    let isPaused = false;

    // Function to advance to next image
    const advanceImage = () => {
      if (isPaused) return;

      currentIndex = (currentIndex + 1) % totalImages;

      // Update carousel position
      carouselImages.style.transform = `translateX(-${currentIndex * 100}%)`;
      carouselImages.dataset.current = currentIndex;

      // Update dots
      dots.forEach((dot, index) => {
        dot.classList.toggle("active", index === currentIndex);
      });
    };

    // Function to start the auto-advance cycle
    const startCycle = () => {
      if (isPaused) return;

      // Wait 5 seconds, then start advancing
      const timeout = setTimeout(() => {
        if (isPaused) return;

        // Start advancing through images
        const interval = setInterval(() => {
          if (isPaused) return;

          advanceImage();

          // If we've completed one full cycle, wait 5 seconds before starting again
          if (currentIndex === 0) {
            clearInterval(interval);
            this.autoAdvanceIntervals.delete(srefCode);

            // Wait 5 seconds and start the cycle again
            const cycleTimeout = setTimeout(() => {
              if (!isPaused) {
                startCycle();
              }
            }, 5000);

            this.autoAdvanceTimeouts.set(srefCode, cycleTimeout);
          }
        }, 3000); // Hold for 3 seconds on each image

        this.autoAdvanceIntervals.set(srefCode, interval);
      }, 5000); // Initial 5-second wait

      this.autoAdvanceTimeouts.set(srefCode, timeout);
    };

    // Pause on hover
    card.addEventListener("mouseenter", () => {
      isPaused = true;
    });

    // Resume on mouse leave
    card.addEventListener("mouseleave", () => {
      isPaused = false;
    });

    // Start the first cycle
    startCycle();
  }

  stopAutoAdvance(srefCode) {
    // Clear interval if it exists
    if (this.autoAdvanceIntervals.has(srefCode)) {
      clearInterval(this.autoAdvanceIntervals.get(srefCode));
      this.autoAdvanceIntervals.delete(srefCode);
    }

    // Clear timeout if it exists
    if (this.autoAdvanceTimeouts.has(srefCode)) {
      clearTimeout(this.autoAdvanceTimeouts.get(srefCode));
      this.autoAdvanceTimeouts.delete(srefCode);
    }
  }

  stopAllAutoAdvance() {
    // Clear all intervals
    this.autoAdvanceIntervals.forEach((interval) => {
      clearInterval(interval);
    });
    this.autoAdvanceIntervals.clear();

    // Clear all timeouts
    this.autoAdvanceTimeouts.forEach((timeout) => {
      clearTimeout(timeout);
    });
    this.autoAdvanceTimeouts.clear();
  }
}

// Global function for example tag clicks
function searchExample(query) {
  const searchInput = document.getElementById("searchInput");
  searchInput.value = query;
  searchInput.focus();

  // Trigger search
  const searchApp = window.srefSearch;
  if (searchApp) {
    searchApp.performSearch();
  }
}

// Global function for tag clicks
function searchByTag(tag) {
  const searchInput = document.getElementById("searchInput");
  searchInput.value = tag;
  searchInput.focus();

  // Trigger search
  const searchApp = window.srefSearch;
  if (searchApp) {
    searchApp.performSearch(tag);
  }
}

// Carousel navigation function
function navigateCarousel(button, direction) {
  const card = button.closest(".sref-card");
  const carouselImages = card.querySelector(".carousel-images");
  const dots = card.querySelectorAll(".carousel-dot");
  const currentIndex = parseInt(carouselImages.dataset.current);
  const totalImages = carouselImages.children.length;

  let newIndex = currentIndex + direction;

  // Handle wrapping
  if (newIndex < 0) newIndex = totalImages - 1;
  if (newIndex >= totalImages) newIndex = 0;

  // Update carousel position
  carouselImages.style.transform = `translateX(-${newIndex * 100}%)`;
  carouselImages.dataset.current = newIndex;

  // Update dots
  dots.forEach((dot, index) => {
    dot.classList.toggle("active", index === newIndex);
  });
}

// Copy SREF code function
function copySREF(srefCode, element) {
  // Copy to clipboard
  navigator.clipboard
    .writeText(srefCode)
    .then(() => {
      // Show feedback
      const feedback = element.nextElementSibling;
      element.classList.add("copied");
      feedback.classList.add("show");

      // Reset after 2 seconds
      setTimeout(() => {
        element.classList.remove("copied");
        feedback.classList.remove("show");
      }, 2000);
    })
    .catch((err) => {
      console.error("Failed to copy SREF code:", err);
      // Fallback for older browsers
      const textArea = document.createElement("textarea");
      textArea.value = srefCode;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);

      // Show feedback
      const feedback = element.nextElementSibling;
      element.classList.add("copied");
      feedback.classList.add("show");

      setTimeout(() => {
        element.classList.remove("copied");
        feedback.classList.remove("show");
      }, 2000);
    });
}

// Global function for finding similar SREFs
async function findSimilarSREFs(srefCode) {
  const searchApp = window.srefSearch;
  if (!searchApp) {
    console.error("Search app not initialized");
    return;
  }

  try {
    // Show loading indicator
    searchApp.showLoading();
    searchApp.hideError();
    searchApp.hideResults();

    // Make API call to find similar SREFs
    const response = await fetch("/similar", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ sref_code: srefCode }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Similar search failed");
    }

    // Update the search input to show what we're finding similar to
    const searchInput = document.getElementById("searchInput");
    searchInput.value = `Similar to ${srefCode}`;

    // Display the similar results
    searchApp.allResults = data.results;
    searchApp.currentPage = 1;
    searchApp.displaySimilarResults(data);
  } catch (error) {
    console.error("Similar search error:", error);
    searchApp.showError(`Similar search failed: ${error.message}`);
  } finally {
    searchApp.hideLoading();
  }
}

// Global function for opening image modal with carousel
function openImageModal(srefCode, startIndex = 0) {
  // Find the result data for this SREF
  const searchApp = window.srefSearch;
  if (!searchApp) {
    console.error("Search app not initialized");
    return;
  }

  // Find the result that matches this SREF code
  const result = searchApp.allResults.find((r) => r.sref_code === srefCode);
  if (!result) {
    console.error("Result not found for SREF:", srefCode);
    return;
  }

  // Create modal container
  const modal = document.createElement("div");
  modal.className = "image-modal";
  modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        cursor: pointer;
    `;

  // Create modal content (non-clickable)
  const modalContent = document.createElement("div");
  modalContent.className = "modal-content";
  modalContent.style.cssText = `
        position: relative;
        max-width: 90%;
        max-height: 90%;
        cursor: default;
    `;

  // Create carousel container
  const carouselContainer = document.createElement("div");
  carouselContainer.className = "modal-carousel";
  carouselContainer.style.cssText = `
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
    `;

  // Create image container
  const imageContainer = document.createElement("div");
  imageContainer.className = "modal-image-container";
  imageContainer.style.cssText = `
        position: relative;
        overflow: hidden;
        border-radius: 12px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
    `;

  // Create images
  const images = result.thumbnails.map((thumb, index) => {
    const img = document.createElement("img");
    img.src = `/static/images/${thumb}`;
    img.alt = `SREF ${srefCode} image ${index + 1}`;
    img.style.cssText = `
          max-width: 100%;
          max-height: 80vh;
          display: ${index === startIndex ? "block" : "none"};
          transition: opacity 0.3s ease;
        `;
    return img;
  });

  images.forEach((img) => imageContainer.appendChild(img));

  // Create navigation arrows
  const prevArrow = document.createElement("button");
  prevArrow.className = "modal-nav modal-nav-prev";
  prevArrow.innerHTML = "‹";
  prevArrow.style.cssText = `
        position: absolute;
        left: -60px;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(255, 255, 255, 0.2);
        color: white;
        border: none;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        font-size: 24px;
        cursor: pointer;
        transition: all 0.3s ease;
        z-index: 10;
    `;

  const nextArrow = document.createElement("button");
  nextArrow.className = "modal-nav modal-nav-next";
  nextArrow.innerHTML = "›";
  nextArrow.style.cssText = `
        position: absolute;
        right: -60px;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(255, 255, 255, 0.2);
        color: white;
        border: none;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        font-size: 24px;
        cursor: pointer;
        transition: all 0.3s ease;
        z-index: 10;
    `;

  // Create dots indicator
  const dotsContainer = document.createElement("div");
  dotsContainer.className = "modal-dots";
  dotsContainer.style.cssText = `
        display: flex;
        justify-content: center;
        gap: 8px;
        margin-top: 20px;
    `;

  const dots = result.thumbnails.map((_, index) => {
    const dot = document.createElement("span");
    dot.className = `modal-dot ${index === startIndex ? "active" : ""}`;
    dot.style.cssText = `
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: ${
            index === startIndex ? "white" : "rgba(255, 255, 255, 0.5)"
          };
          cursor: pointer;
          transition: all 0.3s ease;
        `;
    return dot;
  });

  dots.forEach((dot) => dotsContainer.appendChild(dot));

  // Create close button
  const closeButton = document.createElement("button");
  closeButton.className = "modal-close";
  closeButton.innerHTML = "×";
  closeButton.style.cssText = `
        position: absolute;
        top: -50px;
        right: 0;
        background: rgba(255, 255, 255, 0.2);
        color: white;
        border: none;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        font-size: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        z-index: 10;
    `;

  // Assemble modal
  carouselContainer.appendChild(prevArrow);
  carouselContainer.appendChild(imageContainer);
  carouselContainer.appendChild(nextArrow);
  modalContent.appendChild(carouselContainer);
  modalContent.appendChild(closeButton);
  modalContent.appendChild(dotsContainer);
  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  // Carousel state
  let currentIndex = startIndex;

  // Navigation functions
  function showImage(index) {
    images.forEach((img, i) => {
      img.style.display = i === index ? "block" : "none";
    });
    dots.forEach((dot, i) => {
      dot.style.background = i === index ? "white" : "rgba(255, 255, 255, 0.5)";
      dot.classList.toggle("active", i === index);
    });
    currentIndex = index;
  }

  function nextImage() {
    const nextIndex = (currentIndex + 1) % images.length;
    showImage(nextIndex);
  }

  function prevImage() {
    const prevIndex = (currentIndex - 1 + images.length) % images.length;
    showImage(prevIndex);
  }

  // Event listeners
  nextArrow.addEventListener("click", (e) => {
    e.stopPropagation();
    nextImage();
  });

  prevArrow.addEventListener("click", (e) => {
    e.stopPropagation();
    prevImage();
  });

  closeButton.addEventListener("click", (e) => {
    e.stopPropagation();
    document.body.removeChild(modal);
  });

  dots.forEach((dot, index) => {
    dot.addEventListener("click", (e) => {
      e.stopPropagation();
      showImage(index);
    });
  });

  // Close modal on background click
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      document.body.removeChild(modal);
    }
  });

  // Keyboard navigation
  const keyHandler = (e) => {
    if (e.key === "Escape") {
      document.body.removeChild(modal);
      document.removeEventListener("keydown", keyHandler);
    } else if (e.key === "ArrowLeft") {
      prevImage();
    } else if (e.key === "ArrowRight") {
      nextImage();
    }
  };

  document.addEventListener("keydown", keyHandler);

  // Hover effects for navigation
  [prevArrow, nextArrow, closeButton].forEach((button) => {
    button.addEventListener("mouseenter", () => {
      button.style.background = "rgba(255, 255, 255, 0.4)";
    });
    button.addEventListener("mouseleave", () => {
      button.style.background = "rgba(255, 255, 255, 0.2)";
    });
  });
}

// Initialize the application when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.srefSearch = new SREFSearch();

  // Focus on search input
  document.getElementById("searchInput").focus();

  console.log("SREF Search application initialized");
});
