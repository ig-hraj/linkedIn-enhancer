/**
 * analysis.js — Analysis Results Display
 * 
 * Handles rendering the AI analysis results including:
 *  - Overall score circle
 *  - Section score cards
 *  - Priority actions
 *  - Keyword suggestions
 *  - Rewrite functionality
 */

// ============================================================
// Render Full Analysis
// ============================================================
function renderAnalysis(result) {
    const analysis = result.analysis;
    const completeness = result.completeness;

    // Hide empty state
    document.getElementById("no-analysis").style.display = "none";

    // Render overall score
    renderOverallScore(analysis.overall_score, completeness);

    // Render section cards
    renderSectionScores(analysis.sections);

    // Render priorities and keywords
    renderPriorities(analysis.top_3_priorities, analysis.keyword_suggestions);
}

/**
 * Render only completeness score (fallback when AI fails).
 */
function renderCompletenessOnly(completeness) {
    document.getElementById("no-analysis").style.display = "none";

    const container = document.getElementById("overall-score-container");
    const scoreClass = getScoreClass(completeness.percentage);

    container.innerHTML = `
        <div class="score-circle ${scoreClass}">
            <span class="score-number">${completeness.percentage}</span>
            <span class="score-label">/ 100</span>
        </div>
        <div class="score-level">${completeness.level} Profile</div>
        <p style="color: var(--text-secondary); margin-top: 0.5rem;">
            Completeness score (AI deep analysis unavailable)
        </p>
    `;

    document.getElementById("section-scores-container").innerHTML = "";
    document.getElementById("priorities-container").innerHTML = `
        <h3>⚠️ AI Analysis Unavailable</h3>
        <p>The detailed AI analysis couldn't be completed. Please check your API key and try again.</p>
    `;
}

// ============================================================
// Overall Score
// ============================================================
function renderOverallScore(score, completeness) {
    const container = document.getElementById("overall-score-container");
    const scoreClass = getScoreClass(score);
    const level = completeness ? completeness.level : getLevel(score);

    container.innerHTML = `
        <div class="score-circle ${scoreClass}">
            <span class="score-number">${score}</span>
            <span class="score-label">/ 100</span>
        </div>
        <div class="score-level">${level} Profile</div>
        <p style="color: var(--text-secondary); margin-top: 0.5rem;">
            ${getScoreMessage(score)}
        </p>
    `;
}

// ============================================================
// Section Score Cards
// ============================================================
function renderSectionScores(sections) {
    const container = document.getElementById("section-scores-container");
    container.innerHTML = "";

    const sectionConfig = {
        headline: { icon: "fas fa-heading", label: "Headline" },
        summary: { icon: "fas fa-align-left", label: "Summary / About" },
        experience: { icon: "fas fa-briefcase", label: "Experience" },
        skills: { icon: "fas fa-tools", label: "Skills" }
    };

    for (const [key, data] of Object.entries(sections)) {
        const config = sectionConfig[key] || { icon: "fas fa-star", label: key };
        const scoreClass = getScoreClass(data.score * 10);

        let card = `
            <div class="score-card">
                <div class="score-card-header">
                    <h3><i class="${config.icon}"></i> ${config.label}</h3>
                    <span class="score-badge ${scoreClass}">${data.score}/10</span>
                </div>

                <div class="score-bar">
                    <div class="score-bar-fill ${scoreClass}" 
                         style="width: ${data.score * 10}%; background: ${getScoreColor(data.score * 10)};"></div>
                </div>

                <p class="assessment">${data.current_assessment}</p>
        `;

        // Issues
        if (data.issues && data.issues.length > 0) {
            card += `<div class="card-section-title">Issues Found</div><ul class="issues-list">`;
            data.issues.forEach(issue => {
                card += `<li>${issue}</li>`;
            });
            card += `</ul>`;
        }

        // Suggestions
        if (data.suggestions && data.suggestions.length > 0) {
            card += `<div class="card-section-title">Suggestions</div><ul class="suggestions-list">`;
            data.suggestions.forEach(suggestion => {
                card += `<li>${suggestion}</li>`;
            });
            card += `</ul>`;
        }

        // Recommended skills (skills section only)
        if (data.recommended_skills && data.recommended_skills.length > 0) {
            card += `<div class="card-section-title">Recommended Skills to Add</div>
                     <div class="keywords-container">`;
            data.recommended_skills.forEach(skill => {
                card += `<span class="keyword-chip">${skill}</span>`;
            });
            card += `</div>`;
        }

        card += `</div>`;
        container.innerHTML += card;
    }
}

