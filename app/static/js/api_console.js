// Helper functions
function handleResponse(response) {
    if (!response.ok) throw new Error('Network response was not ok');
    return response.json();
}

function handleError(error) {
    console.error('Error:', error);
    alert('Operation failed. See console for details.');
}

function loadConfig(configId) {
    if (!configId) {
        document.getElementById('selected_config_id').value = '';
        document.getElementById('selected_config_name').value = 'None (using default)';
        return;
    }

    const select = document.getElementById('configSelect');
    const originalText = select.selectedOptions[0].text;
    select.disabled = true;
    select.selectedOptions[0].text = 'Loading...';

    fetch(`/api/get_config?config_id=${configId}`)
        .then(handleResponse)
        .then(data => {
            if (data.config) {
                updateConfigForm(data.config);
            }
        })
        .catch(handleError)
        .finally(() => {
            select.disabled = false;
            select.selectedOptions[0].text = originalText;
        });
}

function updateConfigForm(config) {
    document.getElementById('name').value = config.name;
    document.getElementById('base_url').value = config.base_url;
    document.getElementById('secret_key').value = config.secret_key;
    document.getElementById('verify_ssl').checked = config.verify_ssl;
    document.getElementById('is_default').checked = config.is_default;
    document.querySelector('input[name="config_id"]').value = config.id;
    document.getElementById('selected_config_id').value = config.id;
    document.getElementById('selected_config_name').value = config.name;
}

function updateFormFields() {
    const method = document.getElementById('api_method').value;
    document.getElementById('crew_info_fields').style.display =
        method === 'get_crew_info' ? 'block' : 'none';

    const orderStateFields = document.getElementById('change_order_state_fields');
    orderStateFields.style.display = method === 'change_order_state' ? 'block' : 'none';

    if (method === 'change_order_state') {
        loadOrderStates();
    }
}

function loadOrderStates() {
    const newStateSelect = document.getElementById('new_state');
    newStateSelect.innerHTML = '<option value="" class="loading">Loading states...</option>';
    newStateSelect.disabled = true;

    fetch(`/api/api_console?form_type=load_states`)
        .then(handleResponse)
        .then(data => {
            newStateSelect.innerHTML = '<option value="">Select state...</option>';
            if (data.states?.length) {
                data.states.forEach(state => {
                    const option = new Option(`${state.id} - ${state.name}`, state.id);
                    newStateSelect.add(option);
                });
            }
        })
        .catch(error => {
            newStateSelect.innerHTML = '<option value="">Error loading states</option>';
            console.error('Error loading states:', error);
        })
        .finally(() => {
            newStateSelect.disabled = false;
        });
}

function switchView(viewType) {
    const jsonView = document.getElementById('jsonView');
    const tableView = document.getElementById('tableView');
    const jsonBtn = document.getElementById('jsonViewBtn');
    const tableBtn = document.getElementById('tableViewBtn');

    if (viewType === 'json') {
        jsonView.style.display = 'block';
        tableView.style.display = 'none';
        jsonBtn.classList.add('active');
        tableBtn.classList.remove('active');
    } else {
        jsonView.style.display = 'none';
        tableView.style.display = 'block';
        jsonBtn.classList.remove('active');
        tableBtn.classList.add('active');
    }
}

function copyToClipboard() {
    navigator.clipboard.writeText(document.querySelector('pre').innerText)
        .then(() => {
            const toast = new bootstrap.Toast(document.getElementById('copyToast'));
            toast.show();
        });
}

function initEventListeners() {
    // View switcher
    document.getElementById('jsonViewBtn')?.addEventListener('click', () => switchView('json'));
    document.getElementById('tableViewBtn')?.addEventListener('click', () => switchView('table'));

    // Copy button
    document.getElementById('copyButton')?.addEventListener('click', copyToClipboard);

    // API method selector
    document.getElementById('api_method')?.addEventListener('change', updateFormFields);

    // Config selector
    document.getElementById('configSelect')?.addEventListener('change', (e) => loadConfig(e.target.value));
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initEventListeners();
    updateFormFields();
});