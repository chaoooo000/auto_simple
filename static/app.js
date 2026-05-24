function _(sel) { return document.querySelector(sel); }
function __(sel) { return document.querySelectorAll(sel); }

function setupDropZone(dzId, inputId, listId) {
    var dz = _(dzId);
    var input = _(inputId);
    if (!dz || !input) return;
    dz.addEventListener('click', function() { input.click(); });
    dz.addEventListener('dragover', function(e) { e.preventDefault(); dz.classList.add('dragover'); });
    dz.addEventListener('dragleave', function() { dz.classList.remove('dragover'); });
    dz.addEventListener('drop', function(e) {
        e.preventDefault();
        dz.classList.remove('dragover');
        var files = e.dataTransfer.files;
        var dt = new DataTransfer();
        for (var i = 0; i < files.length; i++) dt.items.add(files[i]);
        input.files = dt.files;
        input.dispatchEvent(new Event('change', { bubbles: true }));
    });
}

function renderProfile(user) {
    if (!user) return '<p class="text-muted text-center mt-4">无数据</p>';
    var html = '<div class="profile-grid animate-stagger visible">';
    var fields = [
        ['姓名', user.name], ['性别', user.gender], ['年龄', user.age], ['最高学历', user.degree],
        ['手机', user.phone], ['邮箱', user.email], ['地址', user.address],
        ['专业', user.major], ['毕业院校', user.school], ['毕业年份', user.graduation_year],
    ];
    fields.forEach(function(f) {
        html += '<div class="profile-card"><div class="label">' + f[0] + '</div><div class="value">' + esc(f[1] || '-') + '</div></div>';
    });
    html += '</div>';

    if (user.skills && user.skills.length) {
        html += '<div class="section-title">专业技能</div><div>';
        user.skills.forEach(function(s) { html += '<span class="skill-tag">' + esc(s) + '</span>'; });
        html += '</div>';
    }
    if (user.education && user.education.length) {
        html += '<div class="section-title">教育背景</div>';
        user.education.forEach(function(e) {
            html += '<div class="expander"><div class="expander-header" role="button" tabindex="0" aria-expanded="false">' + esc(e.school||'-') + ' | ' + esc(e.degree||'-') + ' · ' + esc(e.major||'-') + ' <span class="arrow" aria-hidden="true">▸</span></div>';
            html += '<div class="expander-body"><div class="date">' + esc(e.start_date||'-') + ' ~ ' + esc(e.end_date||'-') + '</div></div></div>';
        });
    }
    if (user.work_experience && user.work_experience.length) {
        html += '<div class="section-title">工作经历</div>';
        user.work_experience.forEach(function(w) {
            html += '<div class="expander"><div class="expander-header" role="button" tabindex="0" aria-expanded="false">' + esc(w.company||'-') + ' — ' + esc(w.position||'-') + ' <span class="arrow" aria-hidden="true">▸</span></div>';
            html += '<div class="expander-body"><div class="date">' + esc(w.start_date||'-') + ' ~ ' + esc(w.end_date||'-') + '</div><div class="desc">' + esc(w.description||'') + '</div></div></div>';
        });
    }
    if (user.project_experience && user.project_experience.length) {
        html += '<div class="section-title">项目经历</div>';
        user.project_experience.forEach(function(p) {
            html += '<div class="expander"><div class="expander-header" role="button" tabindex="0" aria-expanded="false">' + esc(p.name||'未命名项目') + ' <span class="arrow" aria-hidden="true">▸</span></div>';
            html += '<div class="expander-body"><div class="role-line">角色：' + esc(p.role||'-') + '</div><div class="desc">' + esc(p.description||'') + '</div>';
            if (p.technologies && p.technologies.length) {
                html += '<div style="margin-top:6px">';
                p.technologies.forEach(function(t) { html += '<span class="skill-tag">' + esc(t) + '</span>'; });
                html += '</div>';
            }
            html += '</div></div>';
        });
    }
    if (user.certifications && user.certifications.length) {
        html += '<div class="section-title">证书资质</div><div>';
        user.certifications.forEach(function(c) { html += '<span class="skill-tag">' + esc(c) + '</span>'; });
        html += '</div>';
    }
    if (user.languages && user.languages.length) {
        html += '<div class="section-title">语言能力</div><div>';
        user.languages.forEach(function(l) { html += '<span class="skill-tag">' + esc(l) + '</span>'; });
        html += '</div>';
    }
    return html;
}