// ============================================================
// Priorities & Keywords
// ============================================================
function renderPriorities(priorities, keywords) {
    const container = document.getElementById("priorities-container");

    let html = `<h3>🎯 Top 3 Priority Actions</h3>`;

    if (priorities && priorities.length > 0) {
        html += `<ol>`;
        priorities.forEach(p => {
            html += `<li>${p}</li>`;
        });
        html += `</ol>`;
    }

    if (keywords && keywords.length > 0) {
        html += `<div class="card-section-title" style="margin-top:1rem;">🔑 Suggested Keywords for Your Profile</div>
                 <div class="keywords-container">`;
        keywords.forEach(kw => {
            html += `<span class="keyword-chip">${kw}</span>`;
        });
        html += `</div>`;
    }

    container.innerHTML = html;
}

// ============================================================
// Rewrite Section Handler
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("rewrite-btn").addEventListener("click", handleRewrite);
});

async function handleRewrite() {
    const section = document.getElementById("rewrite-select").value;
    const currentContent = document.getElementById("rewrite-current").value.trim();

    if (!currentContent) {
        showToast("❌ Please enter the content you want to rewrite.", true);
        return;
    }

    // Build context from stored profile data
    const context = {};
    if (currentProfileData) {
        context.industry = currentProfileData.industry || "";
        context.target_role = currentProfileData.target_role || "";
        context.experience_years = currentProfileData.experience
            ? `${currentProfileData.experience.length}+ positions`
            : "Not specified";
        context.key_skills = currentProfileData.skills || [];
    }

    showLoading("Generating improved versions...");

    try {
        const response = await fetch(`${API_BASE}/api/rewrite`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                section: section,
                current_content: currentContent,
                context: context
            })
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            renderRewrites(result.rewrites);
            showToast("✅ Rewrite options generated!");
        } else {
            showToast(`❌ ${result.error}`, true);
        }
    } catch (err) {
        hideLoading();
        console.error("Rewrite error:", err);
        showToast("❌ Failed to generate rewrites. Check server connection.", true);
    }
}

function renderRewrites(data) {
    const container = document.getElementById("rewrite-results");
    container.innerHTML = "";

    if (data.versions && data.versions.length > 0) {
        data.versions.forEach((version, index) => {
            const card = document.createElement("div");
            card.className = "rewrite-card";
            card.innerHTML = `
                <div class="rewrite-card-header">
                    <span class="rewrite-style">${index + 1}. ${version.style}</span>
                    <span class="rewrite-char-count">${version.character_count || version.content.length} chars</span>
                </div>
                <div class="rewrite-content">${escapeHtml(version.content)}</div>
                <ul class="rewrite-improvements">
                    ${(version.key_improvements || []).map(imp => `<li>${imp}</li>`).join("")}
                </ul>
                <button class="btn-copy" onclick="copyToClipboard(this, '${escapeForAttr(version.content)}')">
                    <i class="fas fa-copy"></i> Copy to Clipboard
                </button>
            `;
            container.appendChild(card);
        });
    }

    // Optimization tips
    if (data.optimization_tips && data.optimization_tips.length > 0) {
        const tips = document.createElement("div");
        tips.className = "optimization-tips";
        tips.innerHTML = `
            <h4>💡 Optimization Tips</h4>
            <ul>
                ${data.optimization_tips.map(tip => `<li>${tip}</li>`).join("")}
            </ul>
        `;
        container.appendChild(tips);
    }
}

// ============================================================
// Utility Functions
// ============================================================
function getScoreClass(score) {
    if (score >= 80) return "score-excellent";
    if (score >= 60) return "score-good";
    if (score >= 40) return "score-average";
    return "score-poor";
}

function getScoreColor(score) {
    if (score >= 80) return "var(--score-excellent)";
    if (score >= 60) return "var(--score-good)";
    if (score >= 40) return "var(--score-average)";
    return "var(--score-poor)";
}

function getLevel(score) {
    if (score >= 80) return "All-Star";
    if (score >= 60) return "Advanced";
    if (score >= 40) return "Intermediate";
    return "Beginner";
}

function getScoreMessage(score) {
    if (score >= 80) return "Excellent! Your profile is highly optimized. Fine-tune the details below.";
    if (score >= 60) return "Good foundation! A few improvements can make your profile stand out even more.";
    if (score >= 40) return "Decent start, but significant improvements are needed to attract recruiters.";
    return "Your profile needs substantial work. Follow the suggestions below to transform it.";
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function escapeForAttr(text) {
    return text.replace(/'/g, "\\'").replace(/"/g, "&quot;").replace(/\n/g, "\\n");
}

function copyToClipboard(btn, text) {
    const decoded = text.replace(/\\n/g, "\n").replace(/&quot;/g, '"').replace(/\\'/g, "'");
    navigator.clipboard.writeText(decoded).then(() => {
        const original = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        btn.style.background = "var(--score-excellent)";
        btn.style.color = "white";
        setTimeout(() => {
            btn.innerHTML = original;
            btn.style.background = "";
            btn.style.color = "";
        }, 2000);
    }).catch(() => {
        showToast("❌ Failed to copy. Please select and copy manually.", true);
    });
}
