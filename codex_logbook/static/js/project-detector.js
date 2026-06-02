// Project detector for handling project-specific URLs
(function() {
  'use strict';
    
  // Extract project from URL if present
  window.detectProjectFromURL = function() {
    const path = window.location.pathname;
    const projectMatch = path.match(/^\/project\/(.+)$/);
        
    if (projectMatch) {
      const projectDirName = projectMatch[1];
      return projectDirName;
    }
        
    return null;
  };
    
  // Set project based on URL detection
  window.setProjectFromURL = async function() {
    const projectDirName = detectProjectFromURL();
        
    if (!projectDirName) {
      return false;
    }
        
    try {
      // Call the API to set the project
      const response = await fetch('/api/project-by-dir', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ dir_name: projectDirName })
      });
            
      if (!response.ok) {
        const error = await response.json();
        console.error('[ProjectDetector] Failed to set project:', error);
        showError(`Failed to load project: ${error.detail || 'Unknown error'}`);
        return false;
      }
            
      const data = await response.json();
            
      // Update the UI to show the project name
      const projectInfo = document.getElementById('project-info-text');
      if (projectInfo) {
        projectInfo.textContent = `Project: ${data.log_dir_name.replace(/-/g, '/')}`;
      }
            
      return true;
    } catch (error) {
      console.error('[ProjectDetector] Error setting project:', error);
      showError('Failed to load project');
      return false;
    }
  };
    
  // Show error message
  function showError(message) {
    const statsGrid = document.getElementById('overview-stats');
    if (statsGrid) {
      statsGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: #d32f2f;">
                    <h2>Error</h2>
                    <p>${message}</p>
                    <a href="/" style="color: #EB6A1C;">Go to Overview</a>
                </div>
            `;
    }
  }
    
  // Add navigation helper
  window.navigateToOverview = function() {
    window.location.href = '/';
  };
    
  // populateProjectSelector is now handled by the main dashboard code
  // We just need a helper to navigate using project URLs
    
  // Navigate to a project-specific URL
  window.navigateToProject = function(dirName) {
    if (dirName) {
      window.location.href = `/project/${dirName}`;
    }
  };
})();