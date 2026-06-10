/**
 * vietnam-travel-ai.js  v3
 * Ghi nhận TOÀN BỘ ngữ cảnh người dùng: địa điểm, hãng bay, giá, loại xe...
 * Không chỉ ghi "DV_Ve_May_Bay" mà ghi cả "Den_Da_Nang", "NganSach_Cao", "Hang_VietJet"...
 */
(function () {
    'use strict';

    const SESS_ITEMS     = 'vt_items';        // tất cả item đã tích lũy (service + context)
    const SESS_SERVICES  = 'vt_visited_services'; // chỉ service keys (tương thích cũ)
    const SESS_PAGECOUNT = 'vt_page_count';
    const SESS_TOTALTIME = 'vt_total_time';
    const SESS_VOUCHER   = 'vt_voucher_shown';
    const LS_VOUCHER     = 'vt_active_voucher';

    const pageStart = Date.now();

    // ── Đọc ngữ cảnh từ data-context attribute ──────────────────────────
    function getPageContext() {
        // Tìm element có data-page-type (section hoặc container đã được patch)
        const el = document.querySelector('[data-page-type]');
        if (!el) return null;

        const pageType = el.dataset.pageType;
        const refId    = parseInt(el.dataset.refId) || null;
        let   ctx      = {};

        try { ctx = JSON.parse(el.dataset.context || '{}'); } catch (e) {}

        return { pageType, refId, ctx };
    }

    // ── Chuyển ngữ cảnh thành danh sách item cho FP-Growth ──────────────
    // Ví dụ: Flight Da_Nang 2 người giá cao → 
    //   ["DV_Ve_May_Bay", "Den_Da_Nang", "NganSach_Cao", "Hang_VietJet"]
    function buildItemsFromContext(pageType, ctx) {
        const items = new Set();

        // 1. Service chính (luôn có)
        if (ctx.service) items.add(ctx.service);

        // 2. Địa điểm / Đích đến
        if (ctx.destination) items.add(`Den_${ctx.destination}`);
        if (ctx.location)    items.add(`Den_${ctx.location.replace(/\s+/g, '_')}`);
        if (ctx.from)        items.add(`Tu_${ctx.from.replace(/\s+/g, '_')}`);

        // 3. Mức giá
        if (ctx.price_tier)  items.add(`NganSach_${ctx.price_tier}`);

        // 4. Thuộc tính riêng từng loại
        switch (pageType) {
            case 'Flight':
                if (ctx.departure)  items.add(`TuDen_${ctx.departure.replace(/\s+/g, '_')}`);
                if (ctx.airline)    items.add(`Hang_${ctx.airline.replace(/\s+/g, '_')}`);
                if (ctx.month) {
                    const m = parseInt(ctx.month);
                    if ([11, 12, 1].includes(m)) items.add('Mua_Dong');
                    else if ([3, 4, 5].includes(m)) items.add('Mua_Xuan');
                    else if ([6, 7, 8].includes(m)) items.add('Mua_Ha');
                    else items.add('Mua_Thu');
                }
                break;

            case 'Hotel':
                if (ctx.stars) {
                    const s = parseInt(ctx.stars);
                    if (s >= 4)      items.add('KhachSan_CaoCapTroLen4Sao');
                    else if (s >= 3) items.add('KhachSan_TamTot3Sao');
                    else             items.add('KhachSan_BinhDan');
                }
                if (ctx.has_pool)   items.add(ctx.has_pool);
                break;

            case 'Tour':
                if (ctx.duration_days) items.add(ctx.duration_days); // NgayDi_Ngan/Vua/Dai
                break;

            case 'Car':
                if (ctx.brand)     items.add(`Xe_${ctx.brand.replace(/\s+/g, '_')}`);
                if (ctx.available) items.add(ctx.available);
                break;

            case 'Transfer':
                if (ctx.type)      items.add(`PhuongTien_${ctx.type}`);
                break;
        }

        return [...items];
    }

    // ── Ghi nhận vào sessionStorage ─────────────────────────────────────
    function recordBehavior() {
        const info = getPageContext();
        if (!info) return;

        const { pageType, ctx } = info;
        const newItems = buildItemsFromContext(pageType, ctx);

        // Tích lũy tất cả items (không trùng)
        const allItems = JSON.parse(sessionStorage.getItem(SESS_ITEMS) || '[]');
        newItems.forEach(i => { if (!allItems.includes(i)) allItems.push(i); });
        sessionStorage.setItem(SESS_ITEMS, JSON.stringify(allItems));

        // Tương thích cũ: vẫn giữ SESS_SERVICES chỉ chứa service key
        if (ctx.service) {
            const services = JSON.parse(sessionStorage.getItem(SESS_SERVICES) || '[]');
            if (!services.includes(ctx.service)) services.push(ctx.service);
            sessionStorage.setItem(SESS_SERVICES, JSON.stringify(services));
        }

        // Expose cho partial _AssociationSuggestions
        document.body.dataset.serviceKey = ctx.service || '';
        document.body.dataset.pageType   = pageType;
        document.body.dataset.allItems   = allItems.join(',');
    }

    // ── Gửi log hành vi về server ────────────────────────────────────────
    function sendBehaviorLog() {
        const info = getPageContext();
        if (!info) return;

        const { pageType, refId, ctx } = info;
        const timeOnPage = (Date.now() - pageStart) / 1000;
        const scrollPct  = (window.scrollY + window.innerHeight) / Math.max(document.body.scrollHeight, 1);

        let pageValues = Math.min(timeOnPage / 60 * 10, 30);
        if (scrollPct > 0.5) pageValues += 10;
        if (isDetailsPage()) pageValues += 20;

        const newCount = getNum(SESS_PAGECOUNT) + 1;
        const newTime  = getNum(SESS_TOTALTIME) + timeOnPage;
        sessionStorage.setItem(SESS_PAGECOUNT, newCount);
        sessionStorage.setItem(SESS_TOTALTIME, newTime);

        const allItems = JSON.parse(sessionStorage.getItem(SESS_ITEMS) || '[]');

        const payload = JSON.stringify({
            pageType,
            referenceId: refId,
            pageValues:  Math.round(pageValues),
            timeOnPage:  Math.round(timeOnPage),
            contextData: JSON.stringify(ctx),     // gửi nguyên ctx lên server
            allItems:    allItems.join(',')        // toàn bộ items tích lũy
        });

        if (navigator.sendBeacon) {
            navigator.sendBeacon('/Recommendation/LogBehavior',
                new Blob([payload], { type: 'application/json' }));
        } else {
            fetch('/Recommendation/LogBehavior', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: payload, keepalive: true
            });
        }
    }

    // ── Voucher ──────────────────────────────────────────────────────────
    let countdownTimer = null;

    function shouldTryVoucher() {
        if (sessionStorage.getItem(SESS_VOUCHER)) return false;
        if (!isDetailsPage()) return false;
        const total = getNum(SESS_TOTALTIME) + elapsed();
        const pages = getNum(SESS_PAGECOUNT);
        return total >= 90 && pages >= 2;
    }

    async function checkVoucher() {
        if (!shouldTryVoucher()) return;
        try {
            const token = document.querySelector('input[name="__RequestVerificationToken"]')?.value;
            const headers = { 'Content-Type': 'application/json' };
            if (token) headers['RequestVerificationToken'] = token;
            const res  = await fetch('/Recommendation/CheckVoucher', { method: 'POST', headers });
            const data = await res.json();
            if (data.hasVoucher) {
                sessionStorage.setItem(SESS_VOUCHER, '1');
                showVoucherPopup(data);
                injectVoucherBadge(data);
            }
        } catch (e) {}
    }

    function showVoucherPopup(data) {
        injectStyles();
        const expiresAt = new Date(data.expiresAt);
        let   remainMs  = expiresAt - Date.now();

        const overlay = document.createElement('div');
        overlay.id = 'vt-overlay';
        overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.65);display:flex;align-items:center;justify-content:center;z-index:99999;animation:vtFadeIn .25s ease;';
        overlay.innerHTML = `
          <div id="vt-box" style="background:linear-gradient(145deg,#111827,#0f172a);border:1px solid rgba(245,158,11,.45);border-radius:18px;padding:2rem;max-width:400px;width:92%;text-align:center;box-shadow:0 0 50px rgba(245,158,11,.18);position:relative;animation:vtSlideUp .35s ease;">
            <button onclick="vtClose()" style="position:absolute;top:.9rem;right:1rem;background:none;border:none;color:rgba(255,255,255,.4);font-size:1.5rem;cursor:pointer;">×</button>
            <div style="font-size:2.8rem;margin-bottom:.4rem;">🎁</div>
            <div style="color:#f59e0b;font-size:1.3rem;font-weight:800;">VOUCHER DÀNH RIÊNG CHO BẠN!</div>
            <div style="color:rgba(255,255,255,.55);font-size:.85rem;margin:.5rem 0 1.4rem;">Bạn đang khám phá nhiều dịch vụ — nhận ưu đãi ngay!</div>
            <div style="background:rgba(245,158,11,.1);border:2px dashed rgba(245,158,11,.45);border-radius:12px;padding:1.1rem;margin-bottom:1.35rem;">
              <div style="color:rgba(255,255,255,.5);font-size:.75rem;margin-bottom:.35rem;">MÃ ƯU ĐÃI</div>
              <div id="vt-code" style="font-size:1.55rem;font-weight:800;letter-spacing:.18em;color:#f59e0b;font-family:monospace;">${data.code}</div>
              <div style="color:#86efac;font-size:1.05rem;font-weight:700;margin-top:.35rem;">GIẢM ${data.discount}% · ${data.applicableType !== 'All' ? data.applicableType : 'Tất cả dịch vụ'}</div>
            </div>
            <div style="margin-bottom:1.2rem;">
              <div style="color:rgba(255,255,255,.5);font-size:.78rem;margin-bottom:.25rem;">⏱ Hết hạn sau</div>
              <div id="vt-timer" style="font-size:2rem;font-weight:800;color:#f59e0b;font-family:monospace;">15:00</div>
            </div>
            <button onclick="vtCopy('${data.code}')" id="vt-copy-btn" style="width:100%;background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;border:none;border-radius:9px;padding:.8rem;font-size:1rem;font-weight:700;cursor:pointer;">📋 Sao chép mã</button>
          </div>`;
        document.body.appendChild(overlay);

        function tick() {
            remainMs = expiresAt - Date.now();
            const el = document.getElementById('vt-timer');
            if (!el) { clearInterval(countdownTimer); return; }
            if (remainMs <= 0) { el.textContent = 'HẾT HẠN'; clearInterval(countdownTimer); return; }
            el.textContent = `${pad(Math.floor(remainMs/60000))}:${pad(Math.floor((remainMs%60000)/1000))}`;
        }
        tick();
        countdownTimer = setInterval(tick, 1000);
        localStorage.setItem(LS_VOUCHER, JSON.stringify(data));
    }

    function injectVoucherBadge(data) {
        const info = getPageContext();
        if (!info) return;
        const ok = data.applicableType === 'All' || data.applicableType === info.pageType
                   || (data.applicableId && data.applicableId === info.refId);
        if (!ok) return;
        setTimeout(() => {
            if (document.getElementById('vt-badge')) return;
            const el = document.querySelector('.price-big');
            if (!el) return;
            const b = document.createElement('span');
            b.id = 'vt-badge';
            b.style.cssText = 'display:inline-flex;align-items:center;gap:.35rem;background:rgba(245,158,11,.15);border:1px solid rgba(245,158,11,.4);border-radius:6px;padding:.25rem .65rem;margin-left:.75rem;font-size:.8rem;font-weight:700;color:#f59e0b;vertical-align:middle;animation:vtFadeIn .4s ease;';
            b.textContent = `🏷 -${data.discount}% · ${data.code}`;
            el.insertAdjacentElement('afterend', b);
        }, 600);
    }

    function restoreBadge() {
        try {
            const v = JSON.parse(localStorage.getItem(LS_VOUCHER) || 'null');
            if (v && new Date(v.expiresAt) > new Date()) injectVoucherBadge(v);
            else localStorage.removeItem(LS_VOUCHER);
        } catch (e) {}
    }

    function injectStyles() {
        if (document.getElementById('vt-styles')) return;
        const s = document.createElement('style');
        s.id = 'vt-styles';
        s.textContent = '@keyframes vtFadeIn{from{opacity:0}to{opacity:1}}@keyframes vtSlideUp{from{transform:translateY(28px);opacity:0}to{transform:translateY(0);opacity:1}}';
        document.head.appendChild(s);
    }

    window.vtClose = () => { clearInterval(countdownTimer); document.getElementById('vt-overlay')?.remove(); };
    window.vtCopy  = (code) => {
        navigator.clipboard?.writeText(code).then(() => {
            const b = document.getElementById('vt-copy-btn');
            if (b) { b.textContent = '✅ Đã sao chép!'; setTimeout(() => b.textContent = '📋 Sao chép mã', 2000); }
        });
    };

    // ── Helpers ──────────────────────────────────────────────────────────
    function isDetailsPage() { return /\/details\/\d+|\/\d+$/i.test(window.location.pathname); }
    function elapsed()       { return (Date.now() - pageStart) / 1000; }
    function getNum(k)       { return parseFloat(sessionStorage.getItem(k) || '0'); }
    function pad(n)          { return String(n).padStart(2, '0'); }

    // ── Khởi chạy ────────────────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
        recordBehavior();
        restoreBadge();

        const need = Math.max(90 - getNum(SESS_TOTALTIME), 15) * 1000;
        if (getNum(SESS_PAGECOUNT) >= 2) setTimeout(checkVoucher, need);
        else if (getNum(SESS_PAGECOUNT) >= 1) setTimeout(checkVoucher, need);
    });

    window.addEventListener('beforeunload', sendBehaviorLog);
    window.addEventListener('pagehide',     sendBehaviorLog);
})();
