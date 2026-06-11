from google import genai

from app.config import get_settings
from app.models.sensor_data import SensorData


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
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text or _fallback_recommendation(sensor_data), "gemini"


def _fallback_chat_reply(sensor_data: SensorData, message: str) -> str:
    irrigation = (
        "মাটির আর্দ্রতা কম, তাই পাম্প চালু রাখা বা দ্রুত সেচ দেওয়া ভালো।"
        if sensor_data.soil_moisture < 30
        else "মাটির আর্দ্রতা এখন গ্রহণযোগ্য, তাই আপাতত সেচের দরকার নেই।"
    )
    return (
        f"আপনার প্রশ্ন: {message}\n\n"
        "সর্বশেষ সেন্সর ডেটা দেখে বলছি: "
        f"তাপমাত্রা {sensor_data.temperature:.1f}°C, আর্দ্রতা {sensor_data.humidity:.1f}%, "
        f"মাটির আর্দ্রতা {sensor_data.soil_moisture:.1f}%, "
        f"N {sensor_data.nitrogen:.1f}, P {sensor_data.phosphorus:.1f}, K {sensor_data.potassium:.1f}। "
        f"{irrigation} মাঠের বাস্তব অবস্থা মিলিয়ে সিদ্ধান্ত নিন।"
    )


def generate_chat_reply(sensor_data: SensorData, message: str) -> tuple[str, str]:
    settings = get_settings()
    if not settings.gemini_api_key:
        return _fallback_chat_reply(sensor_data, message), "fallback-no-gemini-key"

    prompt = f"""
You are a Bangla smart agriculture assistant. Answer the farmer's question in Bangla.
Use the latest real-time ESP32 sensor reading as context.

Latest sensor reading:
- DHT11 Temperature: {sensor_data.temperature:.2f} °C
- DHT11 Humidity: {sensor_data.humidity:.2f} %
- Soil Moisture: {sensor_data.soil_moisture:.2f} %
- Nitrogen: {sensor_data.nitrogen:.2f}
- Phosphorus: {sensor_data.phosphorus:.2f}
- Potassium: {sensor_data.potassium:.2f}
- Pump status: {"ON" if sensor_data.pump_status else "OFF"}

Farmer question:
{message}

Reply in clear, practical Bangla. Keep the answer concise and useful for field action.
"""
    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text or _fallback_chat_reply(sensor_data, message), "gemini"
