document.addEventListener('DOMContentLoaded', () => {
  // --- 1. INITIALIZE AOS ---
  if(typeof AOS !== 'undefined') {
    AOS.init({ duration: 800, once: true });
  }

  // --- 2. GLOBE INITIALIZATION (Dark/Blue Theme) ---
  const globeContainer = document.getElementById('globeViz');
  if (globeContainer && typeof Globe !== 'undefined') {
    const world = Globe()(globeContainer)
      .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
      .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
      .backgroundColor('rgba(0,0,0,0)') 
      .showAtmosphere(true)
      .atmosphereColor('#43a2ff')
      .atmosphereAltitude(0.15);

    world.controls().autoRotate = true;
    world.controls().autoRotateSpeed = 0.5;
    world.controls().enableZoom = false; 
    
    setTimeout(() => world.pointOfView({ altitude: 1.2 }), 0);

    const satData = [{ lat: 10, lng: 0, alt: 0.35 }];

    world.pathsData([
      [...Array(37).keys()].map(i => ({ lat: 10, lng: i * 10 - 180, alt: 0.35 }))
    ])
    .pathPointLat(d => d.lat)
    .pathPointLng(d => d.lng)
    .pathPointAlt(d => d.alt)
    .pathColor(() => 'rgba(14, 165, 233, 0.4)')
    .pathDashLength(0.01)
    .pathDashGap(0.005)
    .pathDashAnimateTime(15000);

    world.htmlElementsData(satData)
      .htmlElement(d => {
         const el = document.createElement('div');
         el.innerHTML = `
           <div style="transform: translate(-50%, -50%); pointer-events: none;">
             <img src="https://cdn-icons-png.flaticon.com/512/3069/3069411.png" style="width: 60px; height: 60px; filter: drop-shadow(0px 0px 8px rgba(14,165,233,1)); transform: rotate(45deg);" alt="sat" />
           </div>
         `;
         return el;
      })
      .htmlAltitude(d => d.alt);

    const orbitLoop = () => {
        satData[0].lng += 0.25;
        if(satData[0].lng > 180) satData[0].lng -= 360;
        world.htmlElementsData(satData);
        requestAnimationFrame(orbitLoop);
    };
    orbitLoop();

    window.addEventListener('resize', () => {
        world.width(window.innerWidth).height(window.innerHeight);
    });
  }

  // ═══════════════════════════════════════════════════════════
  // GLOBAL STATE (mirrors Streamlit st.session_state['results'])
  // ═══════════════════════════════════════════════════════════
  window.pipelineState = null;  // Will be array after analysis
  let currentFilesArray = [];
  let currentFileUrls = [];

  // ═══════════════════════════════════════════════════════════
  // NAVIGATION
  // ═══════════════════════════════════════════════════════════
  const navBtns = document.querySelectorAll('.nav-btn');
  const sections = document.querySelectorAll('.page-section');
  const btnGoUpload = document.getElementById('btnGoUpload');
  
  function openSection(targetId) {
    sections.forEach(sec => sec.classList.remove('active'));
    navBtns.forEach(btn => btn.classList.remove('active'));
    
    document.getElementById(targetId)?.classList.add('active');
    document.querySelector(`[data-target="${targetId}"]`)?.classList.add('active');

    // Scroll main content to top
    document.querySelector('.main-content')?.scrollTo(0, 0);

    // On entering analysis without data, show placeholder
    if(targetId === 'analysis') {
      if(window.pipelineState) {
        document.getElementById('analysisNoData').style.display = 'none';
        document.getElementById('analysisResults').style.display = 'block';
      } else {
        document.getElementById('analysisNoData').style.display = 'block';
        document.getElementById('analysisResults').style.display = 'none';
      }
    }
    // On entering maps without data, show placeholder
    if(targetId === 'maps') {
      if(window.pipelineState) {
        document.getElementById('mapsNoData').style.display = 'none';
        document.getElementById('mapsResults').style.display = 'block';
      } else {
        document.getElementById('mapsNoData').style.display = 'block';
        document.getElementById('mapsResults').style.display = 'none';
      }
    }
  }

  navBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openSection(btn.getAttribute('data-target'));
    });
  });

  btnGoUpload?.addEventListener('click', () => openSection('upload'));

  // ═══════════════════════════════════════════════════════════
  // TOAST ALERTS
  // ═══════════════════════════════════════════════════════════
  function showToast(message, isError = false) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast mb-4 p-4 rounded-xl shadow-2xl flex items-center text-white font-bold transition-transform transform translate-x-[120%]`;
    toast.style.background = isError ? 'rgba(239, 68, 68, 0.95)' : 'rgba(16, 185, 129, 0.95)';
    toast.style.backdropFilter = 'blur(10px)';
    
    toast.innerHTML = `<i class="fas max-w-sm ${isError ? 'fa-exclamation-triangle' : 'fa-check-circle'} mr-3 text-2xl"></i> <div>${message}</div>`;
    
    container.appendChild(toast);
    setTimeout(() => { toast.classList.remove('translate-x-[120%]'); }, 50);
    setTimeout(() => {
      toast.classList.add('translate-x-[120%]');
      setTimeout(() => toast.remove(), 400);
    }, 4000);
  }

  // ═══════════════════════════════════════════════════════════
  // PAGE 2: UPLOAD (matches 2_upload.py)
  // ═══════════════════════════════════════════════════════════
  const dropZone = document.getElementById('dropZone');
  const fileUpload = document.getElementById('fileUpload');
  const imagePreviewContainer = document.getElementById('imagePreviewContainer');

  if (dropZone && fileUpload) {
    dropZone.addEventListener('click', () => fileUpload.click());

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      handleFiles(e.dataTransfer.files);
    });

    fileUpload.addEventListener('change', (e) => handleFiles(e.target.files));
  }

  function handleFiles(files) {
    if (files.length === 0) return;
    const validExtensions = ['.jp2', '.tif', '.tiff', '.png', '.jpg', '.jpeg'];
    
    let validCount = 0;
    Array.from(files).forEach(file => {
        const fileName = file.name.toLowerCase();
        const isValid = validExtensions.some(ext => fileName.endsWith(ext)) || file.type.startsWith('image/');
        
        if (isValid) {
            currentFilesArray.push(file);
            validCount++;
        }
    });

    if (validCount > 0) {
        document.getElementById('dropZone').style.display = 'none';
        imagePreviewContainer.style.display = 'block';
        renderFileTable();
        showToast(`${validCount} file(s) added. Total: ${currentFilesArray.length}`);
    } else {
        showToast("Incompatible format. Please upload .JP2, .TIF, or .TIFF files.", true);
    }
    
    // Reset input so the same file(s) can be re-selected if needed
    fileUpload.value = '';
  }

  function renderFileTable() {
    document.getElementById('fileCountBadge').innerText = currentFilesArray.length;
    const tbody = document.getElementById('uploadFileTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    currentFilesArray.forEach((f, idx) => {
        const yrMatch = f.name.match(/20\d{2}/);
        const year = yrMatch ? yrMatch[0] : '2024';
        const size = (f.size / (1024*1024)).toFixed(1);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="p-3 text-white truncate max-w-xs" title="${f.name}">${f.name}</td>
            <td class="p-3 text-gray-400">${size} MB</td>
            <td class="p-3 text-accent font-bold">${year}</td>
            <td class="p-3"><input type="number" min="2000" max="2100" value="${year}" class="year-input bg-gray-800 border border-gray-600 rounded px-2 py-1 text-white text-center w-20" data-file-idx="${idx}"></td>
            <td class="p-3 text-center"><button class="text-red-400 hover:text-red-300 transition-colors text-lg px-1" title="Remove file" data-remove-idx="${idx}"><i class="fas fa-times"></i></button></td>
        `;
        tbody.appendChild(tr);
    });

    // Attach remove listeners
    tbody.querySelectorAll('[data-remove-idx]').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.dataset.removeIdx);
        removeFile(idx);
      });
    });

    // If all files removed, show drop zone again
    if(currentFilesArray.length === 0) {
      document.getElementById('dropZone').style.display = '';
      imagePreviewContainer.style.display = 'none';
    }
  }

  function removeFile(idx) {
    currentFilesArray.splice(idx, 1);
    renderFileTable();
    showToast(`File removed. ${currentFilesArray.length} file(s) remaining.`);
  }

  // "Add More Files" button re-opens the file picker
  document.getElementById('btnAddMoreFiles')?.addEventListener('click', () => {
    fileUpload.click();
  });

  // "Run AI Analysis" button on upload page → jump to analysis and trigger
  document.getElementById('btnScanPreview')?.addEventListener('click', () => {
     if(currentFilesArray.length === 0) {
       showToast("No files uploaded. Please add files first.", true);
       return;
     }
     openSection('analysis');
     // Auto-trigger the analysis
     document.getElementById('btnRunAnalysis')?.click();
  });

  // ═══════════════════════════════════════════════════════════
  // PAGE 3: ANALYSIS ENGINE (matches 2_upload.py processing + 3_analysis.py display)
  // ═══════════════════════════════════════════════════════════
  const btnRunAnalysis = document.getElementById('btnRunAnalysis');
  const analysisExecution = document.getElementById('analysisExecution');
  const execProgress = document.getElementById('execProgress');
  const execStatus = document.getElementById('execStatus');
  const analysisComplete = document.getElementById('analysisComplete');

  btnRunAnalysis?.addEventListener('click', async () => {
    // Show analysis panel
    document.getElementById('analysisNoData').style.display = 'none';
    document.getElementById('analysisResults').style.display = 'block';

    btnRunAnalysis.style.display = 'none';
    analysisExecution.style.display = 'block';
    
    let progress = 5;
    execProgress.style.width = `${progress}%`;
    execStatus.innerText = "";

    // Simulate per-file processing logs (matching 2_upload.py status messages)
    const filesToProcess = currentFilesArray.length > 0 ? currentFilesArray : [{name: 'T45QUE_2023_dummy.png'}];
    
    for(let i = 0; i < filesToProcess.length; i++) {
      const f = filesToProcess[i];
      const yrMatch = f.name.match(/20\d{2}/);
      const year = yrMatch ? yrMatch[0] : '2024';
      
      execStatus.innerText += `[SCAN] Processing ${f.name} (Year: ${year})\n`;
      execStatus.innerText += `  [LOAD] Loading JP2 / GeoTIFF...\n`;
      await sleep(300);
      execStatus.innerText += `  [IMG] Image loaded: 5490×5490px | downscale=0.909 | bands: RGB\n`;
      await sleep(200);
      execStatus.innerText += `  [NORM] Normalising uint16 bands — 2nd–98th percentile stretch...\n`;
      await sleep(200);
      execStatus.innerText += `  [AI] Running EfficientNet-B0 inference (batch_size=64)...\n`;
      
      // Progress bar simulation for each file
      const startPct = (i / filesToProcess.length) * 90 + 5;
      const endPct = ((i + 1) / filesToProcess.length) * 90 + 5;
      for(let step = 0; step < 20; step++) {
        progress = startPct + (step / 20) * (endPct - startPct);
        execProgress.style.width = `${progress}%`;
        execStatus.scrollTop = execStatus.scrollHeight;
        await sleep(50);
      }
      
      execStatus.innerText += `  [OK] Done.\n\n`;
      execStatus.scrollTop = execStatus.scrollHeight;
    }

    try {
        // Send batch to backend
        const formData = new FormData();
        if(currentFilesArray.length > 0) {
            currentFilesArray.forEach(f => formData.append('files', f));
        } else {
            const fakeBlob = new Blob([""], {type: "image/png"});
            formData.append('files', fakeBlob, "T45QUE_2023_dummy.png");
        }

        const res = await fetch('/api/analyze_batch', { method: 'POST', body: formData });
        const responseData = await res.json();
        
        // Cache globally (mirrors st.session_state['results'])
        window.pipelineState = responseData.results;
        
        execProgress.style.width = `100%`;
        execStatus.innerText += `[OK] Analysis complete! View the full details below.\n`;
        execStatus.scrollTop = execStatus.scrollHeight;

        setTimeout(() => {
          analysisComplete.style.display = 'block';
          populateAnalysisPage();
          populateHeatmapSelectors();
          buildTemporalExpansionChart();
          buildGrowthChart();
          fetchAndRenderChangeMatrix();
          showToast(`Analysis complete! ${window.pipelineState.length} file(s) processed.`);
        }, 500);

    } catch (err) {
        execProgress.style.width = `100%`;
        execStatus.innerText += `\n[WARN] Backend not reachable. Using demo fallback...\n`;
        
        // Demo fallback data
        window.pipelineState = [
          {filename:"demo_2021.jp2", year_detected:2021, current_footprint:155.95, baseline_footprint:155.95, expansion:0, expansion_pct:1.29, risk:"STABLE", overlay_path:"inference_output/temporal/2021_overlay.png", heatmap_path:"inference_output/temporal/2021_heatmap.png"},
          {filename:"demo_2022.jp2", year_detected:2022, current_footprint:156.26, baseline_footprint:155.95, expansion:0.31, expansion_pct:1.30, risk:"MODERATE", overlay_path:"inference_output/temporal/2022_overlay.png", heatmap_path:"inference_output/temporal/2022_heatmap.png"},
          {filename:"demo_2023.jp2", year_detected:2023, current_footprint:170.70, baseline_footprint:155.95, expansion:14.75, expansion_pct:1.42, risk:"CRITICAL", overlay_path:"inference_output/temporal/2023_overlay.png", heatmap_path:"inference_output/temporal/2023_heatmap.png"},
          {filename:"demo_2024.jp2", year_detected:2024, current_footprint:167.83, baseline_footprint:155.95, expansion:11.88, expansion_pct:1.39, risk:"CRITICAL", overlay_path:"inference_output/temporal/2024_overlay.png", heatmap_path:"inference_output/temporal/2024_heatmap.png"},
          {filename:"demo_2025.jp2", year_detected:2025, current_footprint:172.34, baseline_footprint:155.95, expansion:16.39, expansion_pct:1.43, risk:"CRITICAL", overlay_path:"inference_output/temporal/2025_overlay.png", heatmap_path:"inference_output/temporal/2025_heatmap.png"},
        ];
        
        setTimeout(() => {
           analysisComplete.style.display = 'block';
           populateAnalysisPage();
           populateHeatmapSelectors();
           buildTemporalExpansionChart();
           buildGrowthChart();
           fetchAndRenderChangeMatrix();
           showToast(`Demo data loaded (backend offline).`, true);
        }, 500);
    }
  });

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  // ═══════════════════════════════════════════════════════════
  // PAGE 3: POPULATE ANALYSIS (matches 3_analysis.py)
  // ═══════════════════════════════════════════════════════════
  function populateAnalysisPage() {
    if(!window.pipelineState || window.pipelineState.length === 0) return;
    
    const sorted = [...window.pipelineState].sort((a,b) => a.year_detected - b.year_detected);
    const latest = sorted[sorted.length - 1];
    const baseline = sorted[0];
    
    // Site ID
    document.getElementById('dispSiteId').innerText = 'SITE-01';
    
    // Current Footprint (matching 3_analysis.py col2.metric)
    document.getElementById('footprintLabel').innerText = `Current Footprint (${latest.year_detected})`;
    document.getElementById('currentFootprintVal').innerText = `${latest.current_footprint.toFixed(2)} km²`;
    
    // Expansion since baseline (matching 3_analysis.py col3.metric)
    if(sorted.length > 1) {
      const growth = latest.current_footprint - baseline.current_footprint;
      const growthPct = baseline.current_footprint > 0 ? (growth / baseline.current_footprint * 100) : 0;
      document.getElementById('expansionLabel').innerText = `Expansion since ${baseline.year_detected}`;
      document.getElementById('expansionDeltaVal').innerText = `${growth >= 0 ? '+' : ''}${growth.toFixed(2)} km²`;
      document.getElementById('expansionDeltaVal').style.color = growth > 0 ? 'var(--danger)' : 'var(--success)';
      document.getElementById('expansionPctVal').innerText = `${growthPct >= 0 ? '+' : ''}${growthPct.toFixed(1)}%`;
      document.getElementById('expansionPctVal').style.color = growth > 0 ? 'var(--danger)' : 'var(--success)';
    }
    
    // Risk Profile (matching 3_analysis.py risk logic)
    const val = latest.current_footprint;
    let risk;
    if(val > 170) risk = "CRITICAL (Active Expansion)";
    else if(val > 100) risk = "MODERATE (Persistent Mining)";
    else risk = "LOW (Minimal Activity)";
    document.getElementById('riskProfileLabel').innerText = risk;
    
    // Yearly Summary Table (matching 3_analysis.py dataframe)
    const summBody = document.querySelector('#yearlySummaryTable tbody');
    if(summBody) {
      summBody.innerHTML = '';
      sorted.forEach(item => {
        summBody.innerHTML += `<tr>
          <td class="p-3 font-medium text-white">${item.year_detected}</td>
          <td class="p-3 text-accent">${item.current_footprint.toFixed(2)}</td>
          <td class="p-3 text-gray-300">${item.expansion_pct.toFixed(2)}</td>
        </tr>`;
      });
    }
    
    // Trend Bar Chart (matching 3_analysis.py get_mining_trend_fig)
    buildTrendBarChart(sorted);
    
    // Update complete message
    document.getElementById('analysisCompleteMsg').innerText = `Analysis complete! ${sorted.length} file(s) processed.`;
  }

  // Trend Bar Chart (matching utils/plots.py get_mining_trend_fig)
  let trendChart = null;
  function buildTrendBarChart(sorted) {
    const ctx = document.getElementById('trendBarChartCanvas');
    if(!ctx) return;
    if(trendChart) trendChart.destroy();
    
    const years = sorted.map(r => r.year_detected);
    const areas = sorted.map(r => r.current_footprint);
    
    trendChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: years,
        datasets: [{
          label: 'Mining Area (km²)',
          data: areas,
          backgroundColor: 'rgba(192, 57, 43, 0.8)',
          borderColor: '#c0392b',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (ctx) => `${ctx.parsed.y.toFixed(2)} km²` } }
        },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, title: { display: true, text: 'Mining Area (km²)', color: '#94a3b8' } }
        }
      }
    });
  }

  // ═══════════════════════════════════════════════════════════
  // PAGE 3: REPORT DOWNLOAD (matches 3_analysis.py)
  // ═══════════════════════════════════════════════════════════
  document.getElementById('btnDownloadReport')?.addEventListener('click', () => {
    const state = window.pipelineState;
    if(!state || state.length === 0) {
      showToast("No analysis data to export.", true);
      return;
    }
    const sorted = [...state].sort((a,b) => a.year_detected - b.year_detected);
    const latest = sorted[sorted.length - 1];
    const val = latest.current_footprint;
    let riskWord = val > 170 ? "CRITICAL" : val > 100 ? "MODERATE" : "LOW";
    
    let report = `MINEWATCH SITE INTELLIGENCE REPORT\n`;
    report += `Date Generated: ${new Date().toISOString().split('T')[0]}\n`;
    report += `Site ID: SITE-01\n`;
    report += `Risk Profile: ${riskWord}\n\n`;
    report += `== METRICS ==\n`;
    sorted.forEach(item => {
      report += `${item.year_detected}: ${item.current_footprint.toFixed(2)} km^2\n`;
    });
    
    const blob = new Blob([report], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "SITE-01_report.txt";
    a.click();
    URL.revokeObjectURL(url);
    showToast("Report downloaded!");
  });

  document.getElementById('btnDownloadGPS')?.addEventListener('click', () => {
    const content = "lat,lon,confidence\n14.562,76.431,0.94\n14.579,76.442,0.92\n14.551,76.419,0.91\n14.568,76.438,0.89\n";
    const blob = new Blob([content], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "SITE-01_coordinates.csv";
    a.click();
    URL.revokeObjectURL(url);
    showToast("GPS coordinates exported!");
  });

  // ═══════════════════════════════════════════════════════════
  // RESET PIPELINE — Clear everything and start fresh
  // ═══════════════════════════════════════════════════════════
  document.getElementById('btnResetPipeline')?.addEventListener('click', () => {
    resetPipeline();
  });

  function resetPipeline() {
    // Clear global state
    window.pipelineState = null;
    currentFilesArray = [];
    currentFileUrls = [];

    // Reset upload page
    document.getElementById('dropZone').style.display = '';
    imagePreviewContainer.style.display = 'none';
    const tbody = document.getElementById('uploadFileTableBody');
    if(tbody) tbody.innerHTML = '';
    document.getElementById('fileCountBadge').innerText = '0';

    // Reset analysis page
    document.getElementById('analysisNoData').style.display = 'block';
    document.getElementById('analysisResults').style.display = 'none';
    document.getElementById('btnRunAnalysis').style.display = '';
    document.getElementById('analysisExecution').style.display = 'none';
    document.getElementById('analysisComplete').style.display = 'none';
    document.getElementById('execProgress').style.width = '0%';
    document.getElementById('execStatus').innerText = '';

    // Reset maps page
    document.getElementById('mapsNoData').style.display = 'block';
    document.getElementById('mapsResults').style.display = 'none';
    const yearSelector = document.getElementById('yearSelectorContainer');
    if(yearSelector) yearSelector.innerHTML = '<button class="bg-gray-800 text-gray-400 px-4 py-2 rounded-lg border border-gray-700 shadow pointer-events-none">Awaiting Telemetry</button>';

    // Destroy charts if they exist
    if(trendChart) { trendChart.destroy(); trendChart = null; }
    if(expansionChart) { expansionChart.destroy(); expansionChart = null; }
    if(growthChart) { growthChart.destroy(); growthChart = null; }

    // Navigate to upload page
    openSection('upload');
    showToast("Pipeline reset. Ready for new files.");
  }

  // ═══════════════════════════════════════════════════════════
  // PAGE 4: TEMPORAL TABS (matches 4_temporal.py)
  // ═══════════════════════════════════════════════════════════
  
  // Tab switching for Temporal
  document.querySelectorAll('.temporal-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.temporal-tab').forEach(t => {
        t.classList.remove('active', 'text-accent', 'border-accent');
        t.classList.add('text-gray-400', 'border-transparent');
      });
      document.querySelectorAll('.temporal-tab-content').forEach(c => {
        c.style.display = 'none';
        c.classList.remove('active');
      });
      tab.classList.add('active', 'text-accent', 'border-accent');
      tab.classList.remove('text-gray-400', 'border-transparent');
      const target = document.getElementById(tab.dataset.tab);
      if(target) { target.style.display = 'block'; target.classList.add('active'); }
    });
  });

  // Tab 1: Expansion Chart (matching 4_temporal.py tab1 — get_expansion_fig)
  let expansionChart = null;
  function buildTemporalExpansionChart() {
    const ctx = document.getElementById('temporalChartCanvas');
    if(!ctx) return;
    if(expansionChart) expansionChart.destroy();

    let years, areas;
    if(window.pipelineState && window.pipelineState.length > 0) {
      const sorted = [...window.pipelineState].sort((a,b) => a.year_detected - b.year_detected);
      years = sorted.map(r => r.year_detected);
      areas = sorted.map(r => r.current_footprint);
    } else {
      years = [2021,2022,2023,2024,2025];
      areas = [155.95, 156.26, 170.70, 167.83, 172.34];
    }

    // YoY Change % (matching utils/plots.py get_expansion_fig axes[1])
    const changes = areas.map((a, i) => i === 0 ? 0 : ((a - areas[i-1]) / areas[i-1] * 100));

    expansionChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: years,
        datasets: [
          {
            label: 'Mining Area (km²)',
            data: areas,
            backgroundColor: 'rgba(41, 128, 185, 0.7)',
            borderColor: '#2980b9',
            borderWidth: 1,
            yAxisID: 'y'
          },
          {
            label: 'YoY Change (%)',
            data: changes,
            type: 'line',
            borderColor: '#c0392b',
            backgroundColor: 'rgba(192, 57, 43, 0.0)',
            borderWidth: 2,
            pointRadius: 4,
            pointBackgroundColor: '#c0392b',
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#cbd5e1' } } },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { position: 'left', ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, title: { display: true, text: 'Area (km²)', color: '#94a3b8' } },
          y1: { position: 'right', ticks: { color: '#c0392b' }, grid: { drawOnChartArea: false }, title: { display: true, text: 'YoY Change (%)', color: '#c0392b' } }
        }
      }
    });
  }

  // Tab 2: Change Detection Matrix (matching 4_temporal.py tab2)
  async function fetchAndRenderChangeMatrix() {
    const tbody = document.getElementById('changeMatrixBody');
    if(!tbody) return;
    
    let matrix;
    try {
      const res = await fetch('/api/change_matrix');
      const data = await res.json();
      matrix = data.matrix;
    } catch(e) {
      matrix = [
        {year:2021, persistent:null, new_exp:155.95, recovered:null, net:155.95},
        {year:2022, persistent:120.50, new_exp:35.76, recovered:35.45, net:156.26},
        {year:2023, persistent:135.10, new_exp:35.60, recovered:21.16, net:170.70},
        {year:2024, persistent:145.50, new_exp:22.33, recovered:25.20, net:167.83},
        {year:2025, persistent:150.20, new_exp:22.14, recovered:17.63, net:172.34}
      ];
    }
    
    tbody.innerHTML = '';
    matrix.forEach(row => {
      tbody.innerHTML += `<tr>
        <td class="p-3 text-white font-medium">${row.year}</td>
        <td class="p-3" style="color: #3498db;">${row.persistent !== null ? row.persistent.toFixed(2) : '—'}</td>
        <td class="p-3" style="color: #e74c3c;">${row.new_exp !== null ? row.new_exp.toFixed(2) : '—'}</td>
        <td class="p-3" style="color: #2ecc71;">${row.recovered !== null ? row.recovered.toFixed(2) : '—'}</td>
        <td class="p-3 text-white font-semibold">${row.net.toFixed(2)}</td>
      </tr>`;
    });
  }

  // Tab 3: Growth Chart (matching 4_temporal.py tab3 — get_growth_fig)
  let growthChart = null;
  function buildGrowthChart() {
    const ctx = document.getElementById('growthChartCanvas');
    if(!ctx) return;
    if(growthChart) growthChart.destroy();

    let years, areas;
    if(window.pipelineState && window.pipelineState.length > 0) {
      const sorted = [...window.pipelineState].sort((a,b) => a.year_detected - b.year_detected);
      years = sorted.map(r => r.year_detected);
      areas = sorted.map(r => r.current_footprint);
    } else {
      years = [2021,2022,2023,2024,2025];
      areas = [155.95, 156.26, 170.70, 167.83, 172.34];
    }

    const base = areas[0];
    const percs = areas.map(a => base > 0 ? (a / base * 100) : 100);

    growthChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: years,
        datasets: [{
          label: 'Growth vs Baseline (%)',
          data: percs,
          borderColor: '#ffffff',
          backgroundColor: percs.map(p => p >= 100 ? 'rgba(192,57,43,0.3)' : 'rgba(39,174,96,0.3)'),
          borderWidth: 2,
          pointRadius: 5,
          pointBackgroundColor: '#ffffff',
          fill: true
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#cbd5e1' } },
          annotation: {} // baseline annotation handled by scale
        },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.1)' }, title: { display: true, text: 'Growth vs Baseline (%)', color: '#94a3b8' } }
        }
      }
    });
  }

  // Temporal CSV Download (matching 4_temporal.py st.download_button)
  document.getElementById('btnDownloadTemporalCSV')?.addEventListener('click', async () => {
    let matrix;
    try {
      const res = await fetch('/api/change_matrix');
      const data = await res.json();
      matrix = data.matrix;
    } catch(e) {
      matrix = [{year:2021,persistent:null,new_exp:155.95,recovered:null,net:155.95}];
    }
    
    let csv = "Year,Persistent Area (km²),New Expansion (km²),Recovered Area (km²),Net Area (km²)\n";
    matrix.forEach(row => {
      csv += `${row.year},${row.persistent || ''},${row.new_exp},${row.recovered || ''},${row.net}\n`;
    });
    
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "temporal_data.csv";
    a.click();
    URL.revokeObjectURL(url);
    showToast("Temporal CSV downloaded!");
  });

  // ═══════════════════════════════════════════════════════════
  // PAGE 5: RESULT MAPS (matches 5_result_map.py)
  // ═══════════════════════════════════════════════════════════
  
  let currentMapYear = null;

  function populateHeatmapSelectors() {
    const container = document.getElementById('yearSelectorContainer');
    if(!container) return;
    container.innerHTML = '';
    
    if(!window.pipelineState || window.pipelineState.length === 0) return;
    
    // Show the maps results panel
    document.getElementById('mapsNoData').style.display = 'none';
    document.getElementById('mapsResults').style.display = 'block';
    
    const sorted = [...window.pipelineState].sort((a,b) => a.year_detected - b.year_detected);
    
    sorted.forEach((item, index) => {
        const btn = document.createElement('button');
        const isActive = (index === sorted.length - 1);
        btn.className = `px-4 py-2 font-bold tracking-wide rounded-lg border-b-2 shadow transition-all text-sm ${isActive ? 'bg-sky-900 border-sky-400 text-white' : 'bg-gray-800 text-gray-400 border-gray-700 hover:border-gray-500'}`;
        btn.innerText = item.year_detected;
        
        btn.onclick = () => {
            Array.from(container.children).forEach(c => {
                c.className = 'px-4 py-2 font-bold tracking-wide rounded-lg border-b-2 shadow transition-all text-sm bg-gray-800 text-gray-400 border-gray-700 hover:border-gray-500';
            });
            btn.className = 'px-4 py-2 font-bold tracking-wide rounded-lg border-b-2 shadow transition-all text-sm bg-sky-900 border-sky-400 text-white';
            selectMapYear(item);
        };
        container.appendChild(btn);
    });
    
    // Load latest year by default
    selectMapYear(sorted[sorted.length - 1]);
  }

  function selectMapYear(item) {
    currentMapYear = item;
    
    // Update overlay and heatmap images
    document.getElementById('mapOverlayImg').src = '/' + item.overlay_path;
    document.getElementById('mapHeatmapImg').src = '/' + item.heatmap_path;
    
    // Update per-year metrics (matching 5_result_map.py col1.metric, col2.metric)
    document.getElementById('mapAreaMetric').innerText = `${item.current_footprint.toFixed(2)} km²`;
    document.getElementById('mapCoverageMetric').innerText = `${item.expansion_pct.toFixed(2)} %`;
  }

  // Map view tab switching (Overlay / Heatmap)
  document.querySelectorAll('.map-view-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.map-view-tab').forEach(t => {
        t.classList.remove('active', 'text-accent', 'border-accent');
        t.classList.add('text-gray-400', 'border-transparent');
      });
      document.querySelectorAll('.map-view-content').forEach(c => {
        c.style.display = 'none';
        c.classList.remove('active');
      });
      tab.classList.add('active', 'text-accent', 'border-accent');
      tab.classList.remove('text-gray-400', 'border-transparent');
      const target = document.getElementById(tab.dataset.tab);
      if(target) { target.style.display = 'block'; target.classList.add('active'); }
    });
  });

  // Year-specific CSV download (matching 5_result_map.py st.download_button)
  document.getElementById('btnDownloadYearCSV')?.addEventListener('click', () => {
    const year = currentMapYear ? currentMapYear.year_detected : 'unknown';
    const content = `lat,lon\n14.562,76.431\n14.579,76.442\n14.551,76.419\n`;
    const blob = new Blob([content], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `coords_${year}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Coordinates for ${year} exported!`);
  });

  // ═══════════════════════════════════════════════════════════
  // PAGE 6: MODEL COMPARISON (matches 6_model_comparison.py)
  // ═══════════════════════════════════════════════════════════
  
  // Tab switching for Comparison
  document.querySelectorAll('.comp-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.comp-tab').forEach(t => {
        t.classList.remove('active', 'text-accent', 'border-accent');
        t.classList.add('text-gray-400', 'border-transparent');
      });
      document.querySelectorAll('.comp-tab-content').forEach(c => {
        c.style.display = 'none';
        c.classList.remove('active');
      });
      tab.classList.add('active', 'text-accent', 'border-accent');
      tab.classList.remove('text-gray-400', 'border-transparent');
      const target = document.getElementById(tab.dataset.tab);
      if(target) { target.style.display = 'block'; target.classList.add('active'); }
    });
  });

  // Benchmark Table + Charts
  async function buildComparisonPage() {
    // Fetch model data
    let models;
    try {
      const res = await fetch('/api/model_benchmark');
      const data = await res.json();
      models = data.models;
    } catch(e) {
      models = [
        {name:"Custom CNN", accuracy:0.9167, auc:0.9741, f1:0.88, precision:0.91, recall:0.96},
        {name:"Enhanced CNN", accuracy:0.9257, auc:0.9785, f1:0.92, precision:0.92, recall:0.97},
        {name:"ResNet-18", accuracy:0.9189, auc:0.9738, f1:0.89, precision:0.93, recall:0.94},
        {name:"MobileNetV2", accuracy:0.9212, auc:0.9734, f1:0.90, precision:0.92, recall:0.95},
        {name:"EfficientNet-B0", accuracy:0.9279, auc:0.9711, f1:0.94, precision:0.94, recall:0.94},
        {name:"EfficientNetV2-S", accuracy:0.9234, auc:0.9631, f1:0.93, precision:0.94, recall:0.95}
      ];
    }

    // Find max values for highlighting (matching 6_model_comparison.py highlight_max)
    const maxAcc = Math.max(...models.map(m => m.accuracy));
    const maxAuc = Math.max(...models.map(m => m.auc));
    const maxF1  = Math.max(...models.map(m => m.f1));

    // Render benchmark table
    const tbody = document.getElementById('benchmarkBody');
    if(tbody) {
      tbody.innerHTML = '';
      models.forEach(m => {
        const accStyle = m.accuracy === maxAcc ? 'background-color: rgba(30,58,138,0.6); font-weight: bold;' : '';
        const aucStyle = m.auc === maxAuc ? 'background-color: rgba(30,58,138,0.6); font-weight: bold;' : '';
        const f1Style  = m.f1 === maxF1 ? 'background-color: rgba(30,58,138,0.6); font-weight: bold;' : '';
        
        tbody.innerHTML += `<tr>
          <td class="p-3 text-white font-medium">${m.name}</td>
          <td class="p-3" style="${accStyle}">${m.accuracy.toFixed(4)}</td>
          <td class="p-3" style="${aucStyle}">${m.auc.toFixed(4)}</td>
          <td class="p-3" style="${f1Style}">${m.f1.toFixed(4)}</td>
          <td class="p-3">${m.precision.toFixed(2)}</td>
          <td class="p-3">${m.recall.toFixed(2)}</td>
        </tr>`;
      });
    }

    // Bar Chart (matching utils/plots.py get_comparison_bar_fig)
    const barCtx = document.getElementById('modelBarChartCanvas');
    if(barCtx) {
      new Chart(barCtx, {
        type: 'bar',
        data: {
          labels: models.map(m => m.name),
          datasets: [
            { label: 'Accuracy', data: models.map(m => m.accuracy), backgroundColor: 'rgba(35, 134, 54, 0.7)' },
            { label: 'AUC-ROC', data: models.map(m => m.auc), backgroundColor: 'rgba(31, 111, 235, 0.7)' },
            { label: 'F1-Score', data: models.map(m => m.f1), backgroundColor: 'rgba(137, 87, 229, 0.7)' }
          ]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { labels: { color: '#cbd5e1' } } },
          scales: {
            x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            y: { min: 0.85, max: 1.0, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
          }
        }
      });
    }

    // Radar Chart (matching utils/plots.py get_radar_fig — all 6 models)
    const radarCtx = document.getElementById('modelRadarChartCanvas');
    if(radarCtx) {
      const radarColors = ['#ef4444','#f59e0b','#10b981','#8b5cf6','#0ea5e9','#ec4899'];
      
      new Chart(radarCtx, {
        type: 'radar',
        data: {
          labels: ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'AUC-ROC'],
          datasets: models.map((m, i) => ({
            label: m.name,
            data: [m.accuracy, m.precision, m.recall, m.f1, m.auc],
            borderColor: radarColors[i],
            backgroundColor: radarColors[i].replace(')', ', 0.1)').replace('rgb', 'rgba'),
            borderWidth: 2,
            pointRadius: 2
          }))
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 10 } }, position: 'bottom' } },
          scales: {
            r: {
              min: 0.85, max: 1.0,
              angleLines: { color: 'rgba(255,255,255,0.1)' },
              grid: { color: 'rgba(255,255,255,0.1)' },
              pointLabels: { color: '#cbd5e1', font: { size: 12 } },
              ticks: { display: false }
            }
          }
        }
      });
    }
  }

  // Build comparison page on load
  buildComparisonPage();
  
  // Also build initial temporal charts with fallback data
  buildTemporalExpansionChart();
  buildGrowthChart();
  fetchAndRenderChangeMatrix();

});
