/**
 * Message Modal Module
 * Handles modal functionality for message details
 */

// Set up modal event handlers
document.addEventListener('DOMContentLoaded', function() {
  // Create modal HTML if it doesn't exist (for shared views)
  if (!document.getElementById('message-modal')) {
    const modalHTML = `
            <div id="message-modal" class="modal">
                <div class="modal-content">
                    <span class="modal-close">&times;</span>
                    <div class="modal-header">
                        <h2 id="modal-title" style="margin-bottom: 0;">Message Details</h2>
                        <div class="modal-navigation">
                            <button id="modal-prev-btn" class="modal-nav-btn" onclick="navigateMessage(-1)">← Previous</button>
                            <span id="modal-position" class="modal-position">1 of 100</span>
                            <button id="modal-next-btn" class="modal-nav-btn" onclick="navigateMessage(1)">Next →</button>
                        </div>
                    </div>
                    <div id="modal-body">
                        <!-- Details will be inserted here -->
                    </div>
                </div>
            </div>
        `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
  }
    
  // Modal close button handler
  const closeButton = document.querySelector('.modal-close');
  if (closeButton) {
    closeButton.addEventListener('click', () => {
      document.getElementById('message-modal').style.display = 'none';
    });
  }
    
  // Click outside modal to close
  window.addEventListener('click', (event) => {
    const modal = document.getElementById('message-modal');
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  });
    
  // Keyboard navigation for modal
  document.addEventListener('keydown', (event) => {
    const modal = document.getElementById('message-modal');
    if (modal && modal.style.display === 'block') {
      if (event.key === 'Escape') {
        modal.style.display = 'none';
      }
    }
  });
});