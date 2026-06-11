import logging
import time

from google import genai

from app.config import get_settings
from app.models.sensor_data import SensorData

logger = logging.getLogger(__name__)
GEMINI_RETRY_DELAY_SECONDS = 3600
_gemini_disabled_until = 0.0


def _gemini_is_in_cooldown() -> bool:
    return time.monotonic() < _gemini_disabled_until


def _remember_gemini_failure(exc: Exception) -> str:
    global _gemini_disabled_until

    error_text = str(exc)
    if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text or "quota" in error_text.lower():
        _gemini_disabled_until = time.monotonic() + GEMINI_RETRY_DELAY_SECONDS
        return "fallback-gemini-quota"

    return "fallback-gemini-error"


def _fallback_recommendation(sensor_data: SensorData) -> str:
    irrigation = (
        "মাটির আর্দ্রতা ৩০ শতাংশের নিচে, তাই দ্রুত সেচ দিন।"
        if sensor_data.soil_moisture < 30
        else "মাটির আর্দ্রতা গ্রহণযোগ্য, আপাতত সেচ বন্ধ রাখুন।"
    )
    return (
        "১. মাটির অবস্থা: সেন্সর ডেটা অনুযায়ী ক্ষেত পর্যবেক্ষণযোগ্য অবস্থায় আছে। "
        f"বর্তমান মাটির আর্দ্রতা {sensor_data.soil_moisture:.1f}%।\n"
        f"২. সেচ পরামর্শ: {irrigation}\n"
        "৩. সার পরামর্শ: বাস্তব NPK সেন্সর রিডিং অনুযায়ী নাইট্রোজেন, ফসফরাস ও পটাশিয়ামের "
        "ভারসাম্য দেখে সার প্রয়োগ করুন।\n"
        "৪. রোগের ঝুঁকি: অতিরিক্ত আর্দ্রতা ও উচ্চ তাপমাত্রা থাকলে ছত্রাকের ঝুঁকি বাড়তে পারে।\n"
        "৫. কৃষকের করণীয়: LCD ও ড্যাশবোর্ডে নিয়মিত ডেটা দেখুন, পাম্পের অবস্থা যাচাই করুন, "
        "এবং মাঠে হাতে মাটি পরীক্ষা করে সিদ্ধান্ত নিশ্চিত করুন।"
    )


def generate_recommendation(sensor_data: SensorData) -> tuple[str, str]:
    settings = get_settings()
    if not settings.gemini_api_key:
        return _fallback_recommendation(sensor_data), "fallback-no-gemini-key"
    if _gemini_is_in_cooldown():
        return _fallback_recommendation(sensor_data), "fallback-gemini-quota"

    prompt = f"""
Analyze this smart agriculture sensor reading.

Real sensor values from the ESP32 field device:
- DHT11 Temperature: {sensor_data.temperature:.2f} °C
- DHT11 Humidity: {sensor_data.humidity:.2f} %
- Soil Moisture: {sensor_data.soil_moisture:.2f} %
- Nitrogen: {sensor_data.nitrogen:.2f}
- Phosphorus: {sensor_data.phosphorus:.2f}
- Potassium: {sensor_data.potassium:.2f}

Provide:
1. Soil condition
2. Irrigation recommendation
3. Fertilizer recommendation
4. Disease risk
5. Action for farmer

Return the response in Bangla. Treat temperature, humidity, soil moisture, nitrogen, phosphorus, potassium, and pump status as real field readings.
"""
    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    except Exception as exc:
        source = _remember_gemini_failure(exc)
        logger.warning("Gemini recommendation generation failed: %s", exc)
        return _fallback_recommendation(sensor_data), source

    return response.text or _fallback_recommendation(sensor_data), "gemini"


