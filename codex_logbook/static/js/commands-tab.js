/**
 * Commands Tab Module
 * Handles all functionality for the User Commands tab in the dashboard
 */

// Module state variables
let commandsPage = 1;
let commandsPerPage = DEFAULT_COMMANDS_PER_PAGE;
let commandDetails = [];
let originalCommandDetails = [];
let commandsSortColumn = 'timestamp';
let commandsSortDirection = 'desc';

// Initialize the Commands table
function initializeCommandsTable() {
  // Get command details from statistics
  if (statistics.user_interactions && statistics.user_interactions.command_details) {
    originalCommandDetails = statistics.user_interactions.command_details;
    commandDetails = [...originalCommandDetails];
    window.userCommands = originalCommandDetails;  // Make available globally for sharing
        
    // Sort by default (timestamp desc)
    sortCommandsData();
        
    // Update summary
    const summary = statistics.user_interactions;
        
    // Calculate interruption counts
    const interruptions = commandDetails.filter(cmd => 
      isInterruptionMessage(cmd.user_message)
    ).length;
    const regularCommands = commandDetails.length - interruptions;
        
    document.getElementById('commands-summary').innerHTML = `
            <div class="commands-summary-content">
                <div class="commands-summary-line">
                    <strong>${commandDetails.length}</strong> total
                    (<strong>${regularCommands}</strong> commands, <strong>${interruptions}</strong> interruptions)
                </div>
                <div class="commands-summary-line">
                    ${summary.percentage_requiring_tools}% use tools
                    • Avg ${summary.avg_steps_per_command} steps/command
                    • Avg ${summary.avg_tools_when_used} tools when used
                </div>
            </div>
        `;
        
    // Display the table
    displayCommandsPage();
        
    // Show pagination if needed
    if (commandDetails.length > commandsPerPage) {
      document.getElementById('commands-pagination').style.display = 'flex';
    }
  } else {
    // Hide the commands section if no data
    document.querySelector('.user-commands-section').style.display = 'none';
  }
}

// Filter commands based on search and interrupted status
function filterCommands() {
  const searchTerm = document.getElementById('commands-search').value.toLowerCase();
  const interruptedFilter = document.getElementById('commands-interrupted-filter').value;
    
  // Filter the original data
  commandDetails = originalCommandDetails.filter(cmd => {
    // Search filter
    if (searchTerm && !cmd.user_message.toLowerCase().includes(searchTerm)) {
      return false;
    }
        
    // Interrupted filter
    if (interruptedFilter) {
      if (interruptedFilter === 'yes' && !cmd.followed_by_interruption) {
        return false;
      }
      if (interruptedFilter === 'no' && cmd.followed_by_interruption) {
        return false;
      }
    }
        
    return true;
  });
    
  // Reset to first page
  commandsPage = 1;
    
  // Re-sort the filtered data
  sortCommandsData();
    
  // Update display
  displayCommandsPage();
    
  // Update pagination visibility
  const paginationElement = document.getElementById('commands-pagination');
  if (commandDetails.length > commandsPerPage) {
    paginationElement.style.display = 'flex';
  } else {
    paginationElement.style.display = 'none';
  }
}

