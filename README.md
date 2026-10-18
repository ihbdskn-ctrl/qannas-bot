# Qannas Phone Bot — إشارات XAUUSD فقط

نسخة تعمل من الهاتف فقط: لا تحتاج MT5 Desktop ولا مكتبة `MetaTrader5` ولا تسجيل دخول MT5. يجلب السعر من Yahoo Finance عبر `yfinance`، ويحلل الشموع ويرسل إشارات عربية إلى Telegram. التنفيذ يدوي بالكامل من تطبيق Exness على الهاتف.

## ما الذي تفعله النسخة؟

- فحص XAUUSD كل 5 دقائق افتراضياً على شموع 15 دقيقة.
- الاستراتيجية: اتجاه EMA 20/50، زخم RSI 14، تقاطع MACD، ووقف متكيف مع ATR 14.
- ترسل BUY/SELL فقط عند اكتمال شمعة وبثقة لا تقل عن الحد المحدد.
- كل إشارة تحتوي دخولاً ووقفاً وهدفاً ومبررات التحليل.
- أزرار `اعتماد الإشارة` و`إلغاء الإشارة` داخل Telegram. الاعتماد لا يفتح صفقة؛ يسجل فقط أن المستخدم قرر التنفيذ اليدوي.
- يمنع تكرار نفس الإشارة ويحتفظ بآخر حالة في `data/state.json`.

> ملاحظة البيانات: `XAUUSD=X` من Yahoo هو مصدر تسعير خارجي وقد يختلف قليلاً عن سعر Exness. افحص السعر في Exness قبل التنفيذ اليدوي. يمكن تغيير `YF_SYMBOL` إلى `GC=F` إذا كان رمز XAUUSD غير متاح.

## تشغيل محلي للاختبار

```bash
cp .env.example .env
# ضع توكن Telegram الحقيقي في .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn qannas.app:app --host 0.0.0.0 --port 10000
```

للتشغيل المحلي، يمكن استخدام polling بدلاً من webhook بوضع `PUBLIC_BASE_URL=` ثم تشغيل:

```bash
python -m qannas.polling
```

## نشر Render

1. ارفع هذا المجلد إلى GitHub.
2. أنشئ Web Service من المستودع أو استخدم `render.yaml`.
3. أضف `TELEGRAM_BOT_TOKEN` في Environment Variables.
4. ضع رابط الخدمة النهائي في `PUBLIC_BASE_URL` مثل `https://qannas-phone-bot.onrender.com`.
5. افتح البوت في Telegram وأرسل `/start`.

الخدمة تحتوي `/health` حتى يبقى Render قادراً على فحصها. تشغيل Render المجاني قد يتوقف أو ينام حسب سياسة المنصة؛ لا يوجد ضمان uptime تجاري.

## نشر Replit

استورد المستودع، أضف المتغيرات من `.env.example` إلى Secrets، ثم شغّل:

```bash
uvicorn qannas.app:app --host 0.0.0.0 --port 10000
```

ضع رابط Replit العام في `PUBLIC_BASE_URL` وأعد التشغيل.

## إعدادات MT5 المرجعية

`MT5_LOGIN_REFERENCE=472883977` و`MT5_SERVER_REFERENCE=Exness-MT5Trial16` و`MT5_SYMBOL_REFERENCE=XAUUSD` موجودة للتوثيق فقط، ولا يتم استخدامها للاتصال بأي محطة MT5.

## تنبيه تداول

هذه أداة تحليل وإشارات وليست نصيحة مالية. لا تنفذ إشارة قبل التحقق من السعر والسبريد وحجم العقد وإدارة المخاطر في Exness. لا توجد أوامر آلية ولا ضمان للربح.