def _fallback_chat_reply(sensor_data: SensorData | None, message: str) -> str:
    normalized = message.strip().lower()
    greetings = {"hi", "hello", "hey", "salam", "assalamualaikum", "আসসালামু আলাইকুম", "হ্যালো", "হাই"}
    if normalized in greetings:
        return "হ্যালো! আমি আপনার Bangla AI সহকারী। আপনি যেকোনো প্রশ্ন করতে পারেন, আমি বাংলায় উত্তর দেব।"

    crop_keywords = (
        "fosol",
        "fasal",
        "crop",
        "crops",
        "ধান",
        "চাল",
        "গম",
        "সবজি",
        "ফসল",
        "কি হবে",
        "কী হবে",
        "লাগাব",
        "চাষ",
    )
    weather_keywords = (
        "weather",
        "abohawa",
        "temperature",
        "humidity",
        "rain",
        "বৃষ্টি",
        "আবহাওয়া",
        "আবহাওয়া",
        "তাপমাত্রা",
        "আর্দ্রতা",
    )
    field_status_keywords = (
        "field",
        "khet",
        "khamar",
        "status",
        "condition",
        "obostha",
        "ক্ষেত",
        "খেত",
        "জমি",
        "বর্তমান",
        "অবস্থা",
        "কেমন",
    )
    farming_keywords = (
        "sensor",
        "soil",
        "moisture",
        "temperature",
        "humidity",
        "npk",
        "pump",
        "crop",
        "farm",
        "irrigation",
        "fertilizer",
        "সেন্সর",
        "মাটি",
        "আর্দ্রতা",
        "তাপমাত্রা",
        "এনপিকে",
        "পাম্প",
        "ফসল",
        "সেচ",
        "সার",
        "কৃষি",
        "ক্ষেত",
        "খেত",
        "জমি",
        "fosol",
        "khet",
        "abohawa",
        "weather",
        "obostha",
    )
    asks_about_crop = any(keyword in normalized for keyword in crop_keywords)
    asks_about_weather = any(keyword in normalized for keyword in weather_keywords)
    asks_about_field_status = any(keyword in normalized for keyword in field_status_keywords)
    asks_about_field = (
        asks_about_crop
        or asks_about_weather
        or asks_about_field_status
        or any(keyword in normalized for keyword in farming_keywords)
    )

    if not asks_about_field:
        return (
            f"আপনার প্রশ্ন: {message}\n\n"
            "আমি বাংলায় সাহায্য করতে প্রস্তুত। প্রশ্নটি একটু বিস্তারিত লিখলে আমি আরও ভালোভাবে উত্তর দিতে পারব।"
        )

    if not sensor_data:
        return (
            f"আপনার প্রশ্ন: {message}\n\n"
            "এখন কোনো সর্বশেষ সেন্সর ডেটা পাওয়া যাচ্ছে না। ESP32 ডিভাইস অনলাইন আছে কি না, "
            "WiFi সংযোগ এবং ব্যাকএন্ডে ডেটা পাঠানো হচ্ছে কি না পরীক্ষা করুন।"
        )

    irrigation = (
        "মাটির আর্দ্রতা কম, তাই পাম্প চালু রাখা বা দ্রুত সেচ দেওয়া ভালো।"
        if sensor_data.soil_moisture < 30
        else "মাটির আর্দ্রতা এখন গ্রহণযোগ্য, তাই আপাতত সেচের দরকার নেই।"
    )

    if asks_about_crop:
        return (
            f"আপনার প্রশ্ন: {message}\n\n"
            f"বর্তমান ডেটা অনুযায়ী তাপমাত্রা {sensor_data.temperature:.1f}°C, "
            f"আর্দ্রতা {sensor_data.humidity:.1f}% এবং মাটির আর্দ্রতা "
            f"{sensor_data.soil_moisture:.1f}%। এই অবস্থায় ধান, পাট, ডাঁটা শাক, "
            "লাল শাক, পালং শাক, মরিচ, বেগুন বা ঢেঁড়সের মতো গরম ও আর্দ্র আবহাওয়ার "
            "ফসল ভালো হতে পারে। জমিতে পানি জমে থাকলে সবজির জন্য উঁচু বেড বানান। "
            "স্থানীয় মৌসুম ও বাজারদর দেখে চূড়ান্ত ফসল নির্বাচন করুন।"
        )

    if asks_about_weather:
        return (
            f"আপনার প্রশ্ন: {message}\n\n"
            "আমি বাইরের আবহাওয়ার লাইভ ইন্টারনেট রিপোর্ট দেখছি না, তবে আপনার ক্ষেতের "
            f"DHT11 সেন্সর অনুযায়ী এখন তাপমাত্রা {sensor_data.temperature:.1f}°C এবং "
            f"বাতাসের আর্দ্রতা {sensor_data.humidity:.1f}%। আর্দ্রতা বেশি হলে ছত্রাকের "
            "ঝুঁকি বাড়তে পারে, তাই বাতাস চলাচল ভালো রাখুন এবং পাতায় অতিরিক্ত পানি জমতে দেবেন না।"
        )

    if asks_about_field_status:
        return (
            f"আপনার প্রশ্ন: {message}\n\n"
            f"আপনার ক্ষেতের বর্তমান অবস্থা: তাপমাত্রা {sensor_data.temperature:.1f}°C, "
            f"আর্দ্রতা {sensor_data.humidity:.1f}%, মাটির আর্দ্রতা "
            f"{sensor_data.soil_moisture:.1f}%, N {sensor_data.nitrogen:.1f}, "
            f"P {sensor_data.phosphorus:.1f}, K {sensor_data.potassium:.1f}। "
            f"{irrigation} আর্দ্রতা বেশি থাকলে রোগের লক্ষণ আছে কি না পাতায় নজর রাখুন।"
        )

    return (
        f"আপনার প্রশ্ন: {message}\n\n"
        "সর্বশেষ সেন্সর ডেটা অনুযায়ী: "
        f"তাপমাত্রা {sensor_data.temperature:.1f}°C, আর্দ্রতা {sensor_data.humidity:.1f}%, "
        f"মাটির আর্দ্রতা {sensor_data.soil_moisture:.1f}%, "
        f"N {sensor_data.nitrogen:.1f}, P {sensor_data.phosphorus:.1f}, K {sensor_data.potassium:.1f}। "
        f"{irrigation}"
    )