function renderRecommendations(list) {
    if (!list || !list.length) return '<p class="text-muted text-center mt-4">暂无推荐结果</p>';
    var html = '<div class="recommend-grid">';
    list.forEach(function(r, idx) {
        var pct = Math.round(r.score * 100);
        var color = pct >= 60 ? 'var(--success)' : (pct >= 30 ? 'var(--warning)' : 'var(--danger)');
        var rank = idx + 1;
        html += '<div class="recommend-card">';
        html += '<div class="rank-badge" aria-hidden="true">' + rank + '</div>';
        html += '<h3>' + esc(r.department) + '</h3>';
        html += '<div class="dept-desc">' + esc(r.description) + '</div>';
        html += '<div class="score-bar-wrap"><div class="score-label"><span class="score-text">匹配度</span><span class="score-number" style="color:' + color + '">' + pct + '%</span></div>';
        html += '<div class="score-bar"><div class="score-fill" style="background:' + color + '" data-target="' + pct + '"></div></div></div>';
        (r.reasons||[]).forEach(function(rr) { html += '<div class="reason">' + esc(rr) + '</div>'; });
        html += '</div>';
    });
    html += '</div>';
    return html;
}

function esc(s) {
    if (!s) return '';
    s = String(s);
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function setupAnimateStagger() {
    var els = document.querySelectorAll('.animate-stagger');
    if (!els.length) return;
    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15, rootMargin: '0px 0px -30px 0px' });
    els.forEach(function(el) {
        if (!el.classList.contains('visible')) observer.observe(el);
    });
}

function animateScoreBars(root) {
    var bars = (root || document).querySelectorAll('.score-fill[data-target]');
    bars.forEach(function(bar) {
        var target = bar.dataset.target;
        bar.style.width = '0%';
        requestAnimationFrame(function() {
            requestAnimationFrame(function() {
                bar.style.width = target + '%';
            });
        });
    });
}

function skeletonProfile() {
    var html = '<div class="profile-grid">';
    for (var i = 0; i < 8; i++) {
        html += '<div class="profile-card"><div class="skeleton skeleton-text" style="width:50%;margin-bottom:8px"></div><div class="skeleton skeleton-text medium"></div></div>';
    }
    html += '</div>';
    for (var j = 0; j < 3; j++) {
        html += '<div class="skeleton skeleton-heading" style="margin-top:16px"></div>';
        html += '<div class="skeleton skeleton-card"></div>';
    }
    return html;
}

function skeletonTable(rows) {
    rows = rows || 5;
    var html = '<div class="table-wrapper"><table><thead><tr>';
    var headers = ['文件名', '状态', '姓名', '学历', '专业', '推荐部门', '匹配度'];
    headers.forEach(function(h) { html += '<th>' + h + '</th>'; });
    html += '</tr></thead><tbody>';
    for (var i = 0; i < rows; i++) {
        html += '<tr>';
        for (var j = 0; j < headers.length; j++) {
            html += '<td><div class="skeleton skeleton-text" style="width:' + (60 + Math.random() * 30) + '%"></div></td>';
        }
        html += '</tr>';
    }
    html += '</tbody></table></div>';
    return html;
}

function showToast(msg, type, duration) {
    duration = duration || 3500;
    var t = _('#toast');
    if (!t) return;
    var iconMap = { success: '✅', error: '❌', info: 'ℹ️' };
    var icon = iconMap[type] || '';
    setHTMLSafe(t, '<span class="toast-icon">' + icon + '</span><span class="toast-msg">' + msg + '</span><button class="toast-close" aria-label="关闭通知">✕</button>');
    t.className = 'toast toast-' + (type || 'info') + ' visible';
    var closeBtn = t.querySelector('.toast-close');
    clearTimeout(t._timer);
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            t.className = 'toast hidden';
            clearTimeout(t._timer);
        });
    }
    if (duration > 0) {
        t._timer = setTimeout(function() { t.className = 'toast hidden'; }, duration);
    }
}

function closeModalAnimated(modalEl) {
    if (!modalEl || modalEl.classList.contains('hidden')) return;
    modalEl.classList.add('exit');
    setTimeout(function() {
        modalEl.classList.add('hidden');
        modalEl.classList.remove('exit');
    }, 200);
}

document.addEventListener('click', function(e) {
    var hdr = e.target.closest('.expander-header');
    if (hdr) {
        var exp = hdr.parentElement;
        var isOpen = exp.classList.toggle('open');
        var arrow = hdr.querySelector('.arrow');
        if (arrow) arrow.textContent = isOpen ? '▾' : '▸';
        hdr.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' || e.key === ' ') {
        var hdr = e.target.closest('.expander-header');
        if (hdr) {
            e.preventDefault();
            hdr.click();
        }
    }
});

document.addEventListener('click', function(e) {
    var tab = e.target.closest('.tab');
    if (tab) {
        var tabs = tab.parentElement;
        var container = tabs.parentElement;
        tabs.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
        tab.classList.add('active');
        var targetId = 'tab' + tab.dataset.tab.charAt(0).toUpperCase() + tab.dataset.tab.slice(1);
        container.querySelectorAll('.tab-content').forEach(function(c) { c.classList.remove('active'); });
        var target = _(('#' + targetId));
        if (target) {
            target.classList.add('active');
            animateScoreBars(target);
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {
    setupAnimateStagger();
});

var _ro = new ResizeObserver(function() {});

function setHTMLSafe(el, html) {
    el.textContent = '';
    el.insertAdjacentHTML('afterbegin', html);
}
