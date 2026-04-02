/**
 * app.js — Main Application Logic
 * 
 * Handles:
 *  - Tab navigation
 *  - Profile form management
 *  - Form submission and API calls
 *  - Sample profile loading
 *  - Experience entry management
 *  - Character counters
 */

// ============================================================
// Configuration
// ============================================================
const API_BASE = window.location.origin;

// Global state — stores profile data for use across tabs
let currentProfileData = null;

// ============================================================
// DOM Ready
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    initTabNavigation();
    initFormHandlers();
    initCharCounters();
    addExperienceEntry(); // Start with one empty experience entry
});

// ============================================================
// Tab Navigation
// ============================================================
function initTabNavigation() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");

            // Remove active from all
            tabButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            // Activate clicked tab
            btn.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
        });
    });
}

// ============================================================
// Form Handlers
// ============================================================
function initFormHandlers() {
    // Load sample profile
    document.getElementById("load-sample-btn").addEventListener("click", loadSampleProfile);

    // Clear form
    document.getElementById("clear-form-btn").addEventListener("click", clearForm);

    // Add experience entry
    document.getElementById("add-experience-btn").addEventListener("click", addExperienceEntry);

    // Form submission
    document.getElementById("profile-form").addEventListener("submit", handleFormSubmit);
}

/**
 * Load a sample LinkedIn profile from the API for testing.
 */
async function loadSampleProfile() {
    try {
        const res = await fetch(`${API_BASE}/api/sample-profile`);
        const sample = await res.json();

        // Fill form fields
        document.getElementById("name").value = sample.name || "";
        document.getElementById("headline").value = sample.headline || "";
        document.getElementById("summary").value = sample.summary || "";
        document.getElementById("industry").value = sample.industry || "";
        document.getElementById("target_role").value = sample.target_role || "";
        document.getElementById("skills").value = (sample.skills || []).join(", ");

        // Clear existing experience entries
        document.getElementById("experience-container").innerHTML = "";

        // Add experience entries from sample
        if (sample.experience && sample.experience.length > 0) {
            sample.experience.forEach(exp => {
                addExperienceEntry(exp);
            });
        } else {
            addExperienceEntry();
        }

        // Update character counters
        updateCharCount("headline", 220);
        updateCharCount("summary", 2600);

        showToast("✅ Sample profile loaded! Click 'Analyze My Profile' to see results.");
    } catch (err) {
        console.error("Error loading sample:", err);
        showToast("❌ Failed to load sample profile.", true);
    }
}

/**
 * Clear all form fields.
 */
function clearForm() {
    document.getElementById("profile-form").reset();
    document.getElementById("experience-container").innerHTML = "";
    addExperienceEntry();
    updateCharCount("headline", 220);
    updateCharCount("summary", 2600);
    currentProfileData = null;
    showToast("🧹 Form cleared.");
}

/**
 * Add an experience entry to the form.
 * @param {Object} data - Optional pre-filled data
 */
function addExperienceEntry(data = null) {
    const container = document.getElementById("experience-container");
    const index = container.children.length;

    const entry = document.createElement("div");
    entry.className = "experience-entry";
    entry.innerHTML = `
        <button type="button" class="remove-exp-btn" onclick="this.parentElement.remove()" title="Remove">
            <i class="fas fa-times"></i>
        </button>
        <div class="exp-row">
            <div class="form-group">
                <label>Job Title</label>
                <input type="text" name="exp_title_${index}" 
                       placeholder="e.g., Software Engineer"
                       value="${data ? data.title || '' : ''}">
            </div>
            <div class="form-group">
                <label>Company</label>
                <input type="text" name="exp_company_${index}" 
                       placeholder="e.g., Google"
                       value="${data ? data.company || '' : ''}">
            </div>
        </div>
        <div class="form-group">
            <label>Duration</label>
            <input type="text" name="exp_duration_${index}" 
                   placeholder="e.g., Jan 2020 - Present"
                   value="${data ? data.duration || '' : ''}">
        </div>
        <div class="form-group">
            <label>Description</label>
            <textarea name="exp_desc_${index}" rows="3"
                      placeholder="Describe your achievements, responsibilities, and impact...">${data ? data.description || '' : ''}</textarea>
        </div>
    `;

    container.appendChild(entry);
}

/**
 * Collect all form data into a structured profile object.
 * @returns {Object} Profile data
 */
