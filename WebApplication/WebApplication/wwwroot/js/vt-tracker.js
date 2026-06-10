/**
 * vt-tracker.js  –  Vietnam Travel Global Behavior Tracker  v2
 * ─────────────────────────────────────────────────────────────
 * Nhúng 1 lần vào _Layout.cshtml (thay vietnam-travel-ai.js hoặc thêm kế bên).
 *
 * Luồng hoạt động:
 *  1. Đọc data-context JSON từ section wrapper (Hotel/Flight/Car/Transfer)
 *     hoặc fallback đọc DOM cho Tour (chưa có data-context)
 *  2. Tạo items chuẩn khớp tiền tố rule_generator.py
 *  3. Merge vào sessionStorage['vt_items']  →  gán body.dataset.allItems
 *  4. Gọi POST /Recommendation/LogBehavior
 *  5. Mỗi 3 trang → POST /Recommendation/CheckVoucher → toast nếu có voucher mới
 */
(function VTTracker() {
    'use strict';

    const SS_ITEMS = 'vt_items';
    const SS_COUNT = 'vt_log_count';
    const SS_SHOWN = 'vt_voucher_shown';

    /* ── Helpers ─────────────────────────────────────────────────────────── */
    function getItems() {
        return (sessionStorage.getItem(SS_ITEMS) || '').split(',').filter(Boolean);
    }
    function pushItems(arr) {
        const merged = [...new Set([...getItems(), ...arr.filter(Boolean)])];
        sessionStorage.setItem(SS_ITEMS, merged.join(','));
        document.body.dataset.allItems = merged.join(',');
        return merged;
    }
    function incCount() {
        const n = parseInt(sessionStorage.getItem(SS_COUNT) || '0', 10) + 1;
        sessionStorage.setItem(SS_COUNT, n);
        return n;
    }

    /* ── Chuẩn hoá địa danh → slug item ─────────────────────────────────── */
    const LOC_MAP = [
        [/hà\s*nội|hanoi|ha\s*noi\b|\bhn\b/i, 'Ha_Noi'],
        [/hồ\s*chí\s*minh|ho\s*chi\s*minh|hcm|sài\s*gòn|saigon/i, 'HCM'],
        [/đà\s*nẵng|da\s*nang|\bđna\b/i, 'Da_Nang'],
        [/phú\s*quốc|phu\s*quoc/i, 'Phu_Quoc'],
        [/nha\s*trang/i, 'Nha_Trang'],
        [/đà\s*lạt|da\s*lat/i, 'Da_Lat'],
        [/hội\s*an|hoi\s*an/i, 'Hoi_An'],
        [/huế\b|hue\b/i, 'Hue'],
        [/quy\s*nhơn|quy\s*nhon/i, 'Quy_Nhon'],
        [/vũng\s*tàu|vung\s*tau/i, 'Vung_Tau'],
        [/cần\s*thơ|can\s*tho/i, 'Can_Tho'],
        [/hạ\s*long|ha\s*long/i, 'Ha_Long'],
        [/sa\s*pa|sapa/i, 'Sa_Pa'],
        [/phan\s*thiết|phan\s*thiet/i, 'Phan_Thiet'],
        [/ninh\s*bình|ninh\s*binh/i, 'Ninh_Binh'],
    ];
    function normLoc(str) {
        if (!str) return '';
        for (const [re, val] of LOC_MAP) {
            if (re.test(str)) return val;
        }
        return str.replace(/\s+/g, '_').replace(/[^\w_]/g, '').substring(0, 30);
    }

    function priceTier(val) {
        if (!val || isNaN(val)) return 'NganSach_Trung_Binh';
        if (val < 500000) return 'NganSach_Thap';
        if (val < 2000000) return 'NganSach_Trung_Binh';
        return 'NganSach_Cao';
    }

    /* ── Đọc ngữ cảnh từ data-context hoặc DOM ───────────────────────────── */
    function extractItems() {
        const items = [];

        // Thử đọc data-context JSON (Hotel, Flight, Car, Transfer đã có)
        const sectionEl = document.querySelector('[data-context]');
        if (sectionEl) {
            try {
                const ctx = JSON.parse(sectionEl.dataset.context);

                // service
                if (ctx.service) items.push(ctx.service);

                // địa điểm đến
                const dest = ctx.destination || ctx.location || ctx.to;
                if (dest) {
                    const loc = normLoc(dest);
                    if (loc) items.push('Den_' + loc);
                }

                // xuất phát
                if (ctx.from || ctx.departure) {
                    const f = normLoc(ctx.from || ctx.departure);
                    if (f) items.push('TuDen_' + f);
                }

                // hãng hàng không
                if (ctx.airline) items.push('Hang_' + ctx.airline.replace(/\s+/g, '_').substring(0, 30));

                // khách sạn: sao + hồ bơi
                if (ctx.stars) {
                    items.push('KhachSan_' + ctx.stars + '_sao');
                    items.push(ctx.stars >= 4 ? 'KhachSan_Cao_Cap' : ctx.stars >= 3 ? 'KhachSan_Tieu_Chuan' : 'KhachSan_Binh_Dan');
                }
                if (ctx.has_pool) items.push(ctx.has_pool); // "Co_Ho_Boi" hoặc "Khong_Ho_Boi"

                // loại xe / loại phương tiện
                if (ctx.brand) items.push('Xe_' + ctx.brand.replace(/\s+/g, '_').substring(0, 20));
                if (ctx.type) items.push('Loai_' + ctx.type.replace(/\s+/g, '_'));

                // mức giá — ctx.price_tier đã là "Thap"/"Trung_Binh"/"Cao"
                if (ctx.price_tier) items.push('NganSach_' + ctx.price_tier);

                // tháng đặt
                if (ctx.month) {
                    const m = parseInt(ctx.month);
                    if (m >= 6 && m <= 8) items.push('Mua_He');
                    else if (m >= 12 || m <= 2) items.push('Mua_Dong');
                    else if (m >= 3 && m <= 5) items.push('Mua_Xuan');
                    else items.push('Mua_Thu');
                }

            } catch (e) { /* JSON parse fail — tiếp tục DOM fallback */ }
        }

        // DOM fallback cho Tour Details (chưa có data-context)
        const pt = (document.querySelector('[data-page-type]')?.dataset.pageType || '').toLowerCase();
        const isTour = pt === 'tour' || window.location.pathname.toLowerCase().startsWith('/tour/details');
        if (isTour && !items.includes('DV_Tour_Va_Khu_Vui_Choi')) {
            items.push('DV_Tour_Va_Khu_Vui_Choi');

            // Destination từ meta-item đầu tiên (kế icon pin)
            const metaItems = document.querySelectorAll('.meta-item');
            if (metaItems.length > 0) {
                const locText = metaItems[0].innerText.trim();
                const loc = normLoc(locText);
                if (loc) items.push('Den_' + loc);
            }

            // Số ngày
            const daysMatch = document.body.innerText.match(/(\d+)\s*ngày/i);
            if (daysMatch) {
                const d = parseInt(daysMatch[1]);
                if (d <= 3) items.push('SoNgay_Ngan');
                else if (d <= 7) items.push('SoNgay_TrungBinh');
                else items.push('SoNgay_Dai');
            }

            // Hoạt động từ nội dung trang
            const txt = document.body.innerText;
            if (/tắm biển|bãi biển/i.test(txt)) items.push('HD_Tam_Bien');
            if (/leo núi|trekking/i.test(txt)) items.push('HD_Leo_Nui_Trekking');
            if (/di tích|tham quan|lịch sử/i.test(txt)) items.push('HD_Tham_Quan_Di_Tich');
            if (/ẩm thực|đặc sản/i.test(txt)) items.push('HD_Am_Thuc');
            if (/check.?in|checkin/i.test(txt)) items.push('HD_Check_In');
            if (/nghỉ dưỡng|chữa lành|spa/i.test(txt)) items.push('HD_Nghi_Duong_Chua_Lanh');

            // Mức giá từ .price-big
            const priceEl = document.querySelector('.price-big');
            if (priceEl) {
                const num = parseInt(priceEl.innerText.replace(/[^\d]/g, ''), 10);
                if (num) items.push(priceTier(num));
            }
        }

        // Index/List pages — ghi nhận user ghé thăm mục dịch vụ
        const path = window.location.pathname.toLowerCase();
        const isIndex = !path.includes('/details') && !path.includes('/create') && !path.includes('/edit');
        if (isIndex) {
            if (path.startsWith('/hotel')) items.push('DV_Khach_San_Homestay');
            if (path.startsWith('/flight')) items.push('DV_Ve_May_Bay');
            if (path.startsWith('/tour')) items.push('DV_Tour_Va_Khu_Vui_Choi');
            if (path.startsWith('/car')) items.push('DV_Thue_Xe_Tu_Lai');
            if (path.startsWith('/transfer')) items.push('DV_Dua_Don_San_Bay');
        }

        return [...new Set(items)];
    }

    /* ── Tính PageValues và TimeOnPage ───────────────────────────────────── */
    const t0 = Date.now();
    let maxScroll = 0;
    window.addEventListener('scroll', () => {
        const pct = window.scrollY / Math.max(document.body.scrollHeight - window.innerHeight, 1);
        maxScroll = Math.max(maxScroll, pct);
    }, { passive: true });

    function calcPV() {
        // PageValues: scroll depth (0-100) + bonus chi tiết page
        const path = window.location.pathname.toLowerCase();
        const isDetail = path.includes('/details');
        return Math.round(maxScroll * 80 + (isDetail ? 20 : 5));
    }

    /* ── Gọi API log ─────────────────────────────────────────────────────── */
    async function sendLog(ctxItems) {
        const allMerged = pushItems(ctxItems);
        const path = window.location.pathname;
        const parts = path.replace(/^\//, '').split('/');
        const ctrl = parts[0] || 'Home';
        const refId = parseInt(parts[2] || '0', 10) || null;

        const PT_MAP = { hotel: 'Hotel', flight: 'Flight', tour: 'Tour', car: 'Car', transfer: 'Transfer' };
        const pageType = PT_MAP[ctrl.toLowerCase()] || 'Info';

        const payload = {
            pageType,
            referenceId: refId,
            pageValues: calcPV(),
            timeOnPage: Math.round((Date.now() - t0) / 1000),
            contextData: JSON.stringify({ items: ctxItems }),
            allItems: allMerged.join(','),
        };

        try {
            await fetch('/Recommendation/LogBehavior', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                keepalive: true,
            });
        } catch (_) { }
    }

    /* ── Kiểm tra & hiện voucher ─────────────────────────────────────────── */
    async function maybeCheckVoucher(count) {
        const isRecPage = window.location.pathname.toLowerCase().startsWith('/recommendation');
        if (!isRecPage && count % 3 !== 0) return;
        if (sessionStorage.getItem(SS_SHOWN) === '1') return;

        try {
            const res = await fetch('/Recommendation/CheckVoucher', { method: 'POST' });
            const data = await res.json();
            if (data.hasVoucher && data.isNew) {
                sessionStorage.setItem(SS_SHOWN, '1');
                showVoucherToast(data);
            }
        } catch (_) { }
    }

    /* ── Toast UI ────────────────────────────────────────────────────────── */
    function showVoucherToast(v) {
        if (document.getElementById('vt-toast')) return;

        const expStr = (() => {
            try {
                const d = new Date(v.expiresAt);
                return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
                    + ' ' + d.toLocaleDateString('vi-VN');
            } catch (_) { return ''; }
        })();

        const el = document.createElement('div');
        el.id = 'vt-toast';
        el.innerHTML = `
<div id="vt-toast-inner" style="
    position:fixed;bottom:24px;right:24px;z-index:99999;
    background:linear-gradient(135deg,#065f46 0%,#047857 100%);
    border:1.5px solid #10b981;border-radius:16px;
    padding:1.25rem 1.4rem;max-width:340px;width:calc(100vw - 48px);
    box-shadow:0 12px 40px rgba(0,0,0,.55);
    animation:vtSlideUp .4s cubic-bezier(.22,1,.36,1);
    font-family:inherit;color:#fff;
">
  <div style="display:flex;align-items:flex-start;gap:.85rem;">
    <span style="font-size:2.2rem;line-height:1;flex-shrink:0">🎁</span>
    <div style="flex:1;min-width:0;">
      <div style="font-weight:700;font-size:.98rem;margin-bottom:.25rem;">
        Bạn vừa nhận được Voucher!
      </div>
      <div style="font-size:.83rem;opacity:.9;margin-bottom:.55rem;">
        Giảm <strong style="color:#6ee7b7;font-size:1.05rem;">${v.discount}%</strong>
        cho <strong>${v.applicableType || 'dịch vụ'}</strong>
      </div>
      <div style="font-family:monospace;font-size:.95rem;
          background:rgba(255,255,255,.15);border-radius:6px;
          padding:.28rem .7rem;display:inline-block;
          letter-spacing:.12em;font-weight:700;">
        ${v.code}
      </div>
      ${expStr ? `<div style="font-size:.7rem;opacity:.6;margin-top:.35rem;">Hết hạn: ${expStr}</div>` : ''}
    </div>
    <button onclick="document.getElementById('vt-toast').remove()"
        style="background:none;border:none;color:rgba(255,255,255,.55);
            cursor:pointer;font-size:1.15rem;line-height:1;flex-shrink:0;padding:0;">✕</button>
  </div>
  <div style="margin-top:.9rem;display:flex;gap:.5rem;">
    <a href="/Recommendation/MyVouchers"
        onclick="document.getElementById('vt-toast').remove()"
        style="flex:1;text-align:center;padding:.48rem;
            background:rgba(255,255,255,.2);border-radius:8px;
            color:#fff;text-decoration:none;font-size:.81rem;font-weight:600;
            border:1px solid rgba(255,255,255,.25);">
        🎫 Xem voucher của tôi
    </a>
    <button onclick="document.getElementById('vt-toast').remove()"
        style="padding:.48rem .9rem;background:transparent;
            border:1px solid rgba(255,255,255,.25);border-radius:8px;
            color:rgba(255,255,255,.65);cursor:pointer;font-size:.81rem;">
        Để sau
    </button>
  </div>
</div>
<style>
@keyframes vtSlideUp {
  from { transform:translateY(20px);opacity:0 }
  to   { transform:translateY(0);opacity:1 }
}
</style>`;
        document.body.appendChild(el);
        setTimeout(() => { const t = document.getElementById('vt-toast'); if (t) t.remove(); }, 14000);
    }

    /* ── MAIN ────────────────────────────────────────────────────────────── */
    function main() {
        const items = extractItems();
        // Push ngay để _AssociationSuggestions partial có data
        pushItems(items);

        // Log khi rời trang (pagehide) hoặc sau 6s nếu detail page
        const isDetail = window.location.pathname.toLowerCase().includes('/details');
        let logged = false;
        const doLog = async () => {
            if (logged) return;
            logged = true;
            await sendLog(items);
            const n = incCount();
            maybeCheckVoucher(n);
        };

        window.addEventListener('pagehide', doLog, { once: true });
        if (isDetail) setTimeout(doLog, 6000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', main);
    } else {
        main();
    }
})();