def generate_chat_reply(sensor_data: SensorData | None, message: str) -> tuple[str, str]:
    settings = get_settings()
    if not settings.gemini_api_key:
        return _fallback_chat_reply(sensor_data, message), "fallback-no-gemini-key"
    if _gemini_is_in_cooldown():
        return _fallback_chat_reply(sensor_data, message), "fallback-gemini-quota"

    sensor_context = "No live sensor reading is available right now."
    if sensor_data:
        sensor_context = f"""
Latest SmartAgri sensor reading, use only when relevant:
- DHT11 Temperature: {sensor_data.temperature:.2f} °C
- DHT11 Humidity: {sensor_data.humidity:.2f} %
- Soil Moisture: {sensor_data.soil_moisture:.2f} %
- Nitrogen: {sensor_data.nitrogen:.2f}
- Phosphorus: {sensor_data.phosphorus:.2f}
- Potassium: {sensor_data.potassium:.2f}
- Pump status: {"ON" if sensor_data.pump_status else "OFF"}
"""

    prompt = f"""
You are a helpful general-purpose chatbot for the SmartAgri web app.
Always reply in Bangla.
Answer any user question naturally and clearly.
If the question is about farming, crops, irrigation, fertilizer, weather, or the SmartAgri system, use the sensor context when relevant.
If the question is not about farming, answer normally in Bangla without forcing agriculture context.

{sensor_context}

User question:
{message}

Reply in clear Bangla. Be concise but helpful.
"""
    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    except Exception as exc:
        source = _remember_gemini_failure(exc)
        logger.warning("Gemini chat generation failed: %s", exc)
        return _fallback_chat_reply(sensor_data, message), source

    return response.text or _fallback_chat_reply(sensor_data, message), "gemini"