// Display the current page of commands
function displayCommandsPage() {
  const start = (commandsPage - 1) * commandsPerPage;
  const end = start + commandsPerPage;
  const pageCommands = commandDetails.slice(start, end);
    
  const tbody = document.getElementById('commands-tbody');
  tbody.innerHTML = pageCommands.map((cmd, index) => {
    // Create compact tool names display
    let toolNamesDisplay = '';
    const actualIndex = start + index;
        
    if (cmd.tool_names.length > 0) {
      const uniqueTools = [...new Set(cmd.tool_names)];
      const toolCounts = {};
      cmd.tool_names.forEach(tool => {
        toolCounts[tool] = (toolCounts[tool] || 0) + 1;
      });
            
      if (uniqueTools.length <= 3) {
        // Show all tools with counts if repeated
        toolNamesDisplay = uniqueTools.map(tool => {
          const count = toolCounts[tool];
          return count > 1 ? `${tool}(${count})` : tool;
        }).join(', ');
        toolNamesDisplay = `<span style="font-size: 0.85rem; color: #7A6549;" title="${cmd.tool_names.join(', ')}">${toolNamesDisplay}</span>`;
      } else {
        // Show first 2 tools and clickable count of others
        const firstTwo = uniqueTools.slice(0, 2).map(tool => {
          const count = toolCounts[tool];
          return count > 1 ? `${tool}(${count})` : tool;
        }).join(', ');
        const moreCount = uniqueTools.length - 2;
        toolNamesDisplay = `<span style="font-size: 0.85rem; color: #7A6549;">
                    ${firstTwo}, 
                    <a href="#" onclick="showAllTools(${actualIndex}); return false;" 
                       style="color: #EB6A1C; text-decoration: underline; cursor: pointer;"
                       title="Click to see all tools">+${moreCount} more</a>
                </span>`;
      }
    } else {
      toolNamesDisplay = '<span style="color: #999;">-</span>';
    }
        
    return `
        <tr onclick="showCommandDetail(${actualIndex})" style="cursor: pointer;">
            <td style="overflow: hidden; max-width: 300px;">
                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; word-break: break-all;" 
                     title="${escapeHtml(cmd.user_message)}">
                    ${escapeHtml(cmd.user_message_truncated || cmd.user_message)}
                </div>
            </td>
            <td style="font-size: 0.9rem;">${formatTimestamp(cmd.timestamp)}</td>
            <td style="font-size: 0.85rem;">
                ${cmd.model && cmd.model !== 'N/A' ? 
    formatModelName(cmd.model) : 
    '<span style="color: #999;">-</span>'}
            </td>
            <td style="text-align: center;">${cmd.assistant_steps}</td>
            <td style="text-align: center;">
                ${cmd.tools_used > 0 ? 
    `<span style="color: #EB6A1C; font-weight: bold;">${cmd.tools_used}</span>` : 
    '<span style="color: #999;">0</span>'}
            </td>
            <td style="text-align: center;">
                ${cmd.is_interruption ? '-' : (cmd.estimated_tokens ? cmd.estimated_tokens.toFixed(0) : '-')}
            </td>
            <td style="text-align: center;">
                ${cmd.followed_by_interruption ? 
    '<span style="color: #d32f2f; font-weight: bold;" title="This command was followed by a user interruption">Yes</span>' : 
    '<span style="color: #999;">-</span>'}
            </td>
            <td style="font-size: 0.85rem;">
                ${toolNamesDisplay}
            </td>
        </tr>
    `;
  }).join('');
    
  // Update pagination
  const totalPages = Math.ceil(commandDetails.length / commandsPerPage);
  document.getElementById('commands-total-pages').textContent = totalPages;
  document.getElementById('commands-page-input').value = commandsPage;
  document.getElementById('commands-prev-btn').disabled = commandsPage === 1;
  document.getElementById('commands-next-btn').disabled = commandsPage === totalPages;
    
  // Update sort indicators on first load
  updateCommandsSortIndicators();
}

// Change page by delta
function changeCommandsPage(delta) {
  const totalPages = Math.ceil(commandDetails.length / commandsPerPage);
  commandsPage = Math.max(1, Math.min(totalPages, commandsPage + delta));
  displayCommandsPage();
}

// Go to specific page from input
function goToCommandsPage() {
  const input = document.getElementById('commands-page-input');
  const totalPages = Math.ceil(commandDetails.length / commandsPerPage);
  commandsPage = Math.max(1, Math.min(totalPages, parseInt(input.value) || 1));
  displayCommandsPage();
}

// Update items per page
function updateCommandsPerPage() {
  const select = document.getElementById('commands-per-page');
  commandsPerPage = parseInt(select.value);
  commandsPage = 1; // Reset to first page
  displayCommandsPage();
}

// Show detailed view of a command
function showCommandDetail(index) {
  const cmd = commandDetails[index];
  if (!cmd) {return;}
    
  // Count tool occurrences
  const toolCounts = {};
  if (cmd.tool_names && cmd.tool_names.length > 0) {
    cmd.tool_names.forEach(tool => {
      toolCounts[tool] = (toolCounts[tool] || 0) + 1;
    });
  }
    
  // Create formatted list
  const toolsList = Object.entries(toolCounts)
    .sort((a, b) => b[1] - a[1]) // Sort by count descending
    .map(([tool, count]) => {
      const countText = count > 1 ? `<span style="color: #EB6A1C; font-weight: bold;">(${count}x)</span>` : '';
      return `<div style="padding: 0.5rem 0; border-bottom: 1px solid #eee;">
                <span style="font-size: 1rem;">${tool}</span> ${countText}
            </div>`;
    })
    .join('');
    
  // Use the existing modal
  const modal = document.getElementById('message-modal');
  const modalTitle = document.getElementById('modal-title');
  const modalBody = document.getElementById('modal-body');
    
  modalTitle.textContent = 'User Command Details';
  
  // Hide navigation for commands
  const modalNav = document.querySelector('.modal-navigation');
  if (modalNav) {
    modalNav.style.display = 'none';
  }
  
  // Trim each line while preserving line breaks
  const trimmedMessage = cmd.user_message
    .split('\n')
    .map(line => line.trim())
    .join('\n')
    .trim();
    
  modalBody.innerHTML = `
        <div style="margin-bottom: 1rem;">
            <div class="detail-content" style="margin-top: 0.5rem; white-space: pre-wrap; word-wrap: break-word;">
                ${escapeHtml(trimmedMessage)}
            </div>
        </div>
        <div style="margin-bottom: 1rem;">
            <strong>Timestamp:</strong> ${formatTimestamp(cmd.timestamp)}
        </div>
        <div style="margin-bottom: 1rem;">
            <strong>Assistant Steps:</strong> ${cmd.assistant_steps}
        </div>
        <div style="margin-bottom: 1rem;">
            <strong>Total Tool Calls:</strong> ${cmd.tools_used}
        </div>
        <div style="margin-bottom: 1rem;">
            <strong>Estimated Tokens:</strong> ${cmd.is_interruption ? '-' : (cmd.estimated_tokens ? cmd.estimated_tokens.toFixed(0) : '-')}
        </div>
        ${cmd.tools_used > 0 ? `
            <div style="margin-bottom: 1rem;">
                <strong>Tools Used:</strong>
            </div>
            <div style="max-height: 400px; overflow-y: auto;">
                ${toolsList}
            </div>
        ` : ''}
    `;
    
  modal.style.display = 'block';
}

