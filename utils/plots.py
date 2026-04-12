import matplotlib.pyplot as plt
import numpy as np
import io

def get_mining_trend_fig(session_results):
    fig, ax = plt.subplots(figsize=(8, 4), facecolor='#0d1117')
    ax.set_facecolor('#161b22')
    
    if not session_results:
         ax.text(0.5, 0.5, "Run analysis to populate", ha='center', va='center', color='white')
         ax.axis('off')
    else:
        years = sorted(session_results.keys())
        areas = [session_results[y].get('area_km2', 0) for y in years]
        bars = ax.bar(years, areas, color='#c0392b')
        ax.set_xlabel("Year", color='white')
        ax.set_ylabel("Mining Area (km²)", color='white')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('#30363d')
        ax.set_xticks(years)
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width()/2., h, f'{h:.2f}', ha='center', va='bottom', color='white')
    
    fig.tight_layout()
    # Save to buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    plt.close(fig)
    return buf

def get_expansion_fig(years, areas):
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    fig.patch.set_facecolor('#0d1117')
    
    # Process for chart 1
    ax1 = axes[0]
    ax1.set_facecolor('#161b22')
    ax1.bar(years, areas, color='#2980b9')
    ax1.plot(years, areas, color='#c0392b', marker='o', linewidth=2)
    ax1.set_title("Mining Area (km²)", color='white')
    ax1.tick_params(colors='white')
    ax1.margins(y=0.15)
    for b in ax1.patches:
        ax1.annotate(f'{b.get_height():.2f}', (b.get_x() + b.get_width() / 2., b.get_height()),
                     textcoords="offset points", xytext=(0, 10), ha='center', va='bottom', color='white')
        
    ax2 = axes[1]
    ax2.set_facecolor('#161b22')
    changes = [0] + [(areas[i] - areas[i-1])/areas[i-1]*100 if areas[i-1] != 0 else 0 for i in range(1, len(years))]
    colors = ['#27ae60' if c >= 0 else '#c0392b' for c in changes]
    ax2.bar(years, changes, color=colors)
    ax2.set_title("YoY Change (%)", color='white')
    ax2.tick_params(colors='white')
    ax2.axhline(0, color='white', alpha=0.5)
    ax2.margins(y=0.15)
    for i, b in enumerate(ax2.patches):
        y_offset = 5 if changes[i] >= 0 else -15
        ax2.annotate(f'{changes[i]:.1f}%', (b.get_x() + b.get_width() / 2., b.get_height()),
                     textcoords="offset points", xytext=(0, y_offset), ha='center', color='white')
        
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf

def get_growth_fig(years, areas):
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#161b22')
    
    if len(years) > 0:
        base = areas[0]
        percs = [a/base*100 if base else 0 for a in areas]
        ax.plot(years, percs, marker='o', color='white', zorder=3)
        ax.fill_between(years, 100, percs, where=(np.array(percs) >= 100), facecolor='#c0392b', alpha=0.5, interpolate=True)
        ax.fill_between(years, 100, percs, where=(np.array(percs) <= 100), facecolor='#27ae60', alpha=0.5, interpolate=True)
        ax.axhline(100, ls='--', color='white', alpha=0.5)
        for i, p in enumerate(percs):
            y_off = 10 if p >= 100 else -15
            ax.annotate(f'{p:.1f}%', (years[i], p), textcoords="offset points", xytext=(0, y_off), ha='center', color='white')
            
    ax.set_title("Growth vs Baseline (%)", color='white')
    ax.tick_params(colors='white')
    ax.margins(y=0.20)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf

def get_comparison_bar_fig(accs, aucs, f1s, models):
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#161b22')
    
    x = np.arange(len(models))
    w = 0.25
    b1 = ax.bar(x - w, accs, w, label='Accuracy', color='#238636')
    b2 = ax.bar(x, aucs, w, label='AUC-ROC', color='#1f6feb')
    b3 = ax.bar(x + w, f1s, w, label='F1-Score', color='#8957e5')
    
    ax.set_ylim(0.85, 1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=20, color='white')
    ax.tick_params(axis='y', colors='white')
    ax.legend(loc='lower right', facecolor='#0d1117', labelcolor='white')
    
    for bs in [b1, b2, b3]:
        for b in bs:
            ax.text(b.get_x() + b.get_width()/2., b.get_height()+0.002, f'{b.get_height():.3f}', ha='center', va='bottom', color='white', fontsize=8)
            
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf

def get_radar_fig(models, attrs_list, categories=['Accuracy', 'Precision', 'Recall', 'F1', 'AUC']):
    fig = plt.figure(figsize=(6, 6))
    fig.patch.set_facecolor('#0d1117')
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor('#161b22')
    
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    
    for i, attrs in enumerate(attrs_list):
        values = attrs.copy()
        values += values[:1]
        ax.plot(angles, values, label=models[i], linewidth=2)
        ax.fill(angles, values, alpha=0.1)
        
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, color='white')
    ax.tick_params(colors='white')
    ax.set_ylim(0.85, 1.0)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), facecolor='#0d1117', labelcolor='white', fontsize=9)
    
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf
