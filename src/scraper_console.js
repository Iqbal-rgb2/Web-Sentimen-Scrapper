/**
 * Google Maps Review Scraper (Browser Console Version)
 * * How to run:
 * 1. Open Google Maps in your desktop browser.
 * 2. Search for the target place/business and open the "Reviews" tab.
 * 3. Open Developer Tools (Press F12 or Right Click -> Inspect -> Console).
 * 4. Paste this script into the console and hit Enter.
 * 5. The scraped data will be exported/copied to clipboard as JSON/CSV.
 */

// --- Kode scraping console kamu dimulai di sini ---

(async () => {
    console.log("🚀 Memulai pengikisan data seluruh ulasan Google Maps (Mode Tanpa Batas)...");

    // 1. Cari kontainer scroll yang aktif dan dapat discroll
    const getScrollContainer = () => {
        const containers = document.querySelectorAll('div.m6QErb');
        for (let c of containers) {
            if (c.scrollHeight > c.clientHeight && c.clientHeight > 200) {
                return c;
            }
        }
        return document.querySelector('div.m6QErb.DxyBCb') || document.querySelector('div[role="region"]');
    };

    const container = getScrollContainer();
    if (!container) {
        console.error("❌ Panel scroll ulasan tidak ditemukan. Pastikan tab 'Ulasan' sudah terbuka di Maps!");
        return;
    }

    let previousCount = 0;
    let idleRetries = 0;
    const maxRetries = 10; // Menunggu hingga 10 kali jeda jika ulasan lambat termuat

    console.log("⏳ Sedang menggulir seluruh data ulasan, mohon tunggu hingga tuntas...");

    // 2. Loop Auto-Scroll Tanpa Batas (Infinite Scroll Loop)
    while (true) {
        // Gulir kontainer secara bertahap ke dasar
        container.scrollTop = container.scrollHeight;

        // Picu juga scrollIntoView pada elemen review terakhir
        const reviewCards = document.querySelectorAll('div.jftiEf');
        const currentCount = reviewCards.length;

        if (currentCount > 0) {
            reviewCards[currentCount - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
        }

        // Simulasi event wheel agar listener internal Google Maps aktif
        container.dispatchEvent(new WheelEvent('wheel', { deltaY: 1000, bubbles: true }));

        // Jeda waktu rendering DOM dan request jaringan Google Maps
        await new Promise(r => setTimeout(r, 1800));

        const updatedCount = document.querySelectorAll('div.jftiEf').length;
        console.log(`📈 Ulasan termuat saat ini: ${updatedCount}`);

        if (updatedCount === previousCount) {
            idleRetries++;
            console.log(`⚠️ Menunggu batch ulasan berikutnya... (${idleRetries}/${maxRetries})`);
            
            // Gerakkan sedikit ke atas lalu ke bawah lagi untuk memicu trigger scroll
            container.scrollTop -= 200;
            await new Promise(r => setTimeout(r, 400));
            container.scrollTop = container.scrollHeight;

            if (idleRetries >= maxRetries) {
                console.log("🏁 Seluruh ulasan yang tersedia di Google Maps telah berhasil dimuat!");
                break;
            }
        } else {
            idleRetries = 0;
            previousCount = updatedCount;
        }
    }

    // 3. Ekspansi Semua Tombol "Lainnya" agar Teks Ulasan Panjang Tidak Terpotong
    console.log("📖 Membuka seluruh ulasan yang terpotong tombol 'Lainnya'...");
    const moreButtons = document.querySelectorAll('button.w8nwRe.kyuRq, button[aria-label*="Lainnya"], button[aria-label*="Lihat ulasan lengkap"]');
    moreButtons.forEach(btn => btn.click());
    await new Promise(r => setTimeout(r, 1000));

    // 4. Ekstraksi Seluruh 7 Kolom Data Mentah
    console.log("📊 Mengekstrak seluruh kolom data...");
    const reviews = [];
    document.querySelectorAll('div.jftiEf').forEach(el => {
        // Nama Akun
        const nameEl = el.querySelector('.d4r55');
        const name = nameEl ? nameEl.innerText.trim() : 'Anonymous';

        // Profil & Total Ulasan Akun
        const statsEl = el.querySelector('.RfnDt');
        const statsText = statsEl ? statsEl.innerText : '';
        const isLocalGuide = statsText.includes('Local Guide') ? 'Ya' : 'Bukan';
        const reviewsCountMatch = statsText.match(/(\d+[\d.,]*)\s+ulasan/i);
        const totalUserReviews = reviewsCountMatch ? reviewsCountMatch[1].replace(/[.,]/g, '') : '0';

        // Rating Bintang (1 - 5)
        const ratingEl = el.querySelector('span.kvMYJc') || el.querySelector('.fzvQIb');
        let rating = '';
        if (ratingEl) {
            const aria = ratingEl.getAttribute('aria-label') || ratingEl.innerText;
            const match = aria.match(/([1-5])/);
            if (match) rating = match[1];
        }

        // Tanggal / Waktu Ulasan
        const dateEl = el.querySelector('.rsqaWe');
        const date = dateEl ? dateEl.innerText.trim() : '';

        // Teks Lengkap Ulasan
        const textEl = el.querySelector('.wiI7pd');
        const text = textEl ? textEl.innerText.replace(/\r?\n|\r/g, ' ').trim() : '';

        // Deteksi Lampiran Foto
        const hasImage = el.querySelector('.KtCyie') || el.querySelector('button[aria-label*="foto"]') || el.querySelector('div.Tya61d') ? 'Ya' : 'Tidak';

        // Hanya masukkan ulasan yang memiliki teks kalimat
        if (text) {
            reviews.push({
                User_Name: name,
                Is_Local_Guide: isLocalGuide,
                User_Total_Reviews: totalUserReviews,
                Rating: rating,
                Review_Date: date,
                Has_Image: hasImage,
                Review_Text: text
            });
        }
    });

    // 5. Unduh Otomatis File CSV (UTF-8 BOM)
    let csv = 'User_Name,Is_Local_Guide,User_Total_Reviews,Rating,Review_Date,Has_Image,Review_Text\n';
    reviews.forEach(r => {
        csv += `"${r.User_Name.replace(/"/g, '""')}","${r.Is_Local_Guide}","${r.User_Total_Reviews}","${r.Rating}","${r.Review_Date}","${r.Has_Image}","${r.Review_Text.replace(/"/g, '""')}"\n`;
    });

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'raw_reviews.csv';
    link.click();

    console.log(`✅ Selesai! Berhasil mengekstrak ${reviews.length} ulasan lengkap dari total data yang ada.`);
})();