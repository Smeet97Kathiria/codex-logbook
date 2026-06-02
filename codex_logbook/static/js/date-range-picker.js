// Date Range Picker Component for Charts
// Provides a reusable date picker that limits selection to configurable day ranges

class DateRangePicker {
  constructor(options) {
    this.containerId = options.containerId;
    this.onRangeChange = options.onRangeChange;
    this.minDate = options.minDate || null;
    this.maxDate = options.maxDate || new Date();
    this.defaultDays = options.defaultDays || 30;
    this.maxDays = options.maxDays || 30;
        
    // Initialize with last N days
    this.endDate = new Date();
    this.startDate = new Date();
    this.startDate.setDate(this.endDate.getDate() - (this.defaultDays - 1));
        
    this.render();
  }
    
  render() {
    const container = document.getElementById(this.containerId);
    if (!container) {return;}
        
    // Format dates for input fields
    const formatDate = (date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };
        
    container.innerHTML = `
            <div class="date-range-picker" id="${this.containerId}-picker">
                <div class="date-range-controls">
                    <div class="date-input-group">
                        <input type="date" 
                               id="${this.containerId}-start" 
                               value="${formatDate(this.startDate)}"
                               min="${this.minDate ? formatDate(this.minDate) : ''}"
                               max="${formatDate(this.maxDate)}">
                    </div>
                    <div class="date-input-group">
                        <label>To:</label>
                        <input type="date" 
                               id="${this.containerId}-end" 
                               value="${formatDate(this.endDate)}"
                               min="${this.minDate ? formatDate(this.minDate) : ''}"
                               max="${formatDate(this.maxDate)}">
                    </div>
                    <button class="date-range-apply" onclick="window.dateRangePickers['${this.containerId}'].applyRange()">
                        Apply
                    </button>
                    <button class="date-range-preset" onclick="window.dateRangePickers['${this.containerId}'].setLast30Days()">
                        Reset
                    </button>
                </div>
                <div class="date-range-info">
                    <span id="${this.containerId}-info"></span>
                </div>
            </div>
        `;
        
    // Store reference for onclick handlers
    if (!window.dateRangePickers) {window.dateRangePickers = {};}
    window.dateRangePickers[this.containerId] = this;
        
    // Add change listeners
    const startInput = document.getElementById(`${this.containerId}-start`);
    const endInput = document.getElementById(`${this.containerId}-end`);
        
    startInput.addEventListener('change', () => this.validateRange());
    endInput.addEventListener('change', () => this.validateRange());
        
    this.updateInfo();
    this.checkResponsiveLayout();
    
    // Add resize observer to handle dynamic resizing
    if (window.ResizeObserver) {
      const picker = document.getElementById(`${this.containerId}-picker`);
      if (picker) {
        this.resizeObserver = new ResizeObserver(() => {
          this.checkResponsiveLayout();
        });
        this.resizeObserver.observe(picker);
      }
    }
  }
    
  validateRange() {
    // Just update the info display, don't auto-adjust dates
    this.updateInfo();
  }
    
  formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
    
  updateInfo() {
    const startInput = document.getElementById(`${this.containerId}-start`);
    const endInput = document.getElementById(`${this.containerId}-end`);
    const infoSpan = document.getElementById(`${this.containerId}-info`);
        
    if (!startInput || !endInput || !infoSpan) {return;}
        
    const start = new Date(startInput.value);
    const end = new Date(endInput.value);
    const diffDays = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
        
    infoSpan.textContent = `${diffDays} day${diffDays !== 1 ? 's' : ''} selected`;
        
    if (diffDays > this.maxDays) {
      infoSpan.style.color = '#e53e3e';
      infoSpan.textContent += ` (max ${this.maxDays} days)`;
    } else {
      infoSpan.style.color = '#7A6549';
    }
    
    // Check if we need to adjust layout after updating info
    this.checkResponsiveLayout();
  }
  
  checkResponsiveLayout() {
    const picker = document.getElementById(`${this.containerId}-picker`);
    if (!picker) {return;}
    
    const controls = picker.querySelector('.date-range-controls');
    const info = picker.querySelector('.date-range-info');
    if (!controls || !info) {return;}
    
    // Temporarily remove stacked class to measure natural width
    const wasStacked = picker.classList.contains('date-range-picker-stacked');
    picker.classList.remove('date-range-picker-stacked');
    
    // Get the actual widths
    const controlsWidth = controls.scrollWidth;
    const infoWidth = info.scrollWidth;
    const containerWidth = picker.clientWidth;
    const padding = 20; // Account for padding/margins
    
    // Check if both elements can fit on the same line with some breathing room
    const totalNeededWidth = controlsWidth + infoWidth + padding;
    
    // Stack if there's not enough room or if container is very narrow
    if (totalNeededWidth > containerWidth || containerWidth < 500) {
      picker.classList.add('date-range-picker-stacked');
    } else if (wasStacked && totalNeededWidth < containerWidth * 0.9) {
      // Only unstack if there's definitely enough room (hysteresis to prevent flashing)
      picker.classList.remove('date-range-picker-stacked');
    } else if (wasStacked) {
      // Keep the previous state if we're in the gray zone
      picker.classList.add('date-range-picker-stacked');
    }
  }
    
  applyRange() {
    const startInput = document.getElementById(`${this.containerId}-start`);
    const endInput = document.getElementById(`${this.containerId}-end`);
    const infoSpan = document.getElementById(`${this.containerId}-info`);
        
    if (!startInput || !endInput) {return;}
        
    // Validate dates before applying
    const start = new Date(startInput.value);
    const end = new Date(endInput.value);
        
    // Check if end is before start
    if (end < start) {
      infoSpan.textContent = 'End date must be after start date';
      infoSpan.style.color = '#e53e3e';
      return;
    }
        
    // Check if range exceeds max days
    const diffDays = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
    if (diffDays > this.maxDays) {
      infoSpan.textContent = `${diffDays} days selected (max ${this.maxDays} days allowed)`;
      infoSpan.style.color = '#e53e3e';
      return;
    }
        
    // Store Date objects for internal use (like setLast30Days)
    this.startDate = start;
    this.endDate = end;
        
    // Call the callback with the string values directly to avoid timezone issues
    if (this.onRangeChange) {
      this.onRangeChange({
        startDate: startInput.value,  // Already in YYYY-MM-DD format
        endDate: endInput.value        // Already in YYYY-MM-DD format
      });
    }
        
    // Reset the info color to normal after successful apply
    this.updateInfo();
  }
    
  setLast30Days() {
    this.endDate = new Date();
    this.startDate = new Date();
    this.startDate.setDate(this.endDate.getDate() - 29);
        
    // Update inputs
    const startInput = document.getElementById(`${this.containerId}-start`);
    const endInput = document.getElementById(`${this.containerId}-end`);
        
    if (startInput && endInput) {
      startInput.value = this.formatDateForInput(this.startDate);
      endInput.value = this.formatDateForInput(this.endDate);
      this.updateInfo();
      this.applyRange();
    }
  }
    
  formatDateForAPI(date) {
    // Return YYYY-MM-DD format for API
    return this.formatDateForInput(date);
  }
    
  getDateRange() {
    return {
      startDate: this.formatDateForAPI(this.startDate),
      endDate: this.formatDateForAPI(this.endDate)
    };
  }
  
  destroy() {
    // Clean up resize observer when component is destroyed
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
  }
}