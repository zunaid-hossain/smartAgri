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
        "৩. সার পরামর্শ: NPK মানগুলো বর্তমানে সিমুলেটেড; বাস্তব NPK সেন্সর ঠিক হলে "
        "চূড়ান্ত সার প্রয়োগের সিদ্ধান্ত নিন।\n"
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

Real sensor values:
- Temperature: {sensor_data.temperature:.2f} °C
- Humidity: {sensor_data.humidity:.2f} %
- Soil Moisture: {sensor_data.soil_moisture:.2f} %

Simulated NPK values because the real NPK sensor is defective:
- Nitrogen: {sensor_data.nitrogen:.2f}
- Phosphorus: {sensor_data.phosphorus:.2f}
- Potassium: {sensor_data.potassium:.2f}

Provide:
1. Soil condition
2. Irrigation recommendation
3. Fertilizer recommendation
4. Disease risk
5. Action for farmer

Return the response in Bangla. Clearly mention that NPK values are simulated.
"""
    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text or _fallback_recommendation(sensor_data), "gemini"
