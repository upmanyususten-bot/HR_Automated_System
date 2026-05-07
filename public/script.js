const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const analyzeBtn = document.getElementById('analyzeBtn');
const resultsSection = document.getElementById('resultsSection');
const resultsList = document.getElementById('resultsList');
const jobDescription = document.getElementById('jobDescription');
const dropZone = document.getElementById('dropZone');

let uploadedFiles = [];

// Handle file selection
fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

// Drag and Drop
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--primary)';
});

dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = 'var(--glass-border)';
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
});

function handleFiles(files) {
    uploadedFiles = Array.from(files);
    fileList.innerHTML = '';
    uploadedFiles.forEach(file => {
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `<span><i class="far fa-file-alt"></i> ${file.name}</span><span>${(file.size / 1024).toFixed(1)} KB</span>`;
        fileList.appendChild(div);
    });
}

analyzeBtn.addEventListener('click', async () => {
    const jd = jobDescription.value.trim();
    if (!jd) {
        alert('Please enter a job description');
        return;
    }
    if (uploadedFiles.length === 0) {
        alert('Please upload at least one resume');
        return;
    }

    // UI State: Loading
    analyzeBtn.disabled = true;
    document.querySelector('.btn-text').textContent = 'Analyzing...';
    document.querySelector('.loader').classList.remove('hidden');

    const formData = new FormData();
    formData.append('job_description', jd);
    uploadedFiles.forEach(file => {
        formData.append('files', file);
    });

    try {
        const response = await fetch('/api/rank', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
            displayResults(data.results);
        } else {
            alert('Error: ' + (data.error || 'Failed to process resumes'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Could not connect to the server. Make sure the backend is running.');
    } finally {
        analyzeBtn.disabled = false;
        document.querySelector('.btn-text').textContent = '🔍 Analyze Candidates';
        document.querySelector('.loader').classList.add('hidden');
    }
});

function displayResults(results) {
    resultsSection.classList.remove('hidden');
    resultsList.innerHTML = '';
    
    results.forEach((res, index) => {
        const card = document.createElement('div');
        card.className = 'candidate-card';
        card.style.animationDelay = `${index * 0.1}s`;
        
        card.innerHTML = `
            <div class="candidate-header">
                <div>
                    <h3>${res.candidate_name}</h3>
                    <p style="color: var(--text-muted); font-size: 0.8rem">Rank #${index + 1}</p>
                </div>
                <div class="score-badge">${res.score}% Match</div>
            </div>
            <div style="margin-bottom: 1rem">
                <p style="font-size: 0.9rem; margin-bottom: 0.5rem">Matched Skills (${res.match_count})</p>
                <div class="skills-tags">
                    ${res.matched_skills.map(s => `<span class="tag match">${s}</span>`).join('')}
                </div>
            </div>
            <div>
                <p style="font-size: 0.9rem; margin-bottom: 0.5rem">Missing Skills</p>
                <div class="skills-tags">
                    ${res.missing_skills.slice(0, 10).map(s => `<span class="tag missing">${s}</span>`).join('')}
                    ${res.missing_skills.length > 10 ? `<span class="tag missing">+${res.missing_skills.length - 10} more</span>` : ''}
                </div>
            </div>
        `;
        resultsList.appendChild(card);
    });
    
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}
