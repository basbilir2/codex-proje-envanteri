# len 2 — Ücretsiz işçi, ücretli yönetim

Ana amaç, kaliteyi koruyarak Astra/GPT token tüketimini azaltmaktır. Yerel model lentiküler alan bilgisini, mevcut yazılımın kullanımını ve görev disiplinini öğrenir; işçiliği üstlenir. Ücretli model planı kurar, gerektiğinde teşhis/karar verir ve sonucu denetler.

Akış: **Astra iş emri → yerel çalışma ve kontroller → gerekiyorsa kısa devir → Astra kararı → yerel devam → Astra son denetimi.** Bu döngü iş içinde birçok kez gerçekleşebilir. Her basit adımda ücretli modele dönülmez. Yerel model de devre ihtiyaç duyduğunu belirtebilir; zorunlu devir kurallarını veya son denetimi kaldıramaz.

Ücretli API anahtarı veya harici çıkarım servisi kullanılmaz. Yerel model, mevcut llama.cpp komut satırı motoruyla dosyalar üzerinden çalışır. Ücretli taraf bu oturumdaki abonelik erişimidir. [Resmî OpenAI belgesi](https://learn.chatgpt.com/docs/auth) abonelik girişi ile API anahtarı kullanımını ayrı seçenekler olarak tanımlar.

## Hazırlanan içerik

- Yerel kaynaklar, mevcut ders kartları ve internet araştırması `rag/` altındaki aranabilir bilgi bankasındadır.
- `uzmanlik_programi/UZMANLIK_PLANI.md`: 20 konu modülü, üretici kaynakları ve ayrı sınav düzeni.
- `orchestration/policy.json`: yerelde kalma, Astra’ya devir ve geri dönme kuralları.
- `prompts/local_engineer.txt`: kısa yerel işçi talimatı.
- `tools/local_worker.py`: API kullanmayan yerel bilgi/yanıt ve devir prototipi. Henüz Studio’da işlemleri kendi başına çalıştıran bir araç bağdaştırıcısı değildir.
- `runtime/requests/`: sınırlı ilk kontrol görevleri. Sonuçlar `runtime/runs/` altında ayrı tutulur.

## Token tasarrufu nasıl sağlanacak?

Dosya tarama, bilgi arama, iş emrindeki uygulama adımları ve belirlenmiş kontroller yerelde yapılır. Tekrar eden geçerli görevler gruplanır. Astra’ya bütün kaynak ve log değil, görev farkı ve gerekli kanıt özeti döner. Aynı hatada ücretli-yerel döngüsü tekrarlanmaz; tek somut karar istenir. Kullanım ölçülmeden tasarruf yüzdesi verilmez.

## Eğitim durumu

Hazır ücretsiz temel model olarak Qwen3-14B Q4_K_M seçildi; bu tercih bu bilgisayarda denenmek üzere bir başlangıç adayıdır, nihai kalite kararı değildir. [Üreticinin model kartı](https://huggingface.co/Qwen/Qwen3-14B-GGUF) Apache-2.0 lisansını belirtir. İnternet yalnız kaynak ve model dosyasını almak için kullanılır; yerel çıkarım çevrimdışıdır.

Bilgi bankasına kaynak eklemek model ağırlığı eğitimi değildir. Özel eğitim için gerçek görev kayıtları ve önce/sonra sınamaları gerekir. Henüz “ordinaryüs seviyesine ulaştı” veya “Astra kadar güvenilir” sonucu yoktur. Bu kaliteye yaklaşma hedefi, öğrenilen işlerin doğrulanmasıyla ilerler.

Bu prototip bu aktif sohbetten çağrılır. Arka planda Astra’yı kendiliğinden uyandıran veya farklı ücretli modele otomatik mesaj gönderen düzenek kurulmuş değildir. Dönen devir paketi burada değerlendirilir; kapsamı belli yeni görev yeniden yerele verilir.