function collectFormData() {
    const name = document.getElementById("name").value.trim();
    const headline = document.getElementById("headline").value.trim();
    const summary = document.getElementById("summary").value.trim();
    const industry = document.getElementById("industry").value.trim();
    const targetRole = document.getElementById("target_role").value.trim();
    const skillsRaw = document.getElementById("skills").value.trim();

    // Parse skills from comma-separated string
    const skills = skillsRaw
        ? skillsRaw.split(",").map(s => s.trim()).filter(s => s.length > 0)
        : [];

    // Collect experience entries
    const experience = [];
    const entries = document.querySelectorAll(".experience-entry");
    entries.forEach((entry, i) => {
        const title = entry.querySelector(`[name="exp_title_${i}"]`)?.value.trim() ||
                      entry.querySelector('input[name^="exp_title"]')?.value.trim() || "";
        const company = entry.querySelector(`[name="exp_company_${i}"]`)?.value.trim() ||
                        entry.querySelector('input[name^="exp_company"]')?.value.trim() || "";
        const duration = entry.querySelector(`[name="exp_duration_${i}"]`)?.value.trim() ||
                         entry.querySelector('input[name^="exp_duration"]')?.value.trim() || "";
        const description = entry.querySelector(`[name="exp_desc_${i}"]`)?.value.trim() ||
                            entry.querySelector('textarea[name^="exp_desc"]')?.value.trim() || "";

        if (title || company || description) {
            experience.push({ title, company, duration, description });
        }
    });

    return {
        name,
        headline,
        summary,
        industry,
        target_role: targetRole,
        skills,
        experience
    };
}

/**
 * Handle form submission — send profile to API for analysis.
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    const profileData = collectFormData();

    // Basic validation
    if (!profileData.name || !profileData.headline) {
        showToast("❌ Please fill in at least your Name and Headline.", true);
        return;
    }

    // Store globally for chatbot and rewrite tabs
    currentProfileData = profileData;

    // Show loading overlay
    showLoading("Analyzing your profile with AI...");

    try {
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(profileData)
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            // Render analysis results
            renderAnalysis(result);

            // Auto-populate rewrite tab with headline
            document.getElementById("rewrite-current").value = profileData.headline;

            // Switch to analysis tab
            document.querySelector('[data-tab="analysis-results"]').click();

            showToast("✅ Analysis complete! Check your results.");
        } else {
            // Partial results (completeness score only)
            if (result.completeness) {
                renderCompletenessOnly(result.completeness);
                document.querySelector('[data-tab="analysis-results"]').click();
                showToast("⚠️ AI analysis failed, but completeness score is available.", true);
            } else {
                showToast(`❌ Error: ${result.error}`, true);
            }
        }
    } catch (err) {
        hideLoading();
        console.error("Analysis error:", err);
        showToast("❌ Failed to connect to server. Make sure the backend is running.", true);
    }
}

// ============================================================
// Character Counters
// ============================================================
function initCharCounters() {
    const headline = document.getElementById("headline");
    const summary = document.getElementById("summary");

    headline.addEventListener("input", () => updateCharCount("headline", 220));
    summary.addEventListener("input", () => updateCharCount("summary", 2600));
}

function updateCharCount(fieldId, maxLen) {
    const field = document.getElementById(fieldId);
    const counter = document.getElementById(`${fieldId}-count`);
    if (field && counter) {
        const len = field.value.length;
        counter.textContent = `${len}/${maxLen}`;
        counter.style.color = len > maxLen * 0.9 ? "var(--score-poor)" : "var(--text-muted)";
    }
}

// ============================================================
// UI Utilities
// ============================================================
function showLoading(text = "Processing...") {
    document.getElementById("loading-text").textContent = text;
    document.getElementById("loading-overlay").classList.remove("hidden");
}

function hideLoading() {
    document.getElementById("loading-overlay").classList.add("hidden");
}

/**
 * Show a toast notification at the top of the page.
 */
function showToast(message, isError = false) {
    // Remove existing toasts
    document.querySelectorAll(".toast-notification").forEach(t => t.remove());

    const toast = document.createElement("div");
    toast.className = `toast-notification ${isError ? "toast-error" : "toast-success"}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 1rem;
        left: 50%;
        transform: translateX(-50%);
        padding: 0.85rem 1.5rem;
        border-radius: 8px;
        font-family: var(--font);
        font-size: 0.9rem;
        font-weight: 500;
        z-index: 2000;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        animation: toastSlide 0.3s ease;
        background: ${isError ? '#cc1016' : '#057642'};
        color: white;
        max-width: 90vw;
        text-align: center;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.3s";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