// Show all tools (delegates to showCommandDetail)
function showAllTools(globalIndex) {
  showCommandDetail(globalIndex);
}

// Sort commands table by column
function sortCommandsTable(column) {
  if (commandsSortColumn === column) {
    // Toggle direction
    commandsSortDirection = commandsSortDirection === 'asc' ? 'desc' : 'asc';
  } else {
    // New column, default to appropriate direction
    commandsSortColumn = column;
    commandsSortDirection = column === 'timestamp' ? 'desc' : 'asc';
  }
    
  commandsPage = 1;
  sortCommandsData();
  displayCommandsPage();
  updateCommandsSortIndicators();
}

// Sort commands data
function sortCommandsData() {
  const columnConfig = {
    'user_message': (cmd) => cmd.user_message || '',
    'timestamp': (cmd) => cmd.timestamp || '',
    'model': (cmd) => cmd.model || '',
    'assistant_steps': (cmd) => cmd.assistant_steps || 0,
    'tools_used': (cmd) => cmd.tools_used || 0,
    'estimated_tokens': (cmd) => cmd.estimated_tokens || 0,
    'followed_by_interruption': (cmd) => cmd.followed_by_interruption ? 1 : 0
  };
    
  sortTableData(commandDetails, commandsSortColumn, commandsSortDirection, columnConfig);
}

// Update sort indicators for commands table
function updateCommandsSortIndicators() {
  // Clear all sort classes from commands table headers
  const commandsTable = document.querySelector('#commands-table');
  if (!commandsTable) {return;}
    
  commandsTable.querySelectorAll('th[onclick^="sortCommandsTable"]').forEach(th => {
    th.classList.remove('sort-asc', 'sort-desc');
    // Ensure sortable class is present
    th.classList.add('sortable');
  });
    
  // Also handle the div with onclick inside th for "Interrupted" column
  commandsTable.querySelectorAll('th div[onclick^="sortCommandsTable"]').forEach(div => {
    const th = div.closest('th');
    if (th) {
      th.classList.remove('sort-asc', 'sort-desc');
      th.classList.add('sortable');
    }
  });
    
  // Find and update the active column
  const headers = commandsTable.querySelectorAll('th[onclick^="sortCommandsTable"], th div[onclick^="sortCommandsTable"]');
  headers.forEach(element => {
    const onclickAttr = element.getAttribute('onclick');
    const match = onclickAttr.match(/sortCommandsTable\('([^']+)'\)/);
    if (match && match[1] === commandsSortColumn) {
      const th = element.tagName === 'TH' ? element : element.closest('th');
      if (th) {
        th.classList.add(commandsSortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
      }
    }
  });
}

// Navigation helper for "Go to row" functionality
function goToCommandRow() {
  goToRowInPaginatedTable({
    inputId: 'commands-row-input',
    dataArray: commandDetails,
    itemsPerPage: commandsPerPage,
    navigateFunction: (page) => {
      commandsPage = page;
      displayCommandsPage();
    },
    tbodySelector: '#commands-tbody'
  });
}

// Export commands to CSV
function exportCommandsToCSV() {
  const headers = ['User Command', 'Timestamp', 'Model', 'Steps', 'Tools Used', 'Tokens', 'Interrupted', 'Tool Names'];
    
  // Prepare data for export
  const data = commandDetails.map(cmd => {
    const toolNames = cmd.tool_names.join('; ');
    return [
      cmd.user_message,
      formatTimestamp(cmd.timestamp),
      cmd.model || '-',
      cmd.assistant_steps,
      cmd.tools_used,
      cmd.is_interruption ? '-' : (cmd.estimated_tokens ? cmd.estimated_tokens.toFixed(0) : '-'),
      cmd.followed_by_interruption ? 'Yes' : 'No',
      toolNames || '-'
    ];
  });
    
  const csvContent = exportToCSV(data, headers);
  const timestamp = new Date().toISOString().split('T')[0];
  downloadCSV(csvContent, `commands_export_${timestamp}.csv`);
}

// Export public functions to make them accessible globally
window.initializeCommandsTable = initializeCommandsTable;
window.filterCommands = filterCommands;
window.displayCommandsPage = displayCommandsPage;
window.changeCommandsPage = changeCommandsPage;
window.goToCommandsPage = goToCommandsPage;
window.updateCommandsPerPage = updateCommandsPerPage;
window.showCommandDetail = showCommandDetail;
window.showAllTools = showAllTools;
window.sortCommandsTable = sortCommandsTable;
window.goToCommandRow = goToCommandRow;
window.exportCommandsToCSV = exportCommandsToCSV;
