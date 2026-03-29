import streamlit as st
import numpy as np
from PIL import Image
import requests
import pandas as pd

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Smart Farming AI", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
.title {text-align:center; font-size:40px; font-weight:bold; color:#2e7d32;}
.subtitle {text-align:center; color:gray;}
.card {
    background:white; padding:12px; border-radius:12px;
    box-shadow:0px 4px 10px rgba(0,0,0,0.1);
    text-align:center;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🌱 Smart Farming AI Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-based crop recommendation system</div>', unsafe_allow_html=True)

# ---------------- SOIL ----------------
def predict_soil(img):
    img = np.array(img)
    if img.std() > 60 or img.mean() < 30 or img.mean() > 220:
        return None
    if img.mean() < 80:
        return "Black Soil"
    elif img.mean() < 150:
        return "Red Soil"
    else:
        return "Alluvial Soil"

# ---------------- LOCATION ----------------
def get_location(user_input):
    try:
        # PINCODE
        if user_input.isdigit() and len(user_input) == 6:
            url = f"https://api.zippopotam.us/in/{user_input}"
            res = requests.get(url, timeout=5).json()

            lat = res['places'][0]['latitude']
            lon = res['places'][0]['longitude']

            # Reverse geocode
            geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
            geo = requests.get(geo_url, timeout=5).json()

            address = geo.get("address", {})
            village = address.get("village") or address.get("town") or address.get("city") or "Unknown"

            return {"name": village, "lat": float(lat), "lon": float(lon)}

        # CITY INPUT
        return {"name": user_input, "lat": None, "lon": None}

    except:
        return None

# ---------------- WEATHER ----------------
API_KEY = "12c4705025277a09b280837d6798931d"

def get_weather(location):
    try:
        if location["lat"]:
            url = f"http://api.openweathermap.org/data/2.5/forecast?lat={location['lat']}&lon={location['lon']}&appid={API_KEY}&units=metric"
        else:
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={location['name']}&appid={API_KEY}&units=metric"

        data = requests.get(url).json()

        current = data["list"][0]

        forecast = []
        for i in range(0, 40, 8):
            forecast.append({
                "temp": data["list"][i]["main"]["temp"],
                "humidity": data["list"][i]["main"]["humidity"],
                "rain": data["list"][i].get("rain", {}).get("3h", 0)
            })

        return current, forecast

    except:
        return None, None

# ---------------- SMART CROPS ----------------
def get_crops(soil, weather):
    temp = weather["temp"]
    rain = weather["rain"]

    crops = []

    if rain > 50:
        crops.append("Rice")

    if temp < 30:
        crops.append("Wheat")

    if temp > 25 and rain < 50:
        crops.append("Cotton")

    if rain > 40 and temp > 20:
        crops.append("Sugarcane")

    if rain < 30:
        crops.append("Millets")

    if 20 < rain < 60:
        crops.append("Pulses")

    # Soil filtering
    if soil == "Black Soil":
        crops = [c for c in crops if c in ["Cotton","Sugarcane","Wheat"]]

    elif soil == "Red Soil":
        crops = [c for c in crops if c in ["Millets","Pulses"]]

    elif soil == "Alluvial Soil":
        crops = [c for c in crops if c in ["Rice","Wheat"]]

    return list(set(crops))

# ---------------- FARM DATA ----------------
CROP_DATA = {
    "Rice": {"yield": 2.5, "price": 20000, "cost": 15000},
    "Wheat": {"yield": 3.0, "price": 18000, "cost": 12000},
    "Cotton": {"yield": 2.0, "price": 25000, "cost": 18000},
    "Sugarcane": {"yield": 40, "price": 3000, "cost": 25000},
    "Millets": {"yield": 1.5, "price": 12000, "cost": 8000},
    "Pulses": {"yield": 1.2, "price": 15000, "cost": 9000}
}

def calculate(crop, area):
    d = CROP_DATA[crop]
    y = d["yield"]
    p = d["price"]
    c = d["cost"]

    total_yield = y * area
    revenue = total_yield * p
    total_cost = c * area
    profit = revenue - total_cost

    return y, p, c, total_yield, revenue, total_cost, profit

# ---------------- IMAGES ----------------
CROP_IMAGES = {
    "Rice": "https://t3.ftcdn.net/jpg/10/18/41/42/360_F_1018414204_slajqwEJK41TZ9N7c9V55N8jgu0jnNJB.jpg.jpg",
    "Wheat": "https://t4.ftcdn.net/jpg/06/22/04/67/360_F_622046735_EBl0lGLXovA1c2gDSXvuzoDqa8XbpvRQ.jpg.jpg",
    "Cotton": "https://t4.ftcdn.net/jpg/06/84/31/79/360_F_684317966_Pn9qU1DEfW5zpwoj25znJ1i0VdaOM2Px.jpg",
    "Sugarcane": "https://thumbs.dreamstime.com/b/black-sugarcane-stalks-22124536.jpg.jpg",
    "Maize": "https://media.istockphoto.com/id/1485792634/photo/ripe-yellow-corn-cob-on-the-field.jpg?s=612x612&w=0&k=20&c=5Lhbh5a15DNMdyaxBPGR4XAIjTPXz1Ct52i2WcoVOQs=.jpg",
    "Groundnut":"https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRJpy-_MQaIlV5c6dTIZeT9haptAvFzupH5Pg&s.jpg",
    "Millets": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRWrGNSigpADMrftzaLpMUBeKpObTUjHW6lHg&s.jpg",
    "Pulses": "https://chrysalishigh.com/wp-content/uploads/2024/01/pulses.jpg"
}

# ---------------- INPUT ----------------
st.markdown("### 📥 Enter Details")

col1, col2 = st.columns(2)

with col1:
    img_file = st.file_uploader("Upload Soil Image", type=["jpg","png","jpeg"])

with col2:
    location_input = st.text_input("Enter Village / City OR Pincode")

area = st.number_input("Enter Farm Area (hectares)", min_value=1.0, value=1.0)

# ---------------- BUTTON ----------------
if st.button("🚀 Analyze Farm"):

    if not img_file or not location_input:
        st.error("Enter all inputs")
        st.stop()

    location = get_location(location_input)

    if not location:
        st.error("Invalid location")
        st.stop()

    st.success(f"📍 Location: {location['name']}")

    # SHOW IMAGE
    image = Image.open(img_file)
    st.image(image, caption="Uploaded Soil Image", width=300)

    soil = predict_soil(image)

    if not soil:
        st.error("Not a soil image")
        st.stop()

    st.success(f"🌱 Soil Type: {soil}")

    current, forecast = get_weather(location)

    if not current:
        st.error("Weather error")
        st.stop()

    # WEATHER
    st.subheader("🌦️ Weather")
    c1,c2,c3 = st.columns(3)
    c1.metric("Temp", f"{current['main']['temp']}°C")
    c2.metric("Humidity", f"{current['main']['humidity']}%")
    c3.metric("Rain", f"{current.get('rain',{}).get('3h',0)} mm")

    # GRAPH
    st.subheader("📊 Forecast")
    df = pd.DataFrame(forecast)
    st.line_chart(df)

    # CROPS
    crops = get_crops(soil, forecast[0])

    if len(crops) == 0:
        st.warning("No suitable crops found")
    else:
        st.subheader("🌾 Recommended Crops")

        cols = st.columns(len(crops))

        for i, crop in enumerate(crops):
            with cols[i]:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.image(CROP_IMAGES[crop], width=200)
                st.markdown(f"### {crop}")

                y,p,c,ty,tr,tc,profit = calculate(crop, area)

                st.write(f"Yield/hectare: {y} tons")
                st.write(f"Price/ton: ₹{p}")
                st.write(f"Cost/hectare: ₹{c}")
                st.write("---")
                st.write(f"Total Yield: {ty} tons")
                st.write(f"Revenue: ₹{tr}")
                st.write(f"Cost: ₹{tc}")
                st.success(f"Profit: ₹{profit}")

                st.markdown('</div>', unsafe_allow_html=True)