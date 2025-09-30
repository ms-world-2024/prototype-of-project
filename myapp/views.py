import os
import random
import datetime
import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from myproject import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db.models import Avg, Count 

from .models import Review 

# --- Authentication Views ---

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect("signup")
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect("signup")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect("signup")
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        login(request, user)
        messages.success(request, "Account created successfully!")
        return redirect("home")
    return render(request, "myapp/signup.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password")
            return redirect("login")
    return render(request, "myapp/login.html")

def logout_view(request):
    logout(request)
    return redirect("login")

# --- Page Rendering Views ---

@login_required(login_url="login")
def home_view(request):
    return render(request, "myapp/pages/home_page.html")

@login_required(login_url="login")
def crops_view(request):
    return render(request, "myapp/pages/crops_page.html")

@login_required(login_url="login")
def market_view(request):
    return render(request, "myapp/pages/market_page.html")

@login_required(login_url="login")
def scanner_view(request):
    return render(request, "myapp/pages/scanner_page.html")

@login_required(login_url="login")
def dbt_view(request):
    return render(request, "myapp/pages/dbt_page.html")

@login_required(login_url="login")
def pest_view(request):
    # This view renders the page with the crop list selector
    return render(request, "myapp/pages/pest_page.html")

@login_required(login_url="login")
def organic_main_view(request):
    return render(request, "myapp/pages/organic_main_page.html")

@login_required(login_url="login")
def videos_view(request):
    return render(request, "myapp/pages/videos_page.html")

@login_required(login_url="login")
def agri_news_view(request):
    return render(request, "myapp/pages/agri_news_page.html")

@login_required(login_url="login")
def ctoc_view(request):
    return render(request, "myapp/pages/ctoc_page.html")

@login_required(login_url="login")
def jobs_view(request):
    return render(request, "myapp/pages/jobs_page.html")

@login_required(login_url="login")
def benefits_view(request):
    return render(request, "myapp/pages/benefits_page.html")

@login_required(login_url="login")
def organic_pest_view(request):
    return render(request, "myapp/pages/organic_pest_page.html")
    
@login_required(login_url="login")
def about_organic_view(request):
    return render(request, "myapp/pages/about_organic_page.html")

# --- Review Pages ---
@login_required(login_url="login")
def submit_review(request):
    if request.method == 'POST':
        review_text = request.POST.get('review_text')
        rating = request.POST.get('rating')

        if Review.objects.filter(user=request.user).exists():
            messages.error(request, "You have already submitted a review.")
            return redirect('submit_review')
        Review.objects.create(
            user=request.user,
            review_text=review_text,
            rating=rating
        )
        
        messages.success(request, "Thank you for your valuable feedback! Your review has been submitted.")
        return redirect('submit_review')
        
    return render(request, "myapp/pages/review_page.html")

def view_reviews(request):
    all_reviews = Review.objects.all().order_by('-submission_date')
    
    review_stats = all_reviews.aggregate(
        average_rating=Avg('rating'),
        total_reviews=Count('id')
    )
    
    context = {
        'reviews': all_reviews,
        'total_reviews': review_stats['total_reviews'],
        'average_rating': round(review_stats['average_rating'], 1) if review_stats['average_rating'] else 0
    }
    return render(request, "myapp/pages/reviews_list.html", context)


# --- API Endpoints ---

def get_weather(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    if not lat or not lon:
        return JsonResponse({'error': 'Latitude and longitude are required.'}, status=400)
    OPENWEATHER_API_KEY = settings.OPENWEATHER_API_KEY
    url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&exclude=minutely,hourly"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        current_weather = {
            'temp': round(data['current']['temp']), 'humidity': data['current']['humidity'],
            'condition': data['current']['weather'][0]['description'].title(),
            'wind_speed': round(data['current']['wind_speed']),
            'rainfall': round(data['current'].get('rain', {}).get('1h', 0)),
            'uv_index': data['current']['uvi'], 'location': 'Your Current Location',
        }
        forecast_list = []
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        weather_icons = {
            'clear sky': '☀️', 'few clouds': '⛅', 'scattered clouds': '☁️',
            'broken clouds': '☁️', 'shower rain': '🌧️', 'rain': '🌧️',
            'thunderstorm': '⛈️', 'snow': '❄️', 'mist': '🌫️',
            'light rain': '🌧️', 'overcast clouds': '☁️',
        }
        for i, day in enumerate(data['daily'][:10]):
            forecast_list.append({
                'day': 'Today' if i == 0 else days[datetime.datetime.fromtimestamp(day['dt']).weekday()],
                'icon': weather_icons.get(data['daily'][i]['weather'][0]['description'], '❓'),
                'high': round(data['daily'][i]['temp']['max']), 'low': round(data['daily'][i]['temp']['min']),
                'rain': round(data['daily'][i].get('pop', 0) * 100),
            })
        return JsonResponse({'current': current_weather, 'forecast': forecast_list})
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f"Failed to fetch weather data: {e}"}, status=500)
    except KeyError:
        return JsonResponse({'error': 'Invalid weather data format received.'}, status=500)

def get_market_prices(request):
    market_data = {
        'cereals': [
            {'name': 'Wheat', 'price': 2125 + random.randint(-50, 50), 'change': random.randint(-5, 5)},
            {'name': 'Rice (Common)', 'price': 2040 + random.randint(-40, 40), 'change': random.randint(-4, 4)},
            {'name': 'Basmati Rice', 'price': 4500 + random.randint(-100, 100), 'change': random.randint(-7, 7)},
        ],
        'vegetables': [
            {'name': 'Tomato', 'price': 25 + random.randint(-10, 10), 'change': random.randint(-4, 4), 'unit': 'kg'},
            {'name': 'Onion', 'price': 35 + random.randint(-7, 7), 'change': random.randint(-3, 3), 'unit': 'kg'},
            {'name': 'Potato', 'price': 22 + random.randint(-5, 5), 'change': random.randint(-2, 2), 'unit': 'kg'},
        ],
        'pulses': [
            {'name': 'Chana (Gram)', 'price': 5500 + random.randint(-150, 150), 'change': random.randint(-10, 10)},
            {'name': 'Moong', 'price': 7200 + random.randint(-200, 200), 'change': random.randint(-12, 12)},
        ]
    }
    return JsonResponse(market_data)

def get_crop_details(request, crop_name):
    # This serves the 16-point data for both /crops/ and the base data for /pest/
    crop_data = {
    'wheat': {
        'title': 'Wheat Cultivation (Rabi Crop)',
        'identity_context': 'Triticum aestivum. One of the oldest cultivated crops, essential for global food security, originated in the Fertile Crescent.',
        'soil_requirements': 'Best grown on loamy to clay-loam soils. Needs well-drained soil. Optimal pH is 6.0 to 7.5.',
        'climate_requirements': 'Prefers cool weather (14°C to 18°C) during sowing, a short warm phase for grain filling, and clear sunny weather at maturity.',
        'water_irrigation_needs': 'Requires 450-600 mm of water. Critical stages are Crown Root Initiation (CRI), tillering, flowering, and dough stage.',
        'varieties': 'Popular: HD 3086, PBW 725, WH 1105. High-yield: Pusa Tej, Karan Vandana (DBW 187).',
        'seed_selection_sowing': 'Seed Rate: 100-125 kg/ha. Sowing Depth: 4-5 cm. Sowing Time: Mid-October to Mid-November (Rabi Season).',
        'nutrient_management': 'Requires NPK in 120:60:40 kg/ha ratio. Apply full P and K, and half N at sowing. Remaining N applied in two splits.',
        'season_of_cultivation': 'Rabi (Winter) season crop. Sown in October-December and harvested in March-April.',
        'land_preparation': 'Requires fine, firm, and moist seedbed. Typically involves 1 deep ploughing followed by 2-3 harrowing and planking (leveling).',
        'process_of_cultivation': 'Land Prep → Sowing (seed drill) → CRI Irrigation → N Fertilizer Split → Flower Irrigation → Harvesting (Combine/Manual) → Threshing.',
        'organic_farming_practices': 'Use Farm Yard Manure (FYM) or compost for soil nutrition. Use crop rotation with legumes (like Mung bean) to fix nitrogen.',
        'harvesting_storage': 'Harvest when grains are hard and moisture is 12-14%. Store in clean, dry bags (jute/polypropylene) in a cool, ventilated area.',
        'estimated_cost': 'Approx. ₹30,000 to ₹35,000 per hectare.',
        'locations_of_cultivation': 'Majorly cultivated in Punjab, Haryana, Uttar Pradesh, and Madhya Pradesh.',
        'pests_affecting': 'Aphids, Termites, Wheat Rusts (Yellow, Brown), Loose Smut, Karnal Bunt.',
        'pest_control_measures': 'Chemical: Propiconazole (for rusts), Imidacloprid (for aphids). Organic: Neem oil spray, biological control (Ladybugs).',
        
    },
    
    'rice': {
        'title': 'Rice Cultivation (Kharif Crop)',
        'identity_context': 'Oryza sativa. A staple cereal grain, known for being a Kharif crop, highly dependent on monsoon rainfall.',
        'soil_requirements': 'Grows best on heavy clay and clay loam soils that retain water well. Optimal pH is 6.0 to 7.5.',
        'climate_requirements': 'Requires high humidity, prolonged sunshine, and assured water supply. Ideal temperature: 25°C to 35°C.',
        'water_irrigation_needs': 'Water intensive. Requires continuous standing water (2-5 cm) for most of the growth period, especially during flowering.',
        'varieties': 'Popular: PR-126, Pusa Basmati 1121. Short-duration: CSR 30 (for high salinity).',
        'seed_selection_sowing': 'Transplanting: Mid-June to Mid-July. Direct Seeding: May/June. Seed Rate: 40-50 kg/ha (transplanted).',
        'nutrient_management': 'NPK in 150:60:40 kg/ha. Nitrogen management is key to prevent lodging.',
        'season_of_cultivation': 'Kharif (Monsoon) season crop. Sown/transplanted in June/July and harvested in September/October.',
        'land_preparation': 'Requires puddling (wet cultivation) to create an impermeable layer in the soil to retain water.',
        'process_of_cultivation': 'Nursery Raising → Puddling → Transplanting → Water Management → Fertilizer Application → Harvesting → Drying.',
        'organic_farming_practices': 'Use Azolla and Blue Green Algae for nitrogen fixation. Hand weeding and crop rotation.',
        'harvesting_storage': 'Harvest when panicles are straw yellow. Store at 12% moisture in dry, pest-free silos or bags.',
        'estimated_cost': 'Approx. ₹40,000 to ₹50,000 per hectare.',
        'locations_of_cultivation': 'Majorly cultivated in West Bengal, Punjab, Uttar Pradesh, and Andhra Pradesh.',
        'pests_affecting': 'Stem Borer, Brown Plant Hopper (BPH), Rice Blast (fungal), Bacterial Leaf Blight.',
        'pest_control_measures': 'Chemical: Carbofuran (for stem borer). Chlorpyrifos for brown plant hopper. Neem-based pesticides, water-level management.',
    },
    'maize': {
        'title': 'Maize (Corn) Cultivation',
        'identity_context': 'Zea mays. Used for food, feed, and industrial purposes. Highly adaptable crop.',
        'soil_requirements': 'Deep, fertile, well-drained loamy soils. pH 5.5 to 7.5.',
        'climate_requirements': 'Grows in both Kharif and Rabi. Needs high temperatures (21°C to 27°C) and moderate rainfall.',
        'water_irrigation_needs': 'Needs 600-800 mm of water. Critical stages: silking, tasseling, and dough stage.',
        'varieties': 'Various hybrids for specific regions and uses (e.g., sweet corn, field corn).',
        'seed_selection_sowing': 'Seed Rate: 20-25 kg/ha. Sowing Depth: 3-5 cm.',
        'nutrient_management': 'NPK in 120:60:40 kg/ha ratio, primarily nitrogen.',
        'season_of_cultivation': 'Kharif, Rabi, and Zaid (Spring) seasons.',
        'land_preparation': 'Fine tilth, typically 2-3 ploughings and leveling.',
        'process_of_cultivation': 'Sowing → Thinning and gap filling → Weeding → Side-dressing fertilizer → Irrigation → Harvesting.',
        'organic_farming_practices': 'Use legume intercropping and compost. Use Bt corn (if allowed) for pest resistance.',
        'harvesting_storage': 'Harvest when kernels are hard and moisture is below 20%. Store in dry sheds.',
        'estimated_cost': 'Approx. ₹25,000 to ₹30,000 per hectare.',
        'locations_of_cultivation': 'Karnataka, Andhra Pradesh, Bihar, Maharashtra.',
        'pests_affecting': 'Stem borer, Armyworm, Corn borer, Leaf blight.',
        'pest_control_measures': 'Chemical: Carbaryl (for borers). Organic: Trichoderma viride (fungicide).',
    },
    'barley': {
        'title': 'Barley Cultivation (Rabi Crop)',
        'identity_context': 'Hordeum vulgare. Hardy cereal, mainly used for brewing, feed, and making flour.',
        'soil_requirements': 'Grows in sandy loam to clay loam soils.',
        'climate_requirements': 'Cool, dry climate. Ideal temperature: 12°C to 15°C.',
        'water_irrigation_needs': 'Drought-tolerant, requires less water than wheat (300-400 mm).',
        'varieties': 'RD 2552, BH 902, DWRB 91.',
        'seed_selection_sowing': 'Seed Rate: 75-100 kg/ha. Sowing Time: Mid-October to Mid-November.',
        'nutrient_management': 'NPK in 40:20:20 kg/ha (much lower than wheat).',
        'season_of_cultivation': 'Rabi (Winter) season crop.',
        'land_preparation': 'Similar to wheat, a firm seedbed is preferred.',
        'process_of_cultivation': 'Sowing → Light irrigation → Tillering → Harvesting.',
        'organic_farming_practices': 'Use compost and crop rotation.',
        'harvesting_storage': 'Harvest when the crop turns golden yellow.',
        'estimated_cost': 'Approx. ₹18,000 to ₹22,000 per hectare.',
        'locations_of_cultivation': 'Uttar Pradesh, Rajasthan, Punjab, Haryana.',
        'pests_affecting': 'Loose Smut, Yellow Rust, Aphids.',
        'pest_control_measures': 'Chemical: Seed treatment with Carboxin.',
    },
    'sorghum': {
        'title': 'Sorghum (Jowar) Cultivation',
        'identity_context': 'Sorghum bicolor. Drought-tolerant millet, used for food, feed, and ethanol production.',
        'soil_requirements': 'Wide adaptability, thrives in heavy and light soils, but dislikes very sandy or very heavy clay.',
        'climate_requirements': 'Warm season crop, highly heat and drought tolerant. Ideal temperature: 26°C to 30°C.',
        'water_irrigation_needs': 'Very drought tolerant. Requires 450-550 mm water. Critical stage: flowering.',
        'varieties': 'CSH series (Hybrids).',
        'seed_selection_sowing': 'Seed Rate: 8-10 kg/ha. Sowing Time: Kharif (June/July) and Rabi (September/October).',
        'nutrient_management': 'NPK 80:40:40 kg/ha.',
        'season_of_cultivation': 'Kharif and Rabi seasons.',
        'land_preparation': '2-3 ploughings followed by harrowing and leveling.',
        'process_of_cultivation': 'Sowing → Thinnning → Earthing up → Irrigation → Harvesting.',
        'organic_farming_practices': 'Green manures, Azotobacter treatment for seeds.',
        'harvesting_storage': 'Harvesting: when grains are hard. Storage: dry and moisture-free.',
        'estimated_cost': 'Approx. ₹15,000 to ₹20,000 per hectare.',
        'locations_of_cultivation': 'Maharashtra, Karnataka, Andhra Pradesh, Madhya Pradesh.',
        'pests_affecting': 'Shoot fly, Stem borer, Grain smut, Rust.',
        'pest_control_measures': 'Chemical: Seed treatment with Thiamethoxam.',
    },
    'bajra': {
        'title': 'Bajra (Pearl Millet) Cultivation',
        'identity_context': 'Pennisetum glaucum. The most widely grown type of millet, excellent drought tolerance, high nutritional value.',
        'soil_requirements': 'Best in sandy loam soils but thrives in low-fertility soils. Tolerant to low pH.',
        'climate_requirements': 'Requires hot, dry climate. Highly sensitive to cold and frost. Ideal temperature: 25°C to 35°C.',
        'water_irrigation_needs': 'Highly drought-tolerant, minimum water requirement (250-300 mm).',
        'varieties': 'Hybrid varieties for higher yields.',
        'seed_selection_sowing': 'Sow in July/August at 4-5 kg/ha seed rate.',
        'nutrient_management': 'NPK 80:40:40 kg/ha.',
        'season_of_cultivation': 'Kharif (Monsoon) season crop.',
        'land_preparation': '2-3 shallow cultivations and leveling.',
        'process_of_cultivation': 'Sowing → Thinning → Weeding → Harvesting.',
        'organic_farming_practices': 'Use compost and crop rotation.',
        'harvesting_storage': 'Harvest when grains are hard and dry.',
        'estimated_cost': 'Approx. ₹12,000 to ₹15,000 per hectare.',
        'locations_of_cultivation': 'Rajasthan, Gujarat, Uttar Pradesh, Maharashtra.',
        'pests_affecting': 'Downy mildew, Ergot, Stem borer.',
        'pest_control_measures': 'Chemical: Seed treatment with Metalaxyl.',
    },
    'gram': {
        'title': 'Gram (Chana) Cultivation',
        'identity_context': 'Cicer arietinum. Also known as chickpeas, rich source of protein, used for flour (besan).',
        'soil_requirements': 'Well-drained sandy loam to clay loam soils. Sensitive to salinity.',
        'climate_requirements': 'Cool and dry climate, very sensitive to frost and high temperatures during flowering.',
        'water_irrigation_needs': 'Requires 200-300 mm. Typically rainfed. Critical stage: pre-flowering and pod development.',
        'varieties': 'Kabuli and Desi types. Pusa 372, JG 11.',
        'seed_selection_sowing': 'Seed Rate: 75-100 kg/ha. Sowing Time: October-November (Rabi).',
        'nutrient_management': 'NPK in 20:40:20 kg/ha (low N requirement due to nitrogen fixation).',
        'season_of_cultivation': 'Rabi (Winter) season crop.',
        'land_preparation': 'Fine and friable seedbed, often just one ploughing is sufficient.',
        'process_of_cultivation': 'Sowing → Weeding → Irrigation → Pinching (for bushy growth) → Harvesting.',
        'organic_farming_practices': 'Excellent nitrogen fixer, use Rhizobium culture for seed treatment.',
        'harvesting_storage': 'Harvest when leaves start drying. Storage: grains should be fully dry to prevent pests.',
        'estimated_cost': 'Approx. ₹25,000 to ₹30,000 per hectare.',
        'locations_of_cultivation': 'Madhya Pradesh, Rajasthan, Uttar Pradesh.',
        'pests_affecting': 'Pod borer, Termites, Wilt/Blight.',
        'pest_control_measures': 'Chemical: Quinalphos (for pod borer). Organic: Bt (Bacillus thuringiensis) for borers.',
    },
    'lentil': {
        'title': 'Lentil (Masoor) Cultivation',
        'identity_context': 'Lens culinaris. Highly nutritious legume, often used in Indian dal preparations.',
        'soil_requirements': 'Loam soils are ideal. Highly sensitive to waterlogging.',
        'climate_requirements': 'Cool weather during growth, tolerates frost better than other pulses.',
        'water_irrigation_needs': 'Low water requirement (200-350 mm).',
        'varieties': 'Lens-4076 (Short duration), Pusa Vaibhav.',
        'seed_selection_sowing': 'Seed Rate: 40-60 kg/ha. Sowing Time: October-November.',
        'nutrient_management': 'Requires NPK 20:40:20 kg/ha.',
        'season_of_cultivation': 'Rabi season crop.',
        'land_preparation': 'Similar to gram, requires a fine seedbed.',
        'process_of_cultivation': 'Sowing → Weeding → Irrigation → Harvesting.',
        'organic_farming_practices': 'Rhizobium seed treatment, FYM.',
        'harvesting_storage': 'Harvest when the lower pods turn yellow. Store in dry conditions.',
        'estimated_cost': 'Approx. ₹20,000 to ₹25,000 per hectare.',
        'locations_of_cultivation': 'Madhya Pradesh, Uttar Pradesh, Bihar.',
        'pests_affecting': 'Pod borer, Aphids, Wilt.',
        'pest_control_measures': 'Chemical: Dimethoate (for aphids).',
    },
    'moong': {
        'title': 'Moong (Green Gram) Cultivation',
        'identity_context': 'Vigna radiata. A short-duration pulse crop, commonly used for sprouts and dal.',
        'soil_requirements': 'Sandy loam to loam soils. pH 6.0 to 7.0.',
        'climate_requirements': 'Requires warm weather (25°C to 35°C). Sensitive to cloudy weather during flowering.',
        'water_irrigation_needs': 'Low water need, generally rainfed in Kharif.',
        'varieties': 'Pusa Vishal, SML 668.',
        'seed_selection_sowing': 'Seed Rate: 15-20 kg/ha. Sowing Time: Kharif (June/July) and Zaid (Spring).',
        'nutrient_management': 'NPK 20:40:20 kg/ha.',
        'season_of_cultivation': 'Kharif and Zaid seasons.',
        'land_preparation': 'One deep ploughing and 2-3 harrowings.',
        'process_of_cultivation': 'Sowing → Weeding → Irrigation → Harvesting (multiple pickings).',
        'organic_farming_practices': 'Nitrogen fixer. Often used as a green manure crop.',
        'harvesting_storage': 'Harvesting is done in 2-3 pickings as pods mature unevenly.',
        'estimated_cost': 'Approx. ₹18,000 to ₹22,000 per hectare.',
        'locations_of_cultivation': 'Rajasthan, Maharashtra, Andhra Pradesh.',
        'pests_affecting': 'Yellow Mosaic Virus (YMV), Pod borer, Whitefly.',
        'pest_control_measures': 'Chemical: Imidacloprid (for whitefly). Organic: YMV is controlled by whitefly management.',
    },
    'arhar': {
        'title': 'Arhar/Tur (Pigeon Pea) Cultivation',
        'identity_context': 'Cajanus cajan. A perennial tropical pulse, long duration crop, providing stability to dryland agriculture.',
        'soil_requirements': 'Wide adaptability, deep loamy soils are best. Sensitive to high salinity.',
        'climate_requirements': 'Warm and humid for early growth, dry and warm for maturity. Sensitive to waterlogging.',
        'water_irrigation_needs': 'Drought tolerant, 400-600 mm water requirement.',
        'varieties': 'Pusa 992, UPAS 120.',
        'seed_selection_sowing': 'Seed Rate: 15-20 kg/ha. Sowing Time: June-July (Kharif).',
        'nutrient_management': 'NPK 20:40:20 kg/ha.',
        'season_of_cultivation': 'Kharif season crop (long duration).',
        'land_preparation': 'One deep ploughing and 2-3 harrowing.',
        'process_of_cultivation': 'Sowing → Inter-cultivation → Pod filling → Harvesting.',
        'organic_farming_practices': 'Rhizobium seed treatment, intercropping.',
        'harvesting_storage': 'Harvest when 75-80% pods turn brown. Stored in traditional containers.',
        'estimated_cost': 'Approx. ₹22,000 to ₹28,000 per hectare.',
        'locations_of_cultivation': 'Maharashtra, Karnataka, Madhya Pradesh.',
        'pests_affecting': 'Pod borer, Wilt, Sterility Mosaic.',
        'pest_control_measures': 'Chemical: Endosulfan (for borers, if necessary).',
    },
    'urad': {
        'title': 'Urad (Black Gram) Cultivation',
        'identity_context': 'Vigna mungo. High-protein pulse, mainly used for dal, rich in phosphorus.',
        'soil_requirements': 'Grows well on medium to heavy soils. Tolerant to salinity.',
        'climate_requirements': 'Warm and humid, needs 25°C to 30°C. Tolerates high temperatures.',
        'water_irrigation_needs': '300-400 mm, generally rainfed.',
        'varieties': 'T9, Pant U-19.',
        'seed_selection_sowing': 'Seed Rate: 15-20 kg/ha. Sowing Time: Kharif and Zaid seasons.',
        'nutrient_management': 'NPK 20:40:20 kg/ha.',
        'season_of_cultivation': 'Kharif and Zaid seasons.',
        'land_preparation': 'Fine seedbed, often sown with minimal tillage.',
        'process_of_cultivation': 'Sowing → Weeding → Irrigation → Harvesting (2 pickings).',
        'organic_farming_practices': 'Nitrogen fixer, dual-purpose (pulse and green manure).',
        'harvesting_storage': 'Harvest when most pods are mature. Stored in dry conditions.',
        'estimated_cost': 'Approx. ₹18,000 to ₹23,000 per hectare.',
        'locations_of_cultivation': 'Maharashtra, Uttar Pradesh, Andhra Pradesh.',
        'pests_affecting': 'YMV, Whitefly, Pod borer.',
        'pest_control_measures': 'Chemical: Systemic insecticides for vectors.',
    },
    'mustard': {
        'title': 'Mustard Cultivation',
        'identity_context': 'Brassica spp. Primary oilseed crop in Rabi season, used for cooking oil and animal feed.',
        'soil_requirements': 'Well-drained loamy soils, pH 6.0-7.5.',
        'climate_requirements': 'Cool growing season, sensitive to severe frost. Ideal temperature: 10°C to 25°C.',
        'water_irrigation_needs': 'Low to moderate water needs (200-300 mm).',
        'varieties': 'Pusa Bold, Varuna, RH 30.',
        'seed_selection_sowing': 'Sow in October-November at 5kg/ha seed rate.',
        'nutrient_management': 'NPK 60:40:40 kg/ha. Requires Sulphur for oil synthesis.',
        'season_of_cultivation': 'Rabi (Winter) season crop.',
        'land_preparation': 'Fine seedbed, 1 deep ploughing and 2-3 harrowings.',
        'process_of_cultivation': 'Sowing → Thinning → Irrigation → Fertilizing → Harvesting.',
        'organic_farming_practices': 'Use compost and neem cake.',
        'harvesting_storage': 'Harvest when pods turn yellow. Store in dry, cool conditions.',
        'estimated_cost': 'Approx. ₹15,000 to ₹20,000 per hectare.',
        'locations_of_cultivation': 'Punjab, Rajasthan, Haryana, UP.',
        'pests_affecting': 'Aphids, painted bug.',
        'pest_control_measures': 'Imidacloprid for aphids. Neem oil for organic management.',
    },
    'groundnut': {
        'title': 'Groundnut Cultivation',
        'identity_context': 'Arachis hypogaea. Major oilseed and food crop, rich in protein and oil.',
        'soil_requirements': 'Sandy loam to loamy soils are ideal, needs good drainage. pH 6.0 to 7.5.',
        'climate_requirements': 'Requires warm and humid conditions (25°C to 30°C).',
        'water_irrigation_needs': 'Requires 500-700 mm. Critical stage: pegging (pod formation).',
        'varieties': 'Bolder varieties like GG 20.',
        'seed_selection_sowing': 'Seed Rate: 100-120 kg/ha (bunch type). Sowing Time: Kharif (June/July).',
        'nutrient_management': 'NPK 20:40:40 kg/ha. Requires Calcium (Gypsum) for better pod development.',
        'season_of_cultivation': 'Kharif and Rabi/Summer seasons.',
        'land_preparation': 'Light tillage to keep soil loose for pegging.',
        'process_of_cultivation': 'Sowing → Pegging → Gypsum application → Irrigation → Harvesting.',
        'organic_farming_practices': 'Nitrogen fixer, use organic manures and bio-fertilizers.',
        'harvesting_storage': 'Harvest when most leaves turn yellow. Store in dry and moisture-free conditions.',
        'estimated_cost': 'Approx. ₹30,000 to ₹35,000 per hectare.',
        'locations_of_cultivation': 'Gujarat, Andhra Pradesh, Tamil Nadu.',
        'pests_affecting': 'Aphids, Leaf Spot (Tikka disease), White Grub.',
        'pest_control_measures': 'Chemical: Carbendazim (fungicide). Organic: Trichoderma for soil diseases.',
    },
    'sunflower': {
        'title': 'Sunflower Cultivation',
        'identity_context': 'Helianthus annuus. Highly valued for edible oil, adaptability to various climates and soils.',
        'soil_requirements': 'Wide adaptability, deep fertile soils are ideal. pH 6.5 to 8.0.',
        'climate_requirements': 'Requires a long day, sunny, and warm period. Ideal temperature: 20°C to 25°C.',
        'water_irrigation_needs': 'Moderate water need (500-700 mm). Critical stages: flowering and seed filling.',
        'varieties': 'Hybrids like KBSH 44.',
        'seed_selection_sowing': 'Seed Rate: 8-10 kg/ha. Sowing Time: All seasons (Kharif, Rabi, Zaid).',
        'nutrient_management': 'NPK 60:80:60 kg/ha. Requires Boron for high seed yield.',
        'season_of_cultivation': 'All year round in different parts of India.',
        'land_preparation': '2-3 ploughings and leveling.',
        'process_of_cultivation': 'Sowing → Thinning → Fertilizing → Head development → Harvesting.',
        'organic_farming_practices': 'Use FYM/Compost. Bees are essential for pollination.',
        'harvesting_storage': 'Harvest when the back of the head turns lemon-yellow. Store seeds in moisture-free bins.',
        'estimated_cost': 'Approx. ₹22,000 to ₹28,000 per hectare.',
        'locations_of_cultivation': 'Karnataka, Maharashtra, Andhra Pradesh.',
        'pests_affecting': 'Hairy Caterpillar, Rust, Head rot.',
        'pest_control_measures': 'Chemical: Monocrotophos (for pests).',
    },
    'sesame': {
        'title': 'Sesame (Til) Cultivation',
        'identity_context': 'Sesamum indicum. One of the oldest oilseed crops, highly resistant to drought and short-duration.',
        'soil_requirements': 'Well-drained light to medium textured soils. Cannot tolerate waterlogging.',
        'climate_requirements': 'Tropical crop, requires hot conditions (25°C to 30°C).',
        'water_irrigation_needs': 'Low water needs (300-400 mm). Sensitive to drought during flowering.',
        'varieties': 'T-85, Gujarat Til 2.',
        'seed_selection_sowing': 'Seed Rate: 5-7 kg/ha. Sowing Time: Kharif (June/July).',
        'nutrient_management': 'NPK 50:30:30 kg/ha. Needs Sulphur.',
        'season_of_cultivation': 'Kharif season crop.',
        'land_preparation': 'Fine, friable seedbed.',
        'process_of_cultivation': 'Sowing → Thinning → Inter-cultivation → Capsule development → Harvesting.',
        'organic_farming_practices': 'Use FYM, weeding is critical in early stages.',
        'harvesting_storage': 'Harvest before capsules fully dry out to prevent shattering. Store in a dry place.',
        'estimated_cost': 'Approx. ₹18,000 to ₹22,000 per hectare.',
        'locations_of_cultivation': 'West Bengal, Rajasthan, Madhya Pradesh.',
        'pests_affecting': 'Phyllody (viral disease), Leaf roller/capsule borer.',
        'pest_control_measures': 'Chemical: Systemic insecticides for pests.',
    },
    'cotton': {
        'title': 'Cotton Cultivation',
        'identity_context': 'Gossypium spp. The most important fiber crop in the world. Requires a long, frost-free period.',
        'soil_requirements': 'Black cotton soils, sandy loam, pH 6.0-8.0.',
        'climate_requirements': 'Warm climate, 200-900mm rainfall.',
        'water_irrigation_needs': 'Irrigate at flowering and boll formation stages.',
        'varieties': 'Bt cotton hybrids, H-6, F-846.',
        'seed_selection_sowing': 'Sow in April-May at 60x30cm spacing.',
        'nutrient_management': 'Apply NPK and micronutrients.',
        'season_of_cultivation': 'Kharif season (summer).',
        'land_preparation': 'Plough and harrow field.',
        'process_of_cultivation': 'Sowing → Irrigation → Fertilizer application → Pest control → Harvesting.',
        'organic_farming_practices': 'Use neem cake, compost, and biopesticides.',
        'harvesting_storage': 'Pick bolls when fully mature. Store in dry place.',
        'estimated_cost': 'Approx. ₹40,000-45,000/ha.',
        'locations_of_cultivation': 'Punjab, Maharashtra, Gujarat, Telangana.',
        'pests_affecting': 'Bollworm, aphids, whitefly.',
        'pest_control_measures': 'Bt cotton for bollworm. Imidacloprid for aphids. Neem oil for organic management.',
    },
    'sugarcane': {
        'title': 'Sugarcane Cultivation',
        'identity_context': 'Saccharum officinarum. Major source of sugar, a long-duration cash crop.',
        'soil_requirements': 'Deep, well-drained loamy soils with pH 6.5-7.5.',
        'climate_requirements': 'Hot, humid climate with 1500-2500mm rainfall.',
        'water_irrigation_needs': 'Very high water requirement (1500-2500 mm).',
        'varieties': 'Co 0238, Co 86032, CoJ 64.',
        'seed_selection_sowing': 'Plant setts in furrows at 75-90cm spacing.',
        'nutrient_management': 'Apply NPK and organic manure. Split application of nitrogen.',
        'season_of_cultivation': 'Planting in spring (Feb-March) or autumn (Sept-Oct).',
        'land_preparation': 'Deep ploughing and leveling.',
        'process_of_cultivation': 'Planting → Irrigation → Earthing up → Fertilizer application → Pest control → Harvesting.',
        'organic_farming_practices': 'Use green manure, compost, and biopesticides.',
        'harvesting_storage': 'Harvest when brix value is high. Transport to mills quickly.',
        'estimated_cost': 'Approx. ₹60,000-70,000/ha.',
        'locations_of_cultivation': 'UP, Maharashtra, Karnataka, Tamil Nadu.',
        'pests_affecting': 'Early shoot borer, top borer, termites.',
        'pest_control_measures': 'Chlorpyriphos for borers. Trichogramma for biological control.',
    },
    'tobacco': {
        'title': 'Tobacco Cultivation',
        'identity_context': 'Nicotiana spp. Commercial crop, leaves used for smoking, chewing, and as a natural pesticide source.',
        'soil_requirements': 'Well-drained sandy loams to heavy loams, depending on the type of tobacco. Needs good aeration.',
        'climate_requirements': 'Requires a warm, frost-free period (20°C to 30°C).',
        'water_irrigation_needs': 'Moderate water requirement (400-500 mm).',
        'varieties': 'Nicotiana tabacum and Nicotiana rustica.',
        'seed_selection_sowing': 'Transplanting of seedlings is common. Sowing Time: Aug-Sep (Nursery).',
        'nutrient_management': 'High Potassium needs for quality. Low N is often preferred for quality leaf production.',
        'season_of_cultivation': 'Rabi season (Transplanting in Oct-Nov).',
        'land_preparation': 'Fine, loose seedbed for good transplanting.',
        'process_of_cultivation': 'Nursery raising → Transplanting → Topping (removing floral buds) → Curing → Grading.',
        'organic_farming_practices': 'FYM, Green manuring. Crop rotation is essential.',
        'harvesting_storage': 'Harvested by primings (picking individual leaves) or entire plant cutting. Curing is a key process.',
        'estimated_cost': 'Approx. ₹45,000 to ₹60,000 per hectare.',
        'locations_of_cultivation': 'Andhra Pradesh, Gujarat, Karnataka.',
        'pests_affecting': 'Aphids, Leaf Curl Virus, Frog-eye spot.',
        'pest_control_measures': 'Chemical: Acephate (for aphids). Organic: Neem oil, field sanitation.',
    },
    'potato': {
        'title': 'Potato Cultivation',
        'identity_context': 'Solanum tuberosum. World\'s fourth-largest food crop, a tuber vegetable.',
        'soil_requirements': 'Sandy loam soils, pH 5.5-6.5.',
        'climate_requirements': 'Cool climate, frost-free period.',
        'water_irrigation_needs': 'Irrigate at tuber initiation and bulking.',
        'varieties': 'Kufri Jyoti, Kufri Bahar, Kufri Sindhuri.',
        'seed_selection_sowing': 'Plant tubers in October-November at 60x20cm spacing.',
        'nutrient_management': 'Apply NPK and organic manure.',
        'season_of_cultivation': 'Rabi season.',
        'land_preparation': 'Plough and ridge field.',
        'process_of_cultivation': 'Planting → Irrigation → Fertilizer application → Pest control → Harvesting.',
        'organic_farming_practices': 'Use compost and crop rotation.',
        'harvesting_storage': 'Harvest when vines dry. Store in cool, dark place.',
        'estimated_cost': 'Approx. ₹60,000-70,000/ha.',
        'locations_of_cultivation': 'Punjab, UP, West Bengal, Karnataka.',
        'pests_affecting': 'Late blight, aphids.',
        'pest_control_measures': 'Mancozeb for blight. Imidacloprid for aphids.',
    },
    'tomato': {
        'title': 'Tomato Cultivation',
        'identity_context': 'Tomato is a vegetable crop, widely grown for fresh and processed use.',
        'soil_requirements': 'Well-drained loamy soils, pH 6.0-7.0.',
        'climate_requirements': 'Warm climate, 20-30°C.',
        'water_irrigation_needs': 'Irrigate at flowering and fruiting stages.',
        'varieties': 'Pusa Ruby, Arka Vikas, Punjab Chhuhara.',
        'seed_selection_sowing': 'Transplant seedlings at 45x60cm spacing.',
        'nutrient_management': 'Apply NPK and organic manure.',
        'season_of_cultivation': 'Kharif and rabi seasons.',
        'land_preparation': 'Plough and level field.',
        'process_of_cultivation': 'Nursery raising → Transplanting → Irrigation → Fertilizer application → Pest control → Harvesting.',
        'organic_farming_practices': 'Use compost, neem cake, and biopesticides.',
        'harvesting_storage': 'Harvest when fruits are red. Store in cool place.',
        'estimated_cost': 'Approx. ₹50,000-60,000/ha.',
        'locations_of_cultivation': 'Punjab, Karnataka, Maharashtra, Andhra Pradesh.',
        'pests_affecting': 'Fruit borer, leaf curl virus.',
        'pest_control_measures': 'Spinosad for fruit borer. Neem oil for organic management.',
    },
    'onion': {
        'title': 'Onion Cultivation',
        'identity_context': 'Onion is a bulb crop, important for culinary use.',
        'soil_requirements': 'Sandy loam soils, pH 6.0-7.0.',
        'climate_requirements': 'Cool to moderate climate.',
        'water_irrigation_needs': 'Irrigate at bulb formation.',
        'varieties': 'Pusa Red, Agrifound Light Red, N-53.',
        'seed_selection_sowing': 'Transplant seedlings at 15x10cm spacing.',
        'nutrient_management': 'Apply NPK and organic manure.',
        'season_of_cultivation': 'Rabi and kharif seasons.',
        'land_preparation': 'Plough and level field.',
        'process_of_cultivation': 'Nursery raising → Transplanting → Irrigation → Fertilizer application → Pest control → Harvesting.',
        'organic_farming_practices': 'Use compost and neem cake.',
        'harvesting_storage': 'Harvest when necks dry. Store in ventilated place.',
        'estimated_cost': 'Approx. ₹40,000-50,000/ha.',
        'locations_of_cultivation': 'Maharashtra, Karnataka, Punjab, Gujarat.',
        'pests_affecting': 'Thrips, onion fly.',
        'pest_control_measures': 'Imidacloprid for thrips. Neem oil for organic management.',
    },
    'chickpea': {
        'title': 'Chickpea (Gram) Cultivation',
        'identity_context': 'Chickpea is a pulse crop, important for protein.',
        'soil_requirements': 'Sandy loam to clay loam soils, pH 6.0-7.5.',
        'climate_requirements': 'Cool, dry climate.',
        'water_irrigation_needs': 'Irrigate at pod formation if needed.',
        'varieties': 'Pusa 256, JG 11, ICCV 10.',
        'seed_selection_sowing': 'Sow in October-November at 60kg/ha seed rate.',
        'nutrient_management': 'Apply NPK and organic manure.',
        'season_of_cultivation': 'Rabi season.',
        'land_preparation': 'Plough and level field.',
        'process_of_cultivation': 'Sowing → Irrigation → Fertilizer application → Pest control → Harvesting.',
        'organic_farming_practices': 'Use compost and crop rotation.',
        'harvesting_storage': 'Harvest when pods dry. Store in dry place.',
        'estimated_cost': 'Approx. ₹18,000-22,000/ha.',
        'locations_of_cultivation': 'MP, Maharashtra, Rajasthan, UP.',
        'pests_affecting': 'Pod borer, wilt.',
        'pest_control_measures': 'Spinosad for pod borer. Trichoderma for wilt.',
    },
    'soybean': {
        'title': 'Soybean Cultivation',
        'identity_context': 'Soybean is an oilseed and pulse crop, rich in protein.',
        'soil_requirements': 'Well-drained loamy soils, pH 6.0-7.5.',
        'climate_requirements': 'Warm, humid climate.',
        'water_irrigation_needs': 'Irrigate at flowering and pod filling.',
        'varieties': 'JS 335, MAUS 71, NRC 37.',
        'seed_selection_sowing': 'Sow in June-July at 45x5cm spacing.',
        'nutrient_management': 'Apply NPK and organic manure.',
        'season_of_cultivation': 'Kharif season.',
        'land_preparation': 'Plough and level field.',
        'process_of_cultivation': 'Sowing → Irrigation → Fertilizer application → Pest control → Harvesting.',
        'organic_farming_practices': 'Use compost and crop rotation.',
        'harvesting_storage': 'Harvest when pods dry. Store in dry place.',
        'estimated_cost': 'Approx. ₹25,000-30,000/ha.',
        'locations_of_cultivation': 'MP, Maharashtra, Rajasthan.',
        'pests_affecting': 'Stem fly, pod borer.',
        'pest_control_measures': 'Imidacloprid for stem fly. Neem oil for organic management.',
    },
    'groundnut': {
        'title': 'Groundnut Cultivation',
        'identity_context': 'Groundnut is an oilseed crop, grown for edible oil.',
        'soil_requirements': 'Sandy loam soils, pH 6.0-7.5.',
        'climate_requirements': 'Warm, dry climate.',
        'water_irrigation_needs': 'Irrigate at flowering and pod formation.',
        'varieties': 'TG 37A, JL 24, GG 20.',
        'seed_selection_sowing': 'Sow in June-July at 30x10cm spacing.',
        'nutrient_management': 'Apply NPK and gypsum.',
        'season_of_cultivation': 'Kharif and summer seasons.',
        'land_preparation': 'Plough and level field.',
        'process_of_cultivation': 'Sowing → Irrigation → Fertilizer application → Pest control → Harvesting.',
        'organic_farming_practices': 'Use compost and crop rotation.',
        'harvesting_storage': 'Harvest when leaves yellow. Dry pods before storage.',
        'estimated_cost': 'Approx. ₹30,000-35,000/ha.',
        'locations_of_cultivation': 'Gujarat, Andhra Pradesh, Tamil Nadu.',
        'pests_affecting': 'Leaf miner, root rot.',
        'pest_control_measures': 'Imidacloprid for leaf miner. Trichoderma for root rot.',
    },
    'sorghum': {
        'title': 'Sorghum (Jowar) Cultivation',
        'identity_context': 'Sorghum bicolor. Drought-tolerant millet, used for food, feed, and ethanol production.',
        'soil_requirements': 'Wide adaptability, thrives in heavy and light soils, but dislikes very sandy or very heavy clay.',
        'climate_requirements': 'Warm season crop, highly heat and drought tolerant. Ideal temperature: 26°C to 30°C.',
        'water_irrigation_needs': 'Very drought tolerant. Requires 450-550 mm water. Critical stage: flowering.',
        'varieties': 'CSH series (Hybrids).',
        'seed_selection_sowing': 'Seed Rate: 8-10 kg/ha. Sowing Time: Kharif (June/July) and Rabi (September/October).',
        'nutrient_management': 'NPK 80:40:40 kg/ha.',
        'season_of_cultivation': 'Kharif and Rabi seasons.',
        'land_preparation': '2-3 ploughings followed by harrowing and leveling.',
        'process_of_cultivation': 'Sowing → Thinnning → Earthing up → Irrigation → Harvesting.',
        'organic_farming_practices': 'Green manures, Azotobacter treatment for seeds.',
        'harvesting_storage': 'Harvesting: when grains are hard. Storage: dry and moisture-free.',
        'estimated_cost': 'Approx. ₹15,000 to ₹20,000 per hectare.',
        'locations_of_cultivation': 'Maharashtra, Karnataka, Andhra Pradesh, Madhya Pradesh.',
        'pests_affecting': 'Shoot fly, Stem borer, Grain smut, Rust.',
        'pest_control_measures': 'Chemical: Seed treatment with Thiamethoxam.',
    },
    'bajra': {
        'title': 'Bajra (Pearl Millet) Cultivation',
        'identity_context': 'Pennisetum glaucum. The most widely grown type of millet, excellent drought tolerance, high nutritional value.',
        'soil_requirements': 'Best in sandy loam soils but thrives in low-fertility soils. Tolerant to low pH.',
        'climate_requirements': 'Requires hot, dry climate. Highly sensitive to cold and frost. Ideal temperature: 25°C to 35°C.',
        'water_irrigation_needs': 'Highly drought-tolerant, minimum water requirement (250-300 mm).',
        'varieties': 'Hybrid varieties for higher yields.',
        'seed_selection_sowing': 'Sow in July/August at 4-5 kg/ha seed rate.',
        'nutrient_management': 'NPK 80:40:40 kg/ha.',
        'season_of_cultivation': 'Kharif (Monsoon) season crop.',
        'land_preparation': '2-3 shallow cultivations and leveling.',
        'process_of_cultivation': 'Sowing → Thinning → Weeding → Harvesting.',
        'organic_farming_practices': 'Use compost and crop rotation.',
        'harvesting_storage': 'Harvest when grains are hard and dry.',
        'estimated_cost': 'Approx. ₹12,000 to ₹15,000 per hectare.',
        'locations_of_cultivation': 'Rajasthan, Gujarat, Uttar Pradesh, Maharashtra.',
        'pests_affecting': 'Downy mildew, Ergot, Stem borer.',
        'pest_control_measures': 'Chemical: Seed treatment with Metalaxyl.',
    },
    'kinnow': {
        'title': 'Kinnow (Citrus) Cultivation',
        'identity_context': 'Citrus nobilis x Citrus deliciosa. A hybrid citrus fruit, highly popular in Northern India.',
        'soil_requirements': 'Deep, well-drained loamy soils. Sensitive to high soil pH and salinity.',
        'climate_requirements': 'Sub-tropical crop, requires hot summers and cool winters. Sensitive to frost.',
        'water_irrigation_needs': 'Requires drip irrigation. Avoid water on tree trunk.',
        'varieties': 'Kinnow is the most common commercial variety.',
        'seed_selection_sowing': 'Propagation is done through budding on suitable rootstock.',
        'nutrient_management': 'Needs Zinc and Manganese. Application of FYM is essential.',
        'season_of_cultivation': 'Grafted in spring/monsoon. Fruits mature in winter.',
        'land_preparation': 'Pits are dug and filled with mixture of soil and FYM.',
        'process_of_cultivation': 'Planting → Training and pruning → Fertilization → Irrigation → Fruit maturity → Harvesting.',
        'organic_farming_practices': 'Use of organic mulch, cow urine spray for pest deterrence.',
        'harvesting_storage': 'Harvest when fruits attain full color. Can be stored for a limited time in ambient temperature.',
        'estimated_cost': 'High establishment cost (initial years), low maintenance.',
        'locations_of_cultivation': 'Punjab, Haryana, Rajasthan.',
        'pests_affecting': 'Citrus Canker, Citrus Psylla, Leaf Miner.',
        'pest_control_measures': 'Chemical: Copper-based fungicides. Organic: Neem oil, biological control.',
    },
    'peach': {
        'title': 'Peach Cultivation (Temperate Fruit)',
        'identity_context': 'Prunus persica. Temperate fruit, requiring chilling hours for production.',
        'soil_requirements': 'Deep, well-drained, sandy loam soils.',
        'climate_requirements': 'Temperate regions with adequate chilling hours and dry summers.',
        'water_irrigation_needs': 'High water requirement during fruit development.',
        'varieties': 'Early, mid, and late season varieties.',
        'seed_selection_sowing': 'Grafted onto suitable rootstock.',
        'nutrient_management': 'Balanced NPK and organic manure.',
        'season_of_cultivation': 'Harvested in summer (May-August).',
        'land_preparation': 'Pits are dug and filled.',
        'process_of_cultivation': 'Planting → Pruning → Dormancy Management → Fertilization → Harvesting.',
        'organic_farming_practices': 'Mulching and organic sprays.',
        'harvesting_storage': 'Harvest when firm and colored. Store in cold storage.',
        'estimated_cost': 'High initial cost.',
        'locations_of_cultivation': 'Himachal Pradesh, Uttarakhand.',
        'pests_affecting': 'Peach leaf curl, fruit fly.',
        'pest_control_measures': 'Chemical: Fungicides during dormant season. Organic: Pheromone traps.',
    },
    'guava': {
        'title': 'Guava Cultivation (Vitamin C Rich Fruit)',
        'identity_context': 'Psidium guajava. Tropical fruit, adaptable and drought-resistant, known as the "Apple of the Poor."',
        'soil_requirements': 'Can grow on poor soils, but deep, friable soils are best. Tolerates wide pH range (4.5 to 8.2).',
        'climate_requirements': 'Tropical and subtropical climate. Fruits best in cool weather.',
        'water_irrigation_needs': 'Drought tolerant, but yields increase with proper irrigation.',
        'varieties': 'Allahabad Safeda, Lucknow 49.',
        'seed_selection_sowing': 'Propagated by budding or air layering. Planting distance 5-8m.',
        'nutrient_management': 'Requires high Phosphorus and Potassium for flowering and fruiting.',
        'season_of_cultivation': 'Can fruit throughout the year, but main seasons are rainy (Ambe Bahar) and winter (Mrig Bahar).',
        'land_preparation': 'Pits are dug and filled before planting.',
        'process_of_cultivation': 'Planting → Pruning/Training → Fertilization → Bahar treatment (to regulate fruiting).',
        'organic_farming_practices': 'Heavy mulching and FYM application.',
        'harvesting_storage': 'Harvesting: Fruits are ready 3-5 years after planting. Store at room temperature for short periods.',
        'estimated_cost': 'Low annual maintenance cost.',
        'locations_of_cultivation': 'Maharashtra, Bihar, Uttar Pradesh.',
        'pests_affecting': 'Fruit fly, Guava wilt, Scale insects.',
        'pest_control_measures': 'Chemical: Malathion (for fruit fly). Organic: Bagging of fruits to prevent insect attack.',
    },
    'mango': {'title': 'Mango (King of Fruits) Cultivation', 'identity_context': 'Mangifera indica. Tropical evergreen tree, native to South Asia.', 'soil_requirements': 'Deep, well-drained loamy soil.', 'climate_requirements': 'Hot, dry summers; no frost during flowering.', 'water_irrigation_needs': 'Moderate; critical at flowering and fruit setting.', 'varieties': 'Alphonso, Dasheri, Langra.', 'seed_selection_sowing': 'Grafting or budding.', 'nutrient_management': 'High NPK and micro-nutrients.', 'season_of_cultivation': 'Fruit setting in March-April, harvesting in May-July.', 'land_preparation': 'Planting pits filled with organic matter.', 'process_of_cultivation': 'Planting → Training → Manuring → Flowering → Fruit harvest.', 'organic_farming_practices': 'Heavy FYM application, use of trap crops.', 'harvesting_storage': 'Harvest when fully mature; needs careful handling.', 'estimated_cost': 'High initial cost.', 'locations_of_cultivation': 'Uttar Pradesh, Andhra Pradesh, Karnataka.', 'pests_affecting': 'Mango Hopper, Mealy Bug, Powdery Mildew.', 'pest_control_measures': 'Chemical: Carbaryl. Organic: Neem oil.'},
    'pomegranate': {'title': 'Pomegranate Cultivation', 'identity_context': 'Punica granatum. Hardy fruit crop, known for drought tolerance and high commercial value.', 'soil_requirements': 'Adapted to a wide range of soils, deep alluvial or medium black soils preferred.', 'climate_requirements': 'Semi-arid and mild winter climate. Requires hot, dry summers.', 'water_irrigation_needs': 'Drought tolerant, but yields best with drip irrigation (400-600 mm).', 'varieties': 'Bhagwa, Ganesh, Ruby.', 'seed_selection_sowing': 'Propagated by hard wood cuttings.', 'nutrient_management': 'Requires NPK and FYM, split application of nitrogen.', 'season_of_cultivation': 'Flowering/fruiting can be managed (Bahar treatment) for specific seasons.', 'land_preparation': 'Deep tillage and planting pits.', 'process_of_cultivation': 'Planting → Pruning → Bahar Treatment → Fertilization → Harvesting.', 'organic_farming_practices': 'Pest control using neem-based products and mulching.', 'harvesting_storage': 'Harvest when skin color changes and sounds metallic when tapped. Good shelf life.', 'estimated_cost': 'Moderate establishment cost.', 'locations_of_cultivation': 'Maharashtra, Gujarat, Rajasthan.', 'pests_affecting': 'Fruit borer, anar butterfly.', 'pest_control_measures': 'Chemical: Lambda-cyhalothrin. Organic: Bagging of fruits.'},
    'papaya': {'title': 'Papaya Cultivation', 'identity_context': 'Carica papaya. Fast-growing tropical fruit, high in Vitamin A and C.', 'soil_requirements': 'Well-drained sandy loam soil, sensitive to waterlogging.', 'climate_requirements': 'Warm, humid climate (21°C-33°C). Extremely sensitive to frost.', 'water_irrigation_needs': 'Frequent, light irrigation.', 'varieties': 'Pusa Dwarf, Coorg Honey Dew.', 'seed_selection_sowing': 'Sown directly or seedlings transplanted. Plant 1.5m apart.', 'nutrient_management': 'High NPK needs, especially K.', 'season_of_cultivation': 'Planted in all seasons except severe winter and heavy rains.', 'land_preparation': 'Ploughing and pit digging.', 'process_of_cultivation': 'Planting → Inter-cropping (early stages) → Fertilization → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers for better fruit quality.', 'harvesting_storage': 'Harvest when fruit shows yellow streaks. Store in cool place.', 'estimated_cost': 'Low initial cost, short gestation period.', 'locations_of_cultivation': 'Andhra Pradesh, Gujarat, Maharashtra.', 'pests_affecting': 'Root rot, papaya mosaic virus, aphids.', 'pest_control_measures': 'Chemical: Systemic insecticides for aphids. Organic: Roguing (removing) diseased plants.'},
    'cauliflower': {'title': 'Cauliflower Cultivation', 'identity_context': 'Brassica oleracea. Cool season vegetable, grown for its edible white curd.', 'soil_requirements': 'Similar to cabbage, fertile loamy soils.', 'climate_requirements': 'Cool season crop, sensitive to sudden temperature changes.', 'water_irrigation_needs': 'Requires consistent moisture during curd formation.', 'varieties': 'Pusa Katki, Early Synthetic.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High demand for Boron and Molybdenum.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Blanching (tying leaves over the curd) → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when curd is firm and white. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, whiptail.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'cabbage': {'title': 'Cabbage Cultivation', 'identity_context': 'Brassica oleracea. Leafy vegetable, important for vitamins and minerals.', 'soil_requirements': 'Fertile, well-drained loamy soil, pH 6.0-6.5.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires constant moisture, frequent light irrigation.', 'varieties': 'Pusa Mukta, Golden Acre.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High NPK needs, especially N.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Head formation → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when heads are firm. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, black rot.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'carrot': {'title': 'Carrot Cultivation', 'identity_context': 'Daucus carota. Root vegetable, rich in Vitamin A.', 'soil_requirements': 'Deep, loose, sandy loamy soils, stone-free.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires uniform moisture; avoid water stress during root growth.', 'varieties': 'Pusa Kesar, Nantes.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'High Potassium needs.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Deep ploughing to a depth of 30cm to allow straight root growth.', 'process_of_cultivation': 'Sowing → Thinning → Inter-culturing → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost, intercrop with onions.', 'harvesting_storage': 'Harvest when roots are fully developed. Store in cool, humid conditions.', 'estimated_cost': 'Low to moderate.', 'locations_of_cultivation': 'UP, Haryana, Punjab.', 'pests_affecting': 'Carrot weevil, leaf blight.', 'pest_control_measures': 'Chemical: Mancozeb. Organic: Crop rotation.'},
    'radish': {'title': 'Radish Cultivation', 'identity_context': 'Raphanus sativus. Fast-growing root vegetable.', 'soil_requirements': 'Loose, sandy loam soils.', 'climate_requirements': 'Cool season crop, very quick maturity.', 'water_irrigation_needs': 'Requires constant moisture for tender roots.', 'varieties': 'Pusa Chetki (Tropical), Japanese White.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'Responds well to organic manure and balanced NPK.', 'season_of_cultivation': 'All year round (depending on variety).', 'land_preparation': 'Deep, fine tillage.', 'process_of_cultivation': 'Sowing → Thinning → Irrigation → Harvesting (25-45 days).', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers.', 'harvesting_storage': 'Harvest when roots reach optimal size. Cannot be stored long.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, flea beetles.', 'pest_control_measures': 'Chemical: Malathion. Organic: Neem oil.'},
    'spinach': {'title': 'Spinach Cultivation', 'identity_context': 'Spinacia oleracea. Leafy vegetable, rich in iron.', 'soil_requirements': 'Wide range, deep fertile loams preferred.', 'climate_requirements': 'Cool season crop, sensitive to hot weather (causes bolting).', 'water_irrigation_needs': 'High moisture requirement, frequent light irrigation.', 'varieties': 'Pusa Jyoti, All Green.', 'seed_selection_sowing': 'Sown directly.', 'nutrient_management': 'High Nitrogen need for leaf growth.', 'season_of_cultivation': 'Rabi (winter).', 'land_preparation': 'Fine tilth, rich in organic matter.', 'process_of_cultivation': 'Sowing → Irrigation → Fertilization → Harvesting (multiple cuts).', 'organic_farming_practices': 'Heavy organic manure application.', 'harvesting_storage': 'Harvested by cutting leaves; consume fresh.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, leaf miners.', 'pest_control_measures': 'Organic: Neem oil, water spray.'},
    'brinjal': {'title': 'Brinjal (Eggplant) Cultivation', 'identity_context': 'Solanum melongena. Warm-season vegetable, widely consumed.', 'soil_requirements': 'Fertile, well-drained sandy loam to clay loam.', 'climate_requirements': 'Warm season crop, sensitive to frost.', 'water_irrigation_needs': 'Moderate to high, critical at flowering.', 'varieties': 'Pusa Purple Long, Pusa Kranti.', 'seed_selection_sowing': 'Transplanted at 6-8 weeks old.', 'nutrient_management': 'High NPK demand.', 'season_of_cultivation': 'Kharif and Rabi.', 'land_preparation': 'Fine, deep tilth.', 'process_of_cultivation': 'Nursery → Transplanting → Staking (optional) → Irrigation → Harvesting (multiple pickings).', 'organic_farming_practices': 'Use compost, crop rotation.', 'harvesting_storage': 'Harvest when fruits are glossy. Store in cool, dark place.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'Majorly grown in almost all states.', 'pests_affecting': 'Fruit and shoot borer, jassids, little leaf disease.', 'pest_control_measures': 'Chemical: Carbaryl. Organic: Release of parasitoids.'},
    'sorghum-hybrid': {'title': 'Sorghum Sudan Hybrid Cultivation', 'identity_context': 'Hybrid annual grass used exclusively for high-yield fodder/silage.', 'soil_requirements': 'Adapted to most soils, best in well-drained loam.', 'climate_requirements': 'Requires warm temperatures (25°C-30°C) and is drought tolerant.', 'water_irrigation_needs': 'Higher water need than grain sorghum; requires irrigation for multi-cuts.', 'varieties': 'Various multi-cut hybrids available.', 'seed_selection_sowing': 'Seed Rate: 25-30 kg/ha. Sowing Time: Spring or Monsoon.', 'nutrient_management': 'High nitrogen requirement due to frequent cutting.', 'season_of_cultivation': 'Grown in Kharif and Zaid seasons.', 'land_preparation': 'Fine seedbed.', 'process_of_cultivation': 'Sowing → First cut (45-60 days) → Fertilization → Subsequent cuts.', 'organic_farming_practices': 'Use slurry and bio-fertilizers after each cut.', 'harvesting_storage': 'Cut at boot stage. Used for hay, silage, or green chop.', 'estimated_cost': 'Moderate input cost.', 'locations_of_cultivation': 'Punjab, Haryana, Rajasthan.', 'pests_affecting': 'Stem borers, shoot fly.', 'pest_control_measures': 'Chemical: Carbaryl. Organic: Biological control.'},
    'berseem': {'title': 'Berseem (Clover) Cultivation', 'identity_context': 'Trifolium alexandrinum. Highly valuable winter fodder legume, known for nitrogen fixation and palatability.', 'soil_requirements': 'Medium to heavy loam soils. Sensitive to acidity.', 'climate_requirements': 'Cool season crop. Ideal temperature: 18°C to 25°C.', 'water_irrigation_needs': 'Requires frequent irrigation (5-7 days interval).', 'varieties': 'Mescavi, Wardan.', 'seed_selection_sowing': 'Seed Rate: 25-30 kg/ha. Sowing Time: October.', 'nutrient_management': 'High Phosphorus and Potassium.', 'season_of_cultivation': 'Rabi (Winter) season crop.', 'land_preparation': 'Finely prepared seedbed.', 'process_of_cultivation': 'Sowing → Inoculation → First cut (50-60 days) → Subsequent cuts (25-30 days).', 'organic_farming_practices': 'Excellent soil improver and nitrogen fixer.', 'harvesting_storage': 'Multiple cuts over 4-5 months. Used as green fodder.', 'estimated_cost': 'Low annual maintenance cost.', 'locations_of_cultivation': 'Punjab, Haryana, Uttar Pradesh.', 'pests_affecting': 'Aphids, Root rot.', 'pest_control_measures': 'Organic: Neem products, proper water management.'},
    'maize-silage': {'title': 'Maize (for Silage) Cultivation', 'identity_context': 'Field corn harvested when moisture content is ideal for animal feed preservation.', 'soil_requirements': 'Deep, fertile, well-drained loamy soils.', 'climate_requirements': 'Warm season crop, needs high temperatures.', 'water_irrigation_needs': 'High water requirement.', 'varieties': 'Specific tall hybrids for high biomass.', 'seed_selection_sowing': 'Seed Rate: 40-50 kg/ha. Sowing Time: Kharif (June-July).', 'nutrient_management': 'High NPK for high biomass production.', 'season_of_cultivation': 'Kharif and Zaid seasons.', 'land_preparation': 'Fine tilth.', 'process_of_cultivation': 'Sowing → Fertilization → Irrigation → Harvesting at dough stage.', 'organic_farming_practices': 'Use heavy FYM/compost.', 'harvesting_storage': 'Harvested whole plant, chopped, and stored in an airtight silo/pit for fermentation.', 'estimated_cost': 'Moderate input cost.', 'locations_of_cultivation': 'Punjab, Haryana, Maharashtra.', 'pests_affecting': 'Stem borers, armyworm.', 'pest_control_measures': 'IPM practices.'},
    'alfalfa': {'title': 'Alfalfa (Lucerne) Cultivation', 'identity_context': 'Medicago sativa. Perennial forage legume, known as "Queen of Forages" for high protein.', 'soil_requirements': 'Deep, well-drained loam to clay loam, slightly alkaline pH (6.5-7.5).', 'climate_requirements': 'Tolerates wide range, but sensitive to extreme heat and humidity.', 'water_irrigation_needs': 'Requires frequent irrigation, but less than berseem.', 'varieties': 'Anand-2, T9.', 'seed_selection_sowing': 'Seed Rate: 20-25 kg/ha. Sowing Time: October.', 'nutrient_management': 'High Phosphorus and Potassium.', 'season_of_cultivation': 'Perennial crop, but main growth in Rabi/winter.', 'land_preparation': 'Fine, firm seedbed.', 'process_of_cultivation': 'Sowing → First cut (70-80 days) → Subsequent cuts (25-30 days).', 'organic_farming_practices': 'Excellent soil improver and nitrogen fixer.', 'harvesting_storage': 'Multiple cuts per year. Used as green fodder, hay, or silage.', 'estimated_cost': 'Low annual maintenance cost.', 'locations_of_cultivation': 'Gujarat, Maharashtra, Rajasthan.', 'pests_affecting': 'Aphids, Leaf spot.', 'pest_control_measures': 'Chemical: Malathion. Organic: Biological control.'},
    'kinnow-silage': {'title': 'Kinnow (Citrus) Cultivation', 'identity_context': 'Citrus hybrid.', 'soil_requirements': 'Deep, well-drained loamy soils.', 'climate_requirements': 'Sub-tropical crop.', 'water_irrigation_needs': 'Requires drip irrigation.', 'varieties': 'Kinnow.', 'seed_selection_sowing': 'Budding.', 'nutrient_management': 'Needs Zinc and Manganese.', 'season_of_cultivation': 'Grafted in spring/monsoon.', 'land_preparation': 'Pits are dug and filled.', 'process_of_cultivation': 'Planting → Training → Fertilization → Irrigation → Harvesting.', 'organic_farming_practices': 'Organic mulch, cow urine spray.', 'harvesting_storage': 'Harvest when fruits attain full color.', 'estimated_cost': 'High initial cost.', 'locations_of_cultivation': 'Punjab, Haryana, Rajasthan.', 'pests_affecting': 'Citrus Canker, Citrus Psylla.', 'pest_control_measures': 'Chemical: Copper-based fungicides. Organic: Neem oil.'},
    'guava-silage': {'title': 'Guava Cultivation', 'identity_context': 'Psidium guajava. Tropical fruit.', 'soil_requirements': 'Tolerates wide pH range.', 'climate_requirements': 'Tropical and subtropical climate.', 'water_irrigation_needs': 'Drought tolerant.', 'varieties': 'Allahabad Safeda, Lucknow 49.', 'seed_selection_sowing': 'Budding or air layering.', 'nutrient_management': 'High Phosphorus and Potassium.', 'season_of_cultivation': 'Rainy and winter seasons.', 'land_preparation': 'Pits are dug and filled.', 'process_of_cultivation': 'Planting → Pruning → Fertilization → Irrigation → Harvesting.', 'organic_farming_practices': 'Heavy mulching and FYM application.', 'harvesting_storage': 'Fruits are ready 3-5 years after planting.', 'estimated_cost': 'Low annual maintenance cost.', 'locations_of_cultivation': 'Maharashtra, Bihar, Uttar Pradesh.', 'pests_affecting': 'Fruit fly, Guava wilt.', 'pest_control_measures': 'Chemical: Malathion. Organic: Bagging of fruits.'},
    'mango-silage': {'title': 'Mango (King of Fruits) Cultivation', 'identity_context': 'Mangifera indica. Tropical evergreen tree, native to South Asia.', 'soil_requirements': 'Deep, well-drained loamy soil.', 'climate_requirements': 'Hot, dry summers; no frost during flowering.', 'water_irrigation_needs': 'Moderate; critical at flowering and fruit setting.', 'varieties': 'Alphonso, Dasheri, Langra.', 'seed_selection_sowing': 'Grafting or budding.', 'nutrient_management': 'High NPK and micro-nutrients.', 'season_of_cultivation': 'Fruit setting in March-April, harvesting in May-July.', 'land_preparation': 'Planting pits filled with organic matter.', 'process_of_cultivation': 'Planting → Training → Manuring → Flowering → Fruit harvest.', 'organic_farming_practices': 'Heavy FYM application, use of trap crops.', 'harvesting_storage': 'Harvest when fully mature; needs careful handling.', 'estimated_cost': 'High initial cost.', 'locations_of_cultivation': 'Uttar Pradesh, Andhra Pradesh, Karnataka.', 'pests_affecting': 'Mango Hopper, Mealy Bug, Powdery Mildew.', 'pest_control_measures': 'Chemical: Carbaryl. Organic: Neem oil.'},
    'pomegranate-silage': {'title': 'Pomegranate Cultivation', 'identity_context': 'Punica granatum. Hardy fruit crop, known for drought tolerance and high commercial value.', 'soil_requirements': 'Adapted to a wide range of soils, deep alluvial or medium black soils preferred.', 'climate_requirements': 'Semi-arid and mild winter climate. Requires hot, dry summers.', 'water_irrigation_needs': 'Drought tolerant, but yields best with drip irrigation (400-600 mm).', 'varieties': 'Bhagwa, Ganesh, Ruby.', 'seed_selection_sowing': 'Propagated by hard wood cuttings.', 'nutrient_management': 'Requires NPK and FYM, split application of nitrogen.', 'season_of_cultivation': 'Flowering/fruiting can be managed (Bahar treatment) for specific seasons.', 'land_preparation': 'Deep tillage and planting pits.', 'process_of_cultivation': 'Planting → Pruning → Bahar Treatment → Fertilization → Harvesting.', 'organic_farming_practices': 'Pest control using neem-based products and mulching.', 'harvesting_storage': 'Harvest when skin color changes and sounds metallic when tapped. Good shelf life.', 'estimated_cost': 'Moderate establishment cost.', 'locations_of_cultivation': 'Maharashtra, Gujarat, Rajasthan.', 'pests_affecting': 'Fruit borer, anar butterfly.', 'pest_control_measures': 'Chemical: Lambda-cyhalothrin. Organic: Bagging of fruits.'},
    'papaya-silage': {'title': 'Papaya Cultivation', 'identity_context': 'Carica papaya. Fast-growing tropical fruit, high in Vitamin A and C.', 'soil_requirements': 'Well-drained sandy loam soil, sensitive to waterlogging.', 'climate_requirements': 'Warm, humid climate (21°C-33°C). Extremely sensitive to frost.', 'water_irrigation_needs': 'Frequent, light irrigation.', 'varieties': 'Pusa Dwarf, Coorg Honey Dew.', 'seed_selection_sowing': 'Sown directly or seedlings transplanted. Plant 1.5m apart.', 'nutrient_management': 'High NPK needs, especially K.', 'season_of_cultivation': 'Planted in all seasons except severe winter and heavy rains.', 'land_preparation': 'Ploughing and pit digging.', 'process_of_cultivation': 'Planting → Inter-cropping (early stages) → Fertilization → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers for better fruit quality.', 'harvesting_storage': 'Harvest when fruit shows yellow streaks. Store in cool place.', 'estimated_cost': 'Low initial cost, short gestation period.', 'locations_of_cultivation': 'Andhra Pradesh, Gujarat, Maharashtra.', 'pests_affecting': 'Root rot, papaya mosaic virus, aphids.', 'pest_control_measures': 'Chemical: Systemic insecticides for aphids. Organic: Roguing (removing) diseased plants.'},
    'cauliflower-silage': {'title': 'Cauliflower Cultivation', 'identity_context': 'Brassica oleracea. Cool season vegetable, grown for its edible white curd.', 'soil_requirements': 'Similar to cabbage, fertile loamy soils.', 'climate_requirements': 'Cool season crop, sensitive to sudden temperature changes.', 'water_irrigation_needs': 'Requires consistent moisture during curd formation.', 'varieties': 'Pusa Katki, Early Synthetic.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High demand for Boron and Molybdenum.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Blanching (tying leaves over the curd) → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when curd is firm and white. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, whiptail.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'cabbage-silage': {'title': 'Cabbage Cultivation', 'identity_context': 'Brassica oleracea. Leafy vegetable, important for vitamins and minerals.', 'soil_requirements': 'Fertile, well-drained loamy soil, pH 6.0-6.5.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires constant moisture, frequent light irrigation.', 'varieties': 'Pusa Mukta, Golden Acre.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High NPK needs, especially N.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Head formation → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when heads are firm. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, black rot.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'carrot-silage': {'title': 'Carrot Cultivation', 'identity_context': 'Daucus carota. Root vegetable, rich in Vitamin A.', 'soil_requirements': 'Deep, loose, sandy loamy soils, stone-free.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires uniform moisture; avoid water stress during root growth.', 'varieties': 'Pusa Kesar, Nantes.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'High Potassium needs.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Deep ploughing to a depth of 30cm to allow straight root growth.', 'process_of_cultivation': 'Sowing → Thinning → Inter-culturing → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost, intercrop with onions.', 'harvesting_storage': 'Harvest when roots are fully developed. Store in cool, humid conditions.', 'estimated_cost': 'Low to moderate.', 'locations_of_cultivation': 'UP, Haryana, Punjab.', 'pests_affecting': 'Carrot weevil, leaf blight.', 'pest_control_measures': 'Chemical: Mancozeb. Organic: Crop rotation.'},
    'radish-silage': {'title': 'Radish Cultivation', 'identity_context': 'Raphanus sativus. Fast-growing root vegetable.', 'soil_requirements': 'Loose, sandy loam soils.', 'climate_requirements': 'Cool season crop, very quick maturity.', 'water_irrigation_needs': 'Requires constant moisture for tender roots.', 'varieties': 'Pusa Chetki (Tropical), Japanese White.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'Responds well to organic manure and balanced NPK.', 'season_of_cultivation': 'All year round (depending on variety).', 'land_preparation': 'Deep, fine tillage.', 'process_of_cultivation': 'Sowing → Thinning → Irrigation → Harvesting (25-45 days).', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers.', 'harvesting_storage': 'Harvest when roots reach optimal size. Cannot be stored long.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, flea beetles.', 'pest_control_measures': 'Chemical: Malathion. Organic: Neem oil.'},
    'spinach-silage': {'title': 'Spinach Cultivation', 'identity_context': 'Spinacia oleracea. Leafy vegetable, rich in iron.', 'soil_requirements': 'Wide range, deep fertile loams preferred.', 'climate_requirements': 'Cool season crop, sensitive to hot weather (causes bolting).', 'water_irrigation_needs': 'High moisture requirement, frequent light irrigation.', 'varieties': 'Pusa Jyoti, All Green.', 'seed_selection_sowing': 'Sown directly.', 'nutrient_management': 'High Nitrogen need for leaf growth.', 'season_of_cultivation': 'Rabi (winter).', 'land_preparation': 'Fine tilth, rich in organic matter.', 'process_of_cultivation': 'Sowing → Irrigation → Fertilization → Harvesting (multiple cuts).', 'organic_farming_practices': 'Heavy organic manure application.', 'harvesting_storage': 'Harvested by cutting leaves; consume fresh.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, leaf miners.', 'pest_control_measures': 'Organic: Neem oil, water spray.'},
    'brinjal-silage': {'title': 'Brinjal (Eggplant) Cultivation', 'identity_context': 'Solanum melongena. Warm-season vegetable, widely consumed.', 'soil_requirements': 'Fertile, well-drained sandy loam to clay loam.', 'climate_requirements': 'Warm season crop, sensitive to frost.', 'water_irrigation_needs': 'Moderate to high, critical at flowering.', 'varieties': 'Pusa Purple Long, Pusa Kranti.', 'seed_selection_sowing': 'Transplanted at 6-8 weeks old.', 'nutrient_management': 'High NPK demand.', 'season_of_cultivation': 'Kharif and Rabi.', 'land_preparation': 'Fine, deep tilth.', 'process_of_cultivation': 'Nursery → Transplanting → Staking (optional) → Irrigation → Harvesting (multiple pickings).', 'organic_farming_practices': 'Use compost, crop rotation.', 'harvesting_storage': 'Harvest when fruits are glossy. Store in cool, dark place.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'Majorly grown in almost all states.', 'pests_affecting': 'Fruit and shoot borer, jassids, little leaf disease.', 'pest_control_measures': 'Chemical: Carbaryl. Organic: Release of parasitoids.'},
    'peach-silage': {'title': 'Peach Cultivation', 'identity_context': 'Prunus persica. Temperate fruit, requiring chilling hours for production.', 'soil_requirements': 'Deep, well-drained, sandy loam soils.', 'climate_requirements': 'Temperate regions with adequate chilling hours and dry summers.', 'water_irrigation_needs': 'High water requirement during fruit development.', 'varieties': 'Early, mid, and late season varieties.', 'seed_selection_sowing': 'Grafted onto suitable rootstock.', 'nutrient_management': 'Balanced NPK and organic manure.', 'season_of_cultivation': 'Harvested in summer (May-August).', 'land_preparation': 'Pits are dug and filled.', 'process_of_cultivation': 'Planting → Pruning → Dormancy Management → Fertilization → Harvesting.', 'organic_farming_practices': 'Mulching and organic sprays.', 'harvesting_storage': 'Harvest when firm and colored. Store in cold storage.', 'estimated_cost': 'High initial cost.', 'locations_of_cultivation': 'Himachal Pradesh, Uttarakhand.', 'pests_affecting': 'Peach leaf curl, fruit fly.', 'pest_control_measures': 'Chemical: Fungicides during dormant season. Organic: Pheromone traps.'},
    'pomegranate-silage': {'title': 'Pomegranate Cultivation', 'identity_context': 'Punica granatum. Hardy fruit crop, known for drought tolerance and high commercial value.', 'soil_requirements': 'Adapted to a wide range of soils, deep alluvial or medium black soils preferred.', 'climate_requirements': 'Semi-arid and mild winter climate. Requires hot, dry summers.', 'water_irrigation_needs': 'Drought tolerant, but yields best with drip irrigation (400-600 mm).', 'varieties': 'Bhagwa, Ganesh, Ruby.', 'seed_selection_sowing': 'Propagated by hard wood cuttings.', 'nutrient_management': 'Requires NPK and FYM, split application of nitrogen.', 'season_of_cultivation': 'Flowering/fruiting can be managed (Bahar treatment) for specific seasons.', 'land_preparation': 'Deep tillage and planting pits.', 'process_of_cultivation': 'Planting → Pruning → Bahar Treatment → Fertilization → Harvesting.', 'organic_farming_practices': 'Pest control using neem-based products and mulching.', 'harvesting_storage': 'Harvest when skin color changes and sounds metallic when tapped. Good shelf life.', 'estimated_cost': 'Moderate establishment cost.', 'locations_of_cultivation': 'Maharashtra, Gujarat, Rajasthan.', 'pests_affecting': 'Fruit borer, anar butterfly.', 'pest_control_measures': 'Chemical: Lambda-cyhalothrin. Organic: Bagging of fruits.'},
    'papaya-silage': {'title': 'Papaya Cultivation', 'identity_context': 'Carica papaya. Fast-growing tropical fruit, high in Vitamin A and C.', 'soil_requirements': 'Well-drained sandy loam soil, sensitive to waterlogging.', 'climate_requirements': 'Warm, humid climate (21°C-33°C). Extremely sensitive to frost.', 'water_irrigation_needs': 'Frequent, light irrigation.', 'varieties': 'Pusa Dwarf, Coorg Honey Dew.', 'seed_selection_sowing': 'Sown directly or seedlings transplanted. Plant 1.5m apart.', 'nutrient_management': 'High NPK needs, especially K.', 'season_of_cultivation': 'Planted in all seasons except severe winter and heavy rains.', 'land_preparation': 'Ploughing and pit digging.', 'process_of_cultivation': 'Planting → Inter-cropping (early stages) → Fertilization → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers for better fruit quality.', 'harvesting_storage': 'Harvest when fruit shows yellow streaks. Store in cool place.', 'estimated_cost': 'Low initial cost, short gestation period.', 'locations_of_cultivation': 'Andhra Pradesh, Gujarat, Maharashtra.', 'pests_affecting': 'Root rot, papaya mosaic virus, aphids.', 'pest_control_measures': 'Chemical: Systemic insecticides for aphids. Organic: Roguing (removing) diseased plants.'},
    'cauliflower-silage': {'title': 'Cauliflower Cultivation', 'identity_context': 'Brassica oleracea. Cool season vegetable, grown for its edible white curd.', 'soil_requirements': 'Similar to cabbage, fertile loamy soils.', 'climate_requirements': 'Cool season crop, sensitive to sudden temperature changes.', 'water_irrigation_needs': 'Requires consistent moisture during curd formation.', 'varieties': 'Pusa Katki, Early Synthetic.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High demand for Boron and Molybdenum.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Blanching (tying leaves over the curd) → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when curd is firm and white. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, whiptail.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'cabbage-silage': {'title': 'Cabbage Cultivation', 'identity_context': 'Brassica oleracea. Leafy vegetable, important for vitamins and minerals.', 'soil_requirements': 'Fertile, well-drained loamy soil, pH 6.0-6.5.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires constant moisture, frequent light irrigation.', 'varieties': 'Pusa Mukta, Golden Acre.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High NPK needs, especially N.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Head formation → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when heads are firm. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, black rot.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'carrot-silage': {'title': 'Carrot Cultivation', 'identity_context': 'Daucus carota. Root vegetable, rich in Vitamin A.', 'soil_requirements': 'Deep, loose, sandy loamy soils, stone-free.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires uniform moisture; avoid water stress during root growth.', 'varieties': 'Pusa Kesar, Nantes.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'High Potassium needs.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Deep ploughing to a depth of 30cm to allow straight root growth.', 'process_of_cultivation': 'Sowing → Thinning → Inter-culturing → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost, intercrop with onions.', 'harvesting_storage': 'Harvest when roots are fully developed. Store in cool, humid conditions.', 'estimated_cost': 'Low to moderate.', 'locations_of_cultivation': 'UP, Haryana, Punjab.', 'pests_affecting': 'Carrot weevil, leaf blight.', 'pest_control_measures': 'Chemical: Mancozeb. Organic: Crop rotation.'},
    'radish-silage': {'title': 'Radish Cultivation', 'identity_context': 'Raphanus sativus. Fast-growing root vegetable.', 'soil_requirements': 'Loose, sandy loam soils.', 'climate_requirements': 'Cool season crop, very quick maturity.', 'water_irrigation_needs': 'Requires constant moisture for tender roots.', 'varieties': 'Pusa Chetki (Tropical), Japanese White.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'Responds well to organic manure and balanced NPK.', 'season_of_cultivation': 'All year round (depending on variety).', 'land_preparation': 'Deep, fine tillage.', 'process_of_cultivation': 'Sowing → Thinning → Irrigation → Harvesting (25-45 days).', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers.', 'harvesting_storage': 'Harvest when roots reach optimal size. Cannot be stored long.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, flea beetles.', 'pest_control_measures': 'Chemical: Malathion. Organic: Neem oil.'},
    'spinach-silage': {'title': 'Spinach Cultivation', 'identity_context': 'Spinacia oleracea. Leafy vegetable, rich in iron.', 'soil_requirements': 'Wide range, deep fertile loams preferred.', 'climate_requirements': 'Cool season crop, sensitive to hot weather (causes bolting).', 'water_irrigation_needs': 'High moisture requirement, frequent light irrigation.', 'varieties': 'Pusa Jyoti, All Green.', 'seed_selection_sowing': 'Sown directly.', 'nutrient_management': 'High Nitrogen need for leaf growth.', 'season_of_cultivation': 'Rabi (winter).', 'land_preparation': 'Fine tilth, rich in organic matter.', 'process_of_cultivation': 'Sowing → Irrigation → Fertilization → Harvesting (multiple cuts).', 'organic_farming_practices': 'Heavy organic manure application.', 'harvesting_storage': 'Harvested by cutting leaves; consume fresh.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, leaf miners.', 'pest_control_measures': 'Organic: Neem oil, water spray.'},
    'brinjal-silage': {'title': 'Brinjal (Eggplant) Cultivation', 'identity_context': 'Solanum melongena. Warm-season vegetable, widely consumed.', 'soil_requirements': 'Fertile, well-drained sandy loam to clay loam.', 'climate_requirements': 'Warm season crop, sensitive to frost.', 'water_irrigation_needs': 'Moderate to high, critical at flowering.', 'varieties': 'Pusa Purple Long, Pusa Kranti.', 'seed_selection_sowing': 'Transplanted at 6-8 weeks old.', 'nutrient_management': 'High NPK demand.', 'season_of_cultivation': 'Kharif and Rabi.', 'land_preparation': 'Fine, deep tilth.', 'process_of_cultivation': 'Nursery → Transplanting → Staking (optional) → Irrigation → Harvesting (multiple pickings).', 'organic_farming_practices': 'Use compost, crop rotation.', 'harvesting_storage': 'Harvest when fruits are glossy. Store in cool, dark place.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'Majorly grown in almost all states.', 'pests_affecting': 'Fruit and shoot borer, jassids, little leaf disease.', 'pest_control_measures': 'Chemical: Carbaryl. Organic: Release of parasitoids.'},
    'peach-silage': {'title': 'Peach Cultivation', 'identity_context': 'Prunus persica. Temperate fruit, requiring chilling hours for production.', 'soil_requirements': 'Deep, well-drained, sandy loam soils.', 'climate_requirements': 'Temperate regions with adequate chilling hours and dry summers.', 'water_irrigation_needs': 'High water requirement during fruit development.', 'varieties': 'Early, mid, and late season varieties.', 'seed_selection_sowing': 'Grafted onto suitable rootstock.', 'nutrient_management': 'Balanced NPK and organic manure.', 'season_of_cultivation': 'Harvested in summer (May-August).', 'land_preparation': 'Pits are dug and filled.', 'process_of_cultivation': 'Planting → Pruning → Dormancy Management → Fertilization → Harvesting.', 'organic_farming_practices': 'Mulching and organic sprays.', 'harvesting_storage': 'Harvest when firm and colored. Store in cold storage.', 'estimated_cost': 'High initial cost.', 'locations_of_cultivation': 'Himachal Pradesh, Uttarakhand.', 'pests_affecting': 'Peach leaf curl, fruit fly.', 'pest_control_measures': 'Chemical: Fungicides during dormant season. Organic: Pheromone traps.'},
    'pomegranate-silage': {'title': 'Pomegranate Cultivation', 'identity_context': 'Punica granatum. Hardy fruit crop, known for drought tolerance and high commercial value.', 'soil_requirements': 'Adapted to a wide range of soils, deep alluvial or medium black soils preferred.', 'climate_requirements': 'Semi-arid and mild winter climate. Requires hot, dry summers.', 'water_irrigation_needs': 'Drought tolerant, but yields best with drip irrigation (400-600 mm).', 'varieties': 'Bhagwa, Ganesh, Ruby.', 'seed_selection_sowing': 'Propagated by hard wood cuttings.', 'nutrient_management': 'Requires NPK and FYM, split application of nitrogen.', 'season_of_cultivation': 'Flowering/fruiting can be managed (Bahar treatment) for specific seasons.', 'land_preparation': 'Deep tillage and planting pits.', 'process_of_cultivation': 'Planting → Pruning → Bahar Treatment → Fertilization → Harvesting.', 'organic_farming_practices': 'Pest control using neem-based products and mulching.', 'harvesting_storage': 'Harvest when skin color changes and sounds metallic when tapped. Good shelf life.', 'estimated_cost': 'Moderate establishment cost.', 'locations_of_cultivation': 'Maharashtra, Gujarat, Rajasthan.', 'pests_affecting': 'Fruit borer, anar butterfly.', 'pest_control_measures': 'Chemical: Lambda-cyhalothrin. Organic: Bagging of fruits.'},
    'papaya-silage': {'title': 'Papaya Cultivation', 'identity_context': 'Carica papaya. Fast-growing tropical fruit, high in Vitamin A and C.', 'soil_requirements': 'Well-drained sandy loam soil, sensitive to waterlogging.', 'climate_requirements': 'Warm, humid climate (21°C-33°C). Extremely sensitive to frost.', 'water_irrigation_needs': 'Frequent, light irrigation.', 'varieties': 'Pusa Dwarf, Coorg Honey Dew.', 'seed_selection_sowing': 'Sown directly or seedlings transplanted. Plant 1.5m apart.', 'nutrient_management': 'High NPK needs, especially K.', 'season_of_cultivation': 'Planted in all seasons except severe winter and heavy rains.', 'land_preparation': 'Ploughing and pit digging.', 'process_of_cultivation': 'Planting → Inter-cropping (early stages) → Fertilization → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers for better fruit quality.', 'harvesting_storage': 'Harvest when fruit shows yellow streaks. Store in cool place.', 'estimated_cost': 'Low initial cost, short gestation period.', 'locations_of_cultivation': 'Andhra Pradesh, Gujarat, Maharashtra.', 'pests_affecting': 'Root rot, papaya mosaic virus, aphids.', 'pest_control_measures': 'Chemical: Systemic insecticides for aphids. Organic: Roguing (removing) diseased plants.'},
    'cauliflower-silage': {'title': 'Cauliflower Cultivation', 'identity_context': 'Brassica oleracea. Cool season vegetable, grown for its edible white curd.', 'soil_requirements': 'Similar to cabbage, fertile loamy soils.', 'climate_requirements': 'Cool season crop, sensitive to sudden temperature changes.', 'water_irrigation_needs': 'Requires consistent moisture during curd formation.', 'varieties': 'Pusa Katki, Early Synthetic.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High demand for Boron and Molybdenum.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Blanching (tying leaves over the curd) → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when curd is firm and white. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, whiptail.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'cabbage-silage': {'title': 'Cabbage Cultivation', 'identity_context': 'Brassica oleracea. Leafy vegetable, important for vitamins and minerals.', 'soil_requirements': 'Fertile, well-drained loamy soil, pH 6.0-6.5.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires constant moisture, frequent light irrigation.', 'varieties': 'Pusa Mukta, Golden Acre.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High NPK needs, especially N.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Head formation → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when heads are firm. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, black rot.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'carrot-silage': {'title': 'Carrot Cultivation', 'identity_context': 'Daucus carota. Root vegetable, rich in Vitamin A.', 'soil_requirements': 'Deep, loose, sandy loamy soils, stone-free.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires uniform moisture; avoid water stress during root growth.', 'varieties': 'Pusa Kesar, Nantes.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'High Potassium needs.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Deep ploughing to a depth of 30cm to allow straight root growth.', 'process_of_cultivation': 'Sowing → Thinning → Inter-culturing → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost, intercrop with onions.', 'harvesting_storage': 'Harvest when roots are fully developed. Store in cool, humid conditions.', 'estimated_cost': 'Low to moderate.', 'locations_of_cultivation': 'UP, Haryana, Punjab.', 'pests_affecting': 'Carrot weevil, leaf blight.', 'pest_control_measures': 'Chemical: Mancozeb. Organic: Crop rotation.'},
    'radish-silage': {'title': 'Radish Cultivation', 'identity_context': 'Raphanus sativus. Fast-growing root vegetable.', 'soil_requirements': 'Loose, sandy loam soils.', 'climate_requirements': 'Cool season crop, very quick maturity.', 'water_irrigation_needs': 'Requires constant moisture for tender roots.', 'varieties': 'Pusa Chetki (Tropical), Japanese White.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'Responds well to organic manure and balanced NPK.', 'season_of_cultivation': 'All year round (depending on variety).', 'land_preparation': 'Deep, fine tillage.', 'process_of_cultivation': 'Sowing → Thinning → Irrigation → Harvesting (25-45 days).', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers.', 'harvesting_storage': 'Harvest when roots reach optimal size. Cannot be stored long.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, flea beetles.', 'pest_control_measures': 'Chemical: Malathion. Organic: Neem oil.'},
    'spinach-silage': {'title': 'Spinach Cultivation', 'identity_context': 'Spinacia oleracea. Leafy vegetable, rich in iron.', 'soil_requirements': 'Wide range, deep fertile loams preferred.', 'climate_requirements': 'Cool season crop, sensitive to hot weather (causes bolting).', 'water_irrigation_needs': 'High moisture requirement, frequent light irrigation.', 'varieties': 'Pusa Jyoti, All Green.', 'seed_selection_sowing': 'Sown directly.', 'nutrient_management': 'High Nitrogen need for leaf growth.', 'season_of_cultivation': 'Rabi (winter).', 'land_preparation': 'Fine tilth, rich in organic matter.', 'process_of_cultivation': 'Sowing → Irrigation → Fertilization → Harvesting (multiple cuts).', 'organic_farming_practices': 'Heavy organic manure application.', 'harvesting_storage': 'Harvested by cutting leaves; consume fresh.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, leaf miners.', 'pest_control_measures': 'Organic: Neem oil, water spray.'},
    'brinjal-silage': {'title': 'Brinjal (Eggplant) Cultivation', 'identity_context': 'Solanum melongena. Warm-season vegetable, widely consumed.', 'soil_requirements': 'Fertile, well-drained sandy loam to clay loam.', 'climate_requirements': 'Warm season crop, sensitive to frost.', 'water_irrigation_needs': 'Moderate to high, critical at flowering.', 'varieties': 'Pusa Purple Long, Pusa Kranti.', 'seed_selection_sowing': 'Transplanted at 6-8 weeks old.', 'nutrient_management': 'High NPK demand.', 'season_of_cultivation': 'Kharif and Rabi.', 'land_preparation': 'Fine, deep tilth.', 'process_of_cultivation': 'Nursery → Transplanting → Staking (optional) → Irrigation → Harvesting (multiple pickings).', 'organic_farming_practices': 'Use compost, crop rotation.', 'harvesting_storage': 'Harvest when fruits are glossy. Store in cool, dark place.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'Majorly grown in almost all states.', 'pests_affecting': 'Fruit and shoot borer, jassids, little leaf disease.', 'pest_control_measures': 'Chemical: Carbaryl. Organic: Release of parasitoids.'},
    'peach-silage': {'title': 'Peach Cultivation', 'identity_context': 'Prunus persica. Temperate fruit, requiring chilling hours for production.', 'soil_requirements': 'Deep, well-drained, sandy loam soils.', 'climate_requirements': 'Temperate regions with adequate chilling hours and dry summers.', 'water_irrigation_needs': 'High water requirement during fruit development.', 'varieties': 'Early, mid, and late season varieties.', 'seed_selection_sowing': 'Grafted onto suitable rootstock.', 'nutrient_management': 'Balanced NPK and organic manure.', 'season_of_cultivation': 'Harvested in summer (May-August).', 'land_preparation': 'Pits are dug and filled.', 'process_of_cultivation': 'Planting → Pruning → Dormancy Management → Fertilization → Harvesting.', 'organic_farming_practices': 'Mulching and organic sprays.', 'harvesting_storage': 'Harvest when firm and colored. Store in cold storage.', 'estimated_cost': 'High initial cost.', 'locations_of_cultivation': 'Himachal Pradesh, Uttarakhand.', 'pests_affecting': 'Peach leaf curl, fruit fly.', 'pest_control_measures': 'Chemical: Fungicides during dormant season. Organic: Pheromone traps.'},
    'pomegranate-silage': {'title': 'Pomegranate Cultivation', 'identity_context': 'Punica granatum. Hardy fruit crop, known for drought tolerance and high commercial value.', 'soil_requirements': 'Adapted to a wide range of soils, deep alluvial or medium black soils preferred.', 'climate_requirements': 'Semi-arid and mild winter climate. Requires hot, dry summers.', 'water_irrigation_needs': 'Drought tolerant, but yields best with drip irrigation (400-600 mm).', 'varieties': 'Bhagwa, Ganesh, Ruby.', 'seed_selection_sowing': 'Propagated by hard wood cuttings.', 'nutrient_management': 'Requires NPK and FYM, split application of nitrogen.', 'season_of_cultivation': 'Flowering/fruiting can be managed (Bahar treatment) for specific seasons.', 'land_preparation': 'Deep tillage and planting pits.', 'process_of_cultivation': 'Planting → Pruning → Bahar Treatment → Fertilization → Harvesting.', 'organic_farming_practices': 'Pest control using neem-based products and mulching.', 'harvesting_storage': 'Harvest when skin color changes and sounds metallic when tapped. Good shelf life.', 'estimated_cost': 'Moderate establishment cost.', 'locations_of_cultivation': 'Maharashtra, Gujarat, Rajasthan.', 'pests_affecting': 'Fruit borer, anar butterfly.', 'pest_control_measures': 'Chemical: Lambda-cyhalothrin. Organic: Bagging of fruits.'},
    'papaya-silage': {'title': 'Papaya Cultivation', 'identity_context': 'Carica papaya. Fast-growing tropical fruit, high in Vitamin A and C.', 'soil_requirements': 'Well-drained sandy loam soil, sensitive to waterlogging.', 'climate_requirements': 'Warm, humid climate (21°C-33°C). Extremely sensitive to frost.', 'water_irrigation_needs': 'Frequent, light irrigation.', 'varieties': 'Pusa Dwarf, Coorg Honey Dew.', 'seed_selection_sowing': 'Sown directly or seedlings transplanted. Plant 1.5m apart.', 'nutrient_management': 'High NPK needs, especially K.', 'season_of_cultivation': 'Planted in all seasons except severe winter and heavy rains.', 'land_preparation': 'Ploughing and pit digging.', 'process_of_cultivation': 'Planting → Inter-cropping (early stages) → Fertilization → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers for better fruit quality.', 'harvesting_storage': 'Harvest when fruit shows yellow streaks. Store in cool place.', 'estimated_cost': 'Low initial cost, short gestation period.', 'locations_of_cultivation': 'Andhra Pradesh, Gujarat, Maharashtra.', 'pests_affecting': 'Root rot, papaya mosaic virus, aphids.', 'pest_control_measures': 'Chemical: Systemic insecticides for aphids. Organic: Roguing (removing) diseased plants.'},
    'cauliflower-silage': {'title': 'Cauliflower Cultivation', 'identity_context': 'Brassica oleracea. Cool season vegetable, grown for its edible white curd.', 'soil_requirements': 'Similar to cabbage, fertile loamy soils.', 'climate_requirements': 'Cool season crop, sensitive to sudden temperature changes.', 'water_irrigation_needs': 'Requires consistent moisture during curd formation.', 'varieties': 'Pusa Katki, Early Synthetic.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High demand for Boron and Molybdenum.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Blanching (tying leaves over the curd) → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when curd is firm and white. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, whiptail.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'cabbage-silage': {'title': 'Cabbage Cultivation', 'identity_context': 'Brassica oleracea. Leafy vegetable, important for vitamins and minerals.', 'soil_requirements': 'Fertile, well-drained loamy soil, pH 6.0-6.5.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires constant moisture, frequent light irrigation.', 'varieties': 'Pusa Mukta, Golden Acre.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High NPK needs, especially N.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Head formation → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when heads are firm. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, black rot.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'carrot-silage': {'title': 'Carrot Cultivation', 'identity_context': 'Daucus carota. Root vegetable, rich in Vitamin A.', 'soil_requirements': 'Deep, loose, sandy loamy soils, stone-free.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires uniform moisture; avoid water stress during root growth.', 'varieties': 'Pusa Kesar, Nantes.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'High Potassium needs.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Deep ploughing to a depth of 30cm to allow straight root growth.', 'process_of_cultivation': 'Sowing → Thinning → Inter-culturing → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost, intercrop with onions.', 'harvesting_storage': 'Harvest when roots are fully developed. Store in cool, humid conditions.', 'estimated_cost': 'Low to moderate.', 'locations_of_cultivation': 'UP, Haryana, Punjab.', 'pests_affecting': 'Carrot weevil, leaf blight.', 'pest_control_measures': 'Chemical: Mancozeb. Organic: Crop rotation.'},
    'radish-silage': {'title': 'Radish Cultivation', 'identity_context': 'Raphanus sativus. Fast-growing root vegetable.', 'soil_requirements': 'Loose, sandy loam soils.', 'climate_requirements': 'Cool season crop, very quick maturity.', 'water_irrigation_needs': 'Requires constant moisture for tender roots.', 'varieties': 'Pusa Chetki (Tropical), Japanese White.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'Responds well to organic manure and balanced NPK.', 'season_of_cultivation': 'All year round (depending on variety).', 'land_preparation': 'Deep, fine tillage.', 'process_of_cultivation': 'Sowing → Thinning → Irrigation → Harvesting (25-45 days).', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers.', 'harvesting_storage': 'Harvest when roots reach optimal size. Cannot be stored long.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, flea beetles.', 'pest_control_measures': 'Chemical: Malathion. Organic: Neem oil.'},
    'spinach-silage': {'title': 'Spinach Cultivation', 'identity_context': 'Spinacia oleracea. Leafy vegetable, rich in iron.', 'soil_requirements': 'Wide range, deep fertile loams preferred.', 'climate_requirements': 'Cool season crop, sensitive to hot weather (causes bolting).', 'water_irrigation_needs': 'High moisture requirement, frequent light irrigation.', 'varieties': 'Pusa Jyoti, All Green.', 'seed_selection_sowing': 'Sown directly.', 'nutrient_management': 'High Nitrogen need for leaf growth.', 'season_of_cultivation': 'Rabi (winter).', 'land_preparation': 'Fine tilth, rich in organic matter.', 'process_of_cultivation': 'Sowing → Irrigation → Fertilization → Harvesting (multiple cuts).', 'organic_farming_practices': 'Heavy organic manure application.', 'harvesting_storage': 'Harvested by cutting leaves; consume fresh.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, leaf miners.', 'pest_control_measures': 'Organic: Neem oil, water spray.'},
    'brinjal-silage': {'title': 'Brinjal (Eggplant) Cultivation', 'identity_context': 'Solanum melongena. Warm-season vegetable, widely consumed.', 'soil_requirements': 'Fertile, well-drained sandy loam to clay loam.', 'climate_requirements': 'Warm season crop, sensitive to frost.', 'water_irrigation_needs': 'Moderate to high, critical at flowering.', 'varieties': 'Pusa Purple Long, Pusa Kranti.', 'seed_selection_sowing': 'Transplanted at 6-8 weeks old.', 'nutrient_management': 'High NPK demand.', 'season_of_cultivation': 'Kharif and Rabi.', 'land_preparation': 'Fine, deep tilth.', 'process_of_cultivation': 'Nursery → Transplanting → Staking (optional) → Irrigation → Harvesting (multiple pickings).', 'organic_farming_practices': 'Use compost, crop rotation.', 'harvesting_storage': 'Harvest when fruits are glossy. Store in cool, dark place.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'Majorly grown in almost all states.', 'pests_affecting': 'Fruit and shoot borer, jassids, little leaf disease.', 'pest_control_measures': 'Chemical: Carbaryl. Organic: Release of parasitoids.'},
    'peach-silage': {'title': 'Peach Cultivation', 'identity_context': 'Prunus persica. Temperate fruit, requiring chilling hours for production.', 'soil_requirements': 'Deep, well-drained, sandy loam soils.', 'climate_requirements': 'Temperate regions with adequate chilling hours and dry summers.', 'water_irrigation_needs': 'High water requirement during fruit development.', 'varieties': 'Early, mid, and late season varieties.', 'seed_selection_sowing': 'Grafted onto suitable rootstock.', 'nutrient_management': 'Balanced NPK and organic manure.', 'season_of_cultivation': 'Harvested in summer (May-August).', 'land_preparation': 'Pits are dug and filled.', 'process_of_cultivation': 'Planting → Pruning → Dormancy Management → Fertilization → Harvesting.', 'organic_farming_practices': 'Mulching and organic sprays.', 'harvesting_storage': 'Harvest when firm and colored. Store in cold storage.', 'estimated_cost': 'High initial cost.', 'locations_of_cultivation': 'Himachal Pradesh, Uttarakhand.', 'pests_affecting': 'Peach leaf curl, fruit fly.', 'pest_control_measures': 'Chemical: Fungicides during dormant season. Organic: Pheromone traps.'},
    'pomegranate-silage': {'title': 'Pomegranate Cultivation', 'identity_context': 'Punica granatum. Hardy fruit crop, known for drought tolerance and high commercial value.', 'soil_requirements': 'Adapted to a wide range of soils, deep alluvial or medium black soils preferred.', 'climate_requirements': 'Semi-arid and mild winter climate. Requires hot, dry summers.', 'water_irrigation_needs': 'Drought tolerant, but yields best with drip irrigation (400-600 mm).', 'varieties': 'Bhagwa, Ganesh, Ruby.', 'seed_selection_sowing': 'Propagated by hard wood cuttings.', 'nutrient_management': 'Requires NPK and FYM, split application of nitrogen.', 'season_of_cultivation': 'Flowering/fruiting can be managed (Bahar treatment) for specific seasons.', 'land_preparation': 'Deep tillage and planting pits.', 'process_of_cultivation': 'Planting → Pruning → Bahar Treatment → Fertilization → Harvesting.', 'organic_farming_practices': 'Pest control using neem-based products and mulching.', 'harvesting_storage': 'Harvest when skin color changes and sounds metallic when tapped. Good shelf life.', 'estimated_cost': 'Moderate establishment cost.', 'locations_of_cultivation': 'Maharashtra, Gujarat, Rajasthan.', 'pests_affecting': 'Fruit borer, anar butterfly.', 'pest_control_measures': 'Chemical: Lambda-cyhalothrin. Organic: Bagging of fruits.'},
    'papaya-silage': {'title': 'Papaya Cultivation', 'identity_context': 'Carica papaya. Fast-growing tropical fruit, high in Vitamin A and C.', 'soil_requirements': 'Well-drained sandy loam soil, sensitive to waterlogging.', 'climate_requirements': 'Warm, humid climate (21°C-33°C). Extremely sensitive to frost.', 'water_irrigation_needs': 'Frequent, light irrigation.', 'varieties': 'Pusa Dwarf, Coorg Honey Dew.', 'seed_selection_sowing': 'Sown directly or seedlings transplanted. Plant 1.5m apart.', 'nutrient_management': 'High NPK needs, especially K.', 'season_of_cultivation': 'Planted in all seasons except severe winter and heavy rains.', 'land_preparation': 'Ploughing and pit digging.', 'process_of_cultivation': 'Planting → Inter-cropping (early stages) → Fertilization → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers for better fruit quality.', 'harvesting_storage': 'Harvest when fruit shows yellow streaks. Store in cool place.', 'estimated_cost': 'Low initial cost, short gestation period.', 'locations_of_cultivation': 'Andhra Pradesh, Gujarat, Maharashtra.', 'pests_affecting': 'Root rot, papaya mosaic virus, aphids.', 'pest_control_measures': 'Chemical: Systemic insecticides for aphids. Organic: Roguing (removing) diseased plants.'},
    'cauliflower-silage': {'title': 'Cauliflower Cultivation', 'identity_context': 'Brassica oleracea. Cool season vegetable, grown for its edible white curd.', 'soil_requirements': 'Similar to cabbage, fertile loamy soils.', 'climate_requirements': 'Cool season crop, sensitive to sudden temperature changes.', 'water_irrigation_needs': 'Requires consistent moisture during curd formation.', 'varieties': 'Pusa Katki, Early Synthetic.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High demand for Boron and Molybdenum.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Blanching (tying leaves over the curd) → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when curd is firm and white. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, whiptail.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'cabbage-silage': {'title': 'Cabbage Cultivation', 'identity_context': 'Brassica oleracea. Leafy vegetable, important for vitamins and minerals.', 'soil_requirements': 'Fertile, well-drained loamy soil, pH 6.0-6.5.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires constant moisture, frequent light irrigation.', 'varieties': 'Pusa Mukta, Golden Acre.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High NPK needs, especially N.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Head formation → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when heads are firm. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, black rot.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'carrot-silage': {'title': 'Carrot Cultivation', 'identity_context': 'Daucus carota. Root vegetable, rich in Vitamin A.', 'soil_requirements': 'Deep, loose, sandy loamy soils, stone-free.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires uniform moisture; avoid water stress during root growth.', 'varieties': 'Pusa Kesar, Nantes.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'High Potassium needs.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Deep ploughing to a depth of 30cm to allow straight root growth.', 'process_of_cultivation': 'Sowing → Thinning → Inter-culturing → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost, intercrop with onions.', 'harvesting_storage': 'Harvest when roots are fully developed. Store in cool, humid conditions.', 'estimated_cost': 'Low to moderate.', 'locations_of_cultivation': 'UP, Haryana, Punjab.', 'pests_affecting': 'Carrot weevil, leaf blight.', 'pest_control_measures': 'Chemical: Mancozeb. Organic: Crop rotation.'},
    'radish-silage': {'title': 'Radish Cultivation', 'identity_context': 'Raphanus sativus. Fast-growing root vegetable.', 'soil_requirements': 'Loose, sandy loam soils.', 'climate_requirements': 'Cool season crop, very quick maturity.', 'water_irrigation_needs': 'Requires constant moisture for tender roots.', 'varieties': 'Pusa Chetki (Tropical), Japanese White.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'Responds well to organic manure and balanced NPK.', 'season_of_cultivation': 'All year round (depending on variety).', 'land_preparation': 'Deep, fine tillage.', 'process_of_cultivation': 'Sowing → Thinning → Irrigation → Harvesting (25-45 days).', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers.', 'harvesting_storage': 'Harvest when roots reach optimal size. Cannot be stored long.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, flea beetles.', 'pest_control_measures': 'Chemical: Malathion. Organic: Neem oil.'},
    'spinach-silage': {'title': 'Spinach Cultivation', 'identity_context': 'Spinacia oleracea. Leafy vegetable, rich in iron.', 'soil_requirements': 'Wide range, deep fertile loams preferred.', 'climate_requirements': 'Cool season crop, sensitive to hot weather (causes bolting).', 'water_irrigation_needs': 'High moisture requirement, frequent light irrigation.', 'varieties': 'Pusa Jyoti, All Green.', 'seed_selection_sowing': 'Sown directly.', 'nutrient_management': 'High Nitrogen need for leaf growth.', 'season_of_cultivation': 'Rabi (winter).', 'land_preparation': 'Fine tilth, rich in organic matter.', 'process_of_cultivation': 'Sowing → Irrigation → Fertilization → Harvesting (multiple cuts).', 'organic_farming_practices': 'Heavy organic manure application.', 'harvesting_storage': 'Harvested by cutting leaves; consume fresh.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, leaf miners.', 'pest_control_measures': 'Organic: Neem oil, water spray.'},
    'brinjal-silage': {'title': 'Brinjal (Eggplant) Cultivation', 'identity_context': 'Solanum melongena. Warm-season vegetable, widely consumed.', 'soil_requirements': 'Fertile, well-drained sandy loam to clay loam.', 'climate_requirements': 'Warm season crop, sensitive to frost.', 'water_irrigation_needs': 'Moderate to high, critical at flowering.', 'varieties': 'Pusa Purple Long, Pusa Kranti.', 'seed_selection_sowing': 'Transplanted at 6-8 weeks old.', 'nutrient_management': 'High NPK demand.', 'season_of_cultivation': 'Kharif and Rabi.', 'land_preparation': 'Fine, deep tilth.', 'process_of_cultivation': 'Nursery → Transplanting → Staking (optional) → Irrigation → Harvesting (multiple pickings).', 'organic_farming_practices': 'Use compost, crop rotation.', 'harvesting_storage': 'Harvest when fruits are glossy. Store in cool, dark place.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'Majorly grown in almost all states.', 'pests_affecting': 'Fruit and shoot borer, jassids, little leaf disease.', 'pest_control_measures': 'Chemical: Carbaryl. Organic: Release of parasitoids.'},
    'peach-silage': {'title': 'Peach Cultivation', 'identity_context': 'Prunus persica. Temperate fruit, requiring chilling hours for production.', 'soil_requirements': 'Deep, well-drained, sandy loam soils.', 'climate_requirements': 'Temperate regions with adequate chilling hours and dry summers.', 'water_irrigation_needs': 'High water requirement during fruit development.', 'varieties': 'Early, mid, and late season varieties.', 'seed_selection_sowing': 'Grafted onto suitable rootstock.', 'nutrient_management': 'Balanced NPK and organic manure.', 'season_of_cultivation': 'Harvested in summer (May-August).', 'land_preparation': 'Pits are dug and filled.', 'process_of_cultivation': 'Planting → Pruning → Dormancy Management → Fertilization → Harvesting.', 'organic_farming_practices': 'Mulching and organic sprays.', 'harvesting_storage': 'Harvest when firm and colored. Store in cold storage.', 'estimated_cost': 'High initial cost.', 'locations_of_cultivation': 'Himachal Pradesh, Uttarakhand.', 'pests_affecting': 'Peach leaf curl, fruit fly.', 'pest_control_measures': 'Chemical: Fungicides during dormant season. Organic: Pheromone traps.'},
    'pomegranate-silage': {'title': 'Pomegranate Cultivation', 'identity_context': 'Punica granatum. Hardy fruit crop, known for drought tolerance and high commercial value.', 'soil_requirements': 'Adapted to a wide range of soils, deep alluvial or medium black soils preferred.', 'climate_requirements': 'Semi-arid and mild winter climate. Requires hot, dry summers.', 'water_irrigation_needs': 'Drought tolerant, but yields best with drip irrigation (400-600 mm).', 'varieties': 'Bhagwa, Ganesh, Ruby.', 'seed_selection_sowing': 'Propagated by hard wood cuttings.', 'nutrient_management': 'Requires NPK and FYM, split application of nitrogen.', 'season_of_cultivation': 'Flowering/fruiting can be managed (Bahar treatment) for specific seasons.', 'land_preparation': 'Deep tillage and planting pits.', 'process_of_cultivation': 'Planting → Pruning → Bahar Treatment → Fertilization → Harvesting.', 'organic_farming_practices': 'Pest control using neem-based products and mulching.', 'harvesting_storage': 'Harvest when skin color changes and sounds metallic when tapped. Good shelf life.', 'estimated_cost': 'Moderate establishment cost.', 'locations_of_cultivation': 'Maharashtra, Gujarat, Rajasthan.', 'pests_affecting': 'Fruit borer, anar butterfly.', 'pest_control_measures': 'Chemical: Lambda-cyhalothrin. Organic: Bagging of fruits.'},
    'papaya-silage': {'title': 'Papaya Cultivation', 'identity_context': 'Carica papaya. Fast-growing tropical fruit, high in Vitamin A and C.', 'soil_requirements': 'Well-drained sandy loam soil, sensitive to waterlogging.', 'climate_requirements': 'Warm, humid climate (21°C-33°C). Extremely sensitive to frost.', 'water_irrigation_needs': 'Frequent, light irrigation.', 'varieties': 'Pusa Dwarf, Coorg Honey Dew.', 'seed_selection_sowing': 'Sown directly or seedlings transplanted. Plant 1.5m apart.', 'nutrient_management': 'High NPK needs, especially K.', 'season_of_cultivation': 'Planted in all seasons except severe winter and heavy rains.', 'land_preparation': 'Ploughing and pit digging.', 'process_of_cultivation': 'Planting → Inter-cropping (early stages) → Fertilization → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers for better fruit quality.', 'harvesting_storage': 'Harvest when fruit shows yellow streaks. Store in cool place.', 'estimated_cost': 'Low initial cost, short gestation period.', 'locations_of_cultivation': 'Andhra Pradesh, Gujarat, Maharashtra.', 'pests_affecting': 'Root rot, papaya mosaic virus, aphids.', 'pest_control_measures': 'Chemical: Systemic insecticides for aphids. Organic: Roguing (removing) diseased plants.'},
    'cauliflower-silage': {'title': 'Cauliflower Cultivation', 'identity_context': 'Brassica oleracea. Cool season vegetable, grown for its edible white curd.', 'soil_requirements': 'Similar to cabbage, fertile loamy soils.', 'climate_requirements': 'Cool season crop, sensitive to sudden temperature changes.', 'water_irrigation_needs': 'Requires consistent moisture during curd formation.', 'varieties': 'Pusa Katki, Early Synthetic.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High demand for Boron and Molybdenum.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Blanching (tying leaves over the curd) → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when curd is firm and white. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, whiptail.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'cabbage-silage': {'title': 'Cabbage Cultivation', 'identity_context': 'Brassica oleracea. Leafy vegetable, important for vitamins and minerals.', 'soil_requirements': 'Fertile, well-drained loamy soil, pH 6.0-6.5.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires constant moisture, frequent light irrigation.', 'varieties': 'Pusa Mukta, Golden Acre.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High NPK needs, especially N.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Head formation → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when heads are firm. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, black rot.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'carrot-silage': {'title': 'Carrot Cultivation', 'identity_context': 'Daucus carota. Root vegetable, rich in Vitamin A.', 'soil_requirements': 'Deep, loose, sandy loamy soils, stone-free.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires uniform moisture; avoid water stress during root growth.', 'varieties': 'Pusa Kesar, Nantes.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'High Potassium needs.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Deep ploughing to a depth of 30cm to allow straight root growth.', 'process_of_cultivation': 'Sowing → Thinning → Inter-culturing → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost, intercrop with onions.', 'harvesting_storage': 'Harvest when roots are fully developed. Store in cool, humid conditions.', 'estimated_cost': 'Low to moderate.', 'locations_of_cultivation': 'UP, Haryana, Punjab.', 'pests_affecting': 'Carrot weevil, leaf blight.', 'pest_control_measures': 'Chemical: Mancozeb. Organic: Crop rotation.'},
    'radish-silage': {'title': 'Radish Cultivation', 'identity_context': 'Raphanus sativus. Fast-growing root vegetable.', 'soil_requirements': 'Loose, sandy loam soils.', 'climate_requirements': 'Cool season crop, very quick maturity.', 'water_irrigation_needs': 'Requires constant moisture for tender roots.', 'varieties': 'Pusa Chetki (Tropical), Japanese White.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'Responds well to organic manure and balanced NPK.', 'season_of_cultivation': 'All year round (depending on variety).', 'land_preparation': 'Deep, fine tillage.', 'process_of_cultivation': 'Sowing → Thinning → Irrigation → Harvesting (25-45 days).', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers.', 'harvesting_storage': 'Harvest when roots reach optimal size. Cannot be stored long.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, flea beetles.', 'pest_control_measures': 'Chemical: Malathion. Organic: Neem oil.'},
    'spinach-silage': {'title': 'Spinach Cultivation', 'identity_context': 'Spinacia oleracea. Leafy vegetable, rich in iron.', 'soil_requirements': 'Wide range, deep fertile loams preferred.', 'climate_requirements': 'Cool season crop, sensitive to hot weather (causes bolting).', 'water_irrigation_needs': 'High moisture requirement, frequent light irrigation.', 'varieties': 'Pusa Jyoti, All Green.', 'seed_selection_sowing': 'Sown directly.', 'nutrient_management': 'High Nitrogen need for leaf growth.', 'season_of_cultivation': 'Rabi (winter).', 'land_preparation': 'Fine tilth, rich in organic matter.', 'process_of_cultivation': 'Sowing → Irrigation → Fertilization → Harvesting (multiple cuts).', 'organic_farming_practices': 'Heavy organic manure application.', 'harvesting_storage': 'Harvested by cutting leaves; consume fresh.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, leaf miners.', 'pest_control_measures': 'Organic: Neem oil, water spray.'},
    'brinjal-silage': {'title': 'Brinjal (Eggplant) Cultivation', 'identity_context': 'Solanum melongena. Warm-season vegetable, widely consumed.', 'soil_requirements': 'Fertile, well-drained sandy loam to clay loam.', 'climate_requirements': 'Warm season crop, sensitive to frost.', 'water_irrigation_needs': 'Moderate to high, critical at flowering.', 'varieties': 'Pusa Purple Long, Pusa Kranti.', 'seed_selection_sowing': 'Transplanted at 6-8 weeks old.', 'nutrient_management': 'High NPK demand.', 'season_of_cultivation': 'Kharif and Rabi.', 'land_preparation': 'Fine, deep tilth.', 'process_of_cultivation': 'Nursery → Transplanting → Staking (optional) → Irrigation → Harvesting (multiple pickings).', 'organic_farming_practices': 'Use compost, crop rotation.', 'harvesting_storage': 'Harvest when fruits are glossy. Store in cool, dark place.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'Majorly grown in almost all states.', 'pests_affecting': 'Fruit and shoot borer, jassids, little leaf disease.', 'pest_control_measures': 'Chemical: Carbaryl. Organic: Release of parasitoids.'},
    'peach-silage': {'title': 'Peach Cultivation', 'identity_context': 'Prunus persica. Temperate fruit, requiring chilling hours for production.', 'soil_requirements': 'Deep, well-drained, sandy loam soils.', 'climate_requirements': 'Temperate regions with adequate chilling hours and dry summers.', 'water_irrigation_needs': 'High water requirement during fruit development.', 'varieties': 'Early, mid, and late season varieties.', 'seed_selection_sowing': 'Grafted onto suitable rootstock.', 'nutrient_management': 'Balanced NPK and organic manure.', 'season_of_cultivation': 'Harvested in summer (May-August).', 'land_preparation': 'Pits are dug and filled.', 'process_of_cultivation': 'Planting → Pruning → Dormancy Management → Fertilization → Harvesting.', 'organic_farming_practices': 'Mulching and organic sprays.', 'harvesting_storage': 'Harvest when firm and colored. Store in cold storage.', 'estimated_cost': 'High initial cost.', 'locations_of_cultivation': 'Himachal Pradesh, Uttarakhand.', 'pests_affecting': 'Peach leaf curl, fruit fly.', 'pest_control_measures': 'Chemical: Fungicides during dormant season. Organic: Pheromone traps.'},
    'pomegranate-silage': {'title': 'Pomegranate Cultivation', 'identity_context': 'Punica granatum. Hardy fruit crop, known for drought tolerance and high commercial value.', 'soil_requirements': 'Adapted to a wide range of soils, deep alluvial or medium black soils preferred.', 'climate_requirements': 'Semi-arid and mild winter climate. Requires hot, dry summers.', 'water_irrigation_needs': 'Drought tolerant, but yields best with drip irrigation (400-600 mm).', 'varieties': 'Bhagwa, Ganesh, Ruby.', 'seed_selection_sowing': 'Propagated by hard wood cuttings.', 'nutrient_management': 'Requires NPK and FYM, split application of nitrogen.', 'season_of_cultivation': 'Flowering/fruiting can be managed (Bahar treatment) for specific seasons.', 'land_preparation': 'Deep tillage and planting pits.', 'process_of_cultivation': 'Planting → Pruning → Bahar Treatment → Fertilization → Harvesting.', 'organic_farming_practices': 'Pest control using neem-based products and mulching.', 'harvesting_storage': 'Harvest when skin color changes and sounds metallic when tapped. Good shelf life.', 'estimated_cost': 'Moderate establishment cost.', 'locations_of_cultivation': 'Maharashtra, Gujarat, Rajasthan.', 'pests_affecting': 'Fruit borer, anar butterfly.', 'pest_control_measures': 'Chemical: Lambda-cyhalothrin. Organic: Bagging of fruits.'},
    'papaya-silage': {'title': 'Papaya Cultivation', 'identity_context': 'Carica papaya. Fast-growing tropical fruit, high in Vitamin A and C.', 'soil_requirements': 'Well-drained sandy loam soil, sensitive to waterlogging.', 'climate_requirements': 'Warm, humid climate (21°C-33°C). Extremely sensitive to frost.', 'water_irrigation_needs': 'Frequent, light irrigation.', 'varieties': 'Pusa Dwarf, Coorg Honey Dew.', 'seed_selection_sowing': 'Sown directly or seedlings transplanted. Plant 1.5m apart.', 'nutrient_management': 'High NPK needs, especially K.', 'season_of_cultivation': 'Planted in all seasons except severe winter and heavy rains.', 'land_preparation': 'Ploughing and pit digging.', 'process_of_cultivation': 'Planting → Inter-cropping (early stages) → Fertilization → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers for better fruit quality.', 'harvesting_storage': 'Harvest when fruit shows yellow streaks. Store in cool place.', 'estimated_cost': 'Low initial cost, short gestation period.', 'locations_of_cultivation': 'Andhra Pradesh, Gujarat, Maharashtra.', 'pests_affecting': 'Root rot, papaya mosaic virus, aphids.', 'pest_control_measures': 'Chemical: Systemic insecticides for aphids. Organic: Roguing (removing) diseased plants.'},
    'cauliflower-silage': {'title': 'Cauliflower Cultivation', 'identity_context': 'Brassica oleracea. Cool season vegetable, grown for its edible white curd.', 'soil_requirements': 'Similar to cabbage, fertile loamy soils.', 'climate_requirements': 'Cool season crop, sensitive to sudden temperature changes.', 'water_irrigation_needs': 'Requires consistent moisture during curd formation.', 'varieties': 'Pusa Katki, Early Synthetic.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High demand for Boron and Molybdenum.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Blanching (tying leaves over the curd) → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when curd is firm and white. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, whiptail.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'cabbage-silage': {'title': 'Cabbage Cultivation', 'identity_context': 'Brassica oleracea. Leafy vegetable, important for vitamins and minerals.', 'soil_requirements': 'Fertile, well-drained loamy soil, pH 6.0-6.5.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires constant moisture, frequent light irrigation.', 'varieties': 'Pusa Mukta, Golden Acre.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High NPK needs, especially N.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Head formation → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when heads are firm. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, black rot.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'carrot-silage': {'title': 'Carrot Cultivation', 'identity_context': 'Daucus carota. Root vegetable, rich in Vitamin A.', 'soil_requirements': 'Deep, loose, sandy loamy soils, stone-free.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires uniform moisture; avoid water stress during root growth.', 'varieties': 'Pusa Kesar, Nantes.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'High Potassium needs.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Deep ploughing to a depth of 30cm to allow straight root growth.', 'process_of_cultivation': 'Sowing → Thinning → Inter-culturing → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost, intercrop with onions.', 'harvesting_storage': 'Harvest when roots are fully developed. Store in cool, humid conditions.', 'estimated_cost': 'Low to moderate.', 'locations_of_cultivation': 'UP, Haryana, Punjab.', 'pests_affecting': 'Carrot weevil, leaf blight.', 'pest_control_measures': 'Chemical: Mancozeb. Organic: Crop rotation.'},
    'radish-silage': {'title': 'Radish Cultivation', 'identity_context': 'Raphanus sativus. Fast-growing root vegetable.', 'soil_requirements': 'Loose, sandy loam soils.', 'climate_requirements': 'Cool season crop, very quick maturity.', 'water_irrigation_needs': 'Requires constant moisture for tender roots.', 'varieties': 'Pusa Chetki (Tropical), Japanese White.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'Responds well to organic manure and balanced NPK.', 'season_of_cultivation': 'All year round (depending on variety).', 'land_preparation': 'Deep, fine tillage.', 'process_of_cultivation': 'Sowing → Thinning → Irrigation → Harvesting (25-45 days).', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers.', 'harvesting_storage': 'Harvest when roots reach optimal size. Cannot be stored long.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, flea beetles.', 'pest_control_measures': 'Chemical: Malathion. Organic: Neem oil.'},
    'spinach-silage': {'title': 'Spinach Cultivation', 'identity_context': 'Spinacia oleracea. Leafy vegetable, rich in iron.', 'soil_requirements': 'Wide range, deep fertile loams preferred.', 'climate_requirements': 'Cool season crop, sensitive to hot weather (causes bolting).', 'water_irrigation_needs': 'High moisture requirement, frequent light irrigation.', 'varieties': 'Pusa Jyoti, All Green.', 'seed_selection_sowing': 'Sown directly.', 'nutrient_management': 'High Nitrogen need for leaf growth.', 'season_of_cultivation': 'Rabi (winter).', 'land_preparation': 'Fine tilth, rich in organic matter.', 'process_of_cultivation': 'Sowing → Irrigation → Fertilization → Harvesting (multiple cuts).', 'organic_farming_practices': 'Heavy organic manure application.', 'harvesting_storage': 'Harvested by cutting leaves; consume fresh.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, leaf miners.', 'pest_control_measures': 'Organic: Neem oil, water spray.'},
    'brinjal-silage': {'title': 'Brinjal (Eggplant) Cultivation', 'identity_context': 'Solanum melongena. Warm-season vegetable, widely consumed.', 'soil_requirements': 'Fertile, well-drained sandy loam to clay loam.', 'climate_requirements': 'Warm season crop, sensitive to frost.', 'water_irrigation_needs': 'Moderate to high, critical at flowering.', 'varieties': 'Pusa Purple Long, Pusa Kranti.', 'seed_selection_sowing': 'Transplanted at 6-8 weeks old.', 'nutrient_management': 'High NPK demand.', 'season_of_cultivation': 'Kharif and Rabi.', 'land_preparation': 'Fine, deep tilth.', 'process_of_cultivation': 'Nursery → Transplanting → Staking (optional) → Irrigation → Harvesting (multiple pickings).', 'organic_farming_practices': 'Use compost, crop rotation.', 'harvesting_storage': 'Harvest when fruits are glossy. Store in cool, dark place.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'Majorly grown in almost all states.', 'pests_affecting': 'Fruit and shoot borer, jassids, little leaf disease.', 'pest_control_measures': 'Chemical: Carbaryl. Organic: Release of parasitoids.'},
    'peach-silage': {'title': 'Peach Cultivation', 'identity_context': 'Prunus persica. Temperate fruit, requiring chilling hours for production.', 'soil_requirements': 'Deep, well-drained, sandy loam soils.', 'climate_requirements': 'Temperate regions with adequate chilling hours and dry summers.', 'water_irrigation_needs': 'High water requirement during fruit development.', 'varieties': 'Early, mid, and late season varieties.', 'seed_selection_sowing': 'Grafted onto suitable rootstock.', 'nutrient_management': 'Balanced NPK and organic manure.', 'season_of_cultivation': 'Harvested in summer (May-August).', 'land_preparation': 'Pits are dug and filled.', 'process_of_cultivation': 'Planting → Pruning → Dormancy Management → Fertilization → Harvesting.', 'organic_farming_practices': 'Mulching and organic sprays.', 'harvesting_storage': 'Harvest when firm and colored. Store in cold storage.', 'estimated_cost': 'High initial cost.', 'locations_of_cultivation': 'Himachal Pradesh, Uttarakhand.', 'pests_affecting': 'Peach leaf curl, fruit fly.', 'pest_control_measures': 'Chemical: Fungicides during dormant season. Organic: Pheromone traps.'},
    'pomegranate-silage': {'title': 'Pomegranate Cultivation', 'identity_context': 'Punica granatum. Hardy fruit crop, known for drought tolerance and high commercial value.', 'soil_requirements': 'Adapted to a wide range of soils, deep alluvial or medium black soils preferred.', 'climate_requirements': 'Semi-arid and mild winter climate. Requires hot, dry summers.', 'water_irrigation_needs': 'Drought tolerant, but yields best with drip irrigation (400-600 mm).', 'varieties': 'Bhagwa, Ganesh, Ruby.', 'seed_selection_sowing': 'Propagated by hard wood cuttings.', 'nutrient_management': 'Requires NPK and FYM, split application of nitrogen.', 'season_of_cultivation': 'Flowering/fruiting can be managed (Bahar treatment) for specific seasons.', 'land_preparation': 'Deep tillage and planting pits.', 'process_of_cultivation': 'Planting → Pruning → Bahar Treatment → Fertilization → Harvesting.', 'organic_farming_practices': 'Pest control using neem-based products and mulching.', 'harvesting_storage': 'Harvest when skin color changes and sounds metallic when tapped. Good shelf life.', 'estimated_cost': 'Moderate establishment cost.', 'locations_of_cultivation': 'Maharashtra, Gujarat, Rajasthan.', 'pests_affecting': 'Fruit borer, anar butterfly.', 'pest_control_measures': 'Chemical: Lambda-cyhalothrin. Organic: Bagging of fruits.'},
    'papaya-silage': {'title': 'Papaya Cultivation', 'identity_context': 'Carica papaya. Fast-growing tropical fruit, high in Vitamin A and C.', 'soil_requirements': 'Well-drained sandy loam soil, sensitive to waterlogging.', 'climate_requirements': 'Warm, humid climate (21°C-33°C). Extremely sensitive to frost.', 'water_irrigation_needs': 'Frequent, light irrigation.', 'varieties': 'Pusa Dwarf, Coorg Honey Dew.', 'seed_selection_sowing': 'Sown directly or seedlings transplanted. Plant 1.5m apart.', 'nutrient_management': 'High NPK needs, especially K.', 'season_of_cultivation': 'Planted in all seasons except severe winter and heavy rains.', 'land_preparation': 'Ploughing and pit digging.', 'process_of_cultivation': 'Planting → Inter-cropping (early stages) → Fertilization → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers for better fruit quality.', 'harvesting_storage': 'Harvest when fruit shows yellow streaks. Store in cool place.', 'estimated_cost': 'Low initial cost, short gestation period.', 'locations_of_cultivation': 'Andhra Pradesh, Gujarat, Maharashtra.', 'pests_affecting': 'Root rot, papaya mosaic virus, aphids.', 'pest_control_measures': 'Chemical: Systemic insecticides for aphids. Organic: Roguing (removing) diseased plants.'},
    'cauliflower-silage': {'title': 'Cauliflower Cultivation', 'identity_context': 'Brassica oleracea. Cool season vegetable, grown for its edible white curd.', 'soil_requirements': 'Similar to cabbage, fertile loamy soils.', 'climate_requirements': 'Cool season crop, sensitive to sudden temperature changes.', 'water_irrigation_needs': 'Requires consistent moisture during curd formation.', 'varieties': 'Pusa Katki, Early Synthetic.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High demand for Boron and Molybdenum.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Blanching (tying leaves over the curd) → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when curd is firm and white. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, whiptail.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'cabbage-silage': {'title': 'Cabbage Cultivation', 'identity_context': 'Brassica oleracea. Leafy vegetable, important for vitamins and minerals.', 'soil_requirements': 'Fertile, well-drained loamy soil, pH 6.0-6.5.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires constant moisture, frequent light irrigation.', 'varieties': 'Pusa Mukta, Golden Acre.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High NPK needs, especially N.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Head formation → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when heads are firm. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, black rot.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'carrot-silage': {'title': 'Carrot Cultivation', 'identity_context': 'Daucus carota. Root vegetable, rich in Vitamin A.', 'soil_requirements': 'Deep, loose, sandy loamy soils, stone-free.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires uniform moisture; avoid water stress during root growth.', 'varieties': 'Pusa Kesar, Nantes.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'High Potassium needs.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Deep ploughing to a depth of 30cm to allow straight root growth.', 'process_of_cultivation': 'Sowing → Thinning → Inter-culturing → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost, intercrop with onions.', 'harvesting_storage': 'Harvest when roots are fully developed. Store in cool, humid conditions.', 'estimated_cost': 'Low to moderate.', 'locations_of_cultivation': 'UP, Haryana, Punjab.', 'pests_affecting': 'Carrot weevil, leaf blight.', 'pest_control_measures': 'Chemical: Mancozeb. Organic: Crop rotation.'},
    'radish-silage': {'title': 'Radish Cultivation', 'identity_context': 'Raphanus sativus. Fast-growing root vegetable.', 'soil_requirements': 'Loose, sandy loam soils.', 'climate_requirements': 'Cool season crop, very quick maturity.', 'water_irrigation_needs': 'Requires constant moisture for tender roots.', 'varieties': 'Pusa Chetki (Tropical), Japanese White.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'Responds well to organic manure and balanced NPK.', 'season_of_cultivation': 'All year round (depending on variety).', 'land_preparation': 'Deep, fine tillage.', 'process_of_cultivation': 'Sowing → Thinning → Irrigation → Harvesting (25-45 days).', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers.', 'harvesting_storage': 'Harvest when roots reach optimal size. Cannot be stored long.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, flea beetles.', 'pest_control_measures': 'Chemical: Malathion. Organic: Neem oil.'},
    'spinach-silage': {'title': 'Spinach Cultivation', 'identity_context': 'Spinacia oleracea. Leafy vegetable, rich in iron.', 'soil_requirements': 'Wide range, deep fertile loams preferred.', 'climate_requirements': 'Cool season crop, sensitive to hot weather (causes bolting).', 'water_irrigation_needs': 'High moisture requirement, frequent light irrigation.', 'varieties': 'Pusa Jyoti, All Green.', 'seed_selection_sowing': 'Sown directly.', 'nutrient_management': 'High Nitrogen need for leaf growth.', 'season_of_cultivation': 'Rabi (winter).', 'land_preparation': 'Fine tilth, rich in organic matter.', 'process_of_cultivation': 'Sowing → Irrigation → Fertilization → Harvesting (multiple cuts).', 'organic_farming_practices': 'Heavy organic manure application.', 'harvesting_storage': 'Harvested by cutting leaves; consume fresh.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, leaf miners.', 'pest_control_measures': 'Organic: Neem oil, water spray.'},
    'brinjal-silage': {'title': 'Brinjal (Eggplant) Cultivation', 'identity_context': 'Solanum melongena. Warm-season vegetable, widely consumed.', 'soil_requirements': 'Fertile, well-drained sandy loam to clay loam.', 'climate_requirements': 'Warm season crop, sensitive to frost.', 'water_irrigation_needs': 'Moderate to high, critical at flowering.', 'varieties': 'Pusa Purple Long, Pusa Kranti.', 'seed_selection_sowing': 'Transplanted at 6-8 weeks old.', 'nutrient_management': 'High NPK demand.', 'season_of_cultivation': 'Kharif and Rabi.', 'land_preparation': 'Fine, deep tilth.', 'process_of_cultivation': 'Nursery → Transplanting → Staking (optional) → Irrigation → Harvesting (multiple pickings).', 'organic_farming_practices': 'Use compost, crop rotation.', 'harvesting_storage': 'Harvest when fruits are glossy. Store in cool, dark place.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'Majorly grown in almost all states.', 'pests_affecting': 'Fruit and shoot borer, jassids, little leaf disease.', 'pest_control_measures': 'Chemical: Carbaryl. Organic: Release of parasitoids.'},
    'peach-silage': {'title': 'Peach Cultivation', 'identity_context': 'Prunus persica. Temperate fruit, requiring chilling hours for production.', 'soil_requirements': 'Deep, well-drained, sandy loam soils.', 'climate_requirements': 'Temperate regions with adequate chilling hours and dry summers.', 'water_irrigation_needs': 'High water requirement during fruit development.', 'varieties': 'Early, mid, and late season varieties.', 'seed_selection_sowing': 'Grafted onto suitable rootstock.', 'nutrient_management': 'Balanced NPK and organic manure.', 'season_of_cultivation': 'Harvested in summer (May-August).', 'land_preparation': 'Pits are dug and filled.', 'process_of_cultivation': 'Planting → Pruning → Dormancy Management → Fertilization → Harvesting.', 'organic_farming_practices': 'Mulching and organic sprays.', 'harvesting_storage': 'Harvest when firm and colored. Store in cold storage.', 'estimated_cost': 'High initial cost.', 'locations_of_cultivation': 'Himachal Pradesh, Uttarakhand.', 'pests_affecting': 'Peach leaf curl, fruit fly.', 'pest_control_measures': 'Chemical: Fungicides during dormant season. Organic: Pheromone traps.'},
    'pomegranate-silage': {'title': 'Pomegranate Cultivation', 'identity_context': 'Punica granatum. Hardy fruit crop, known for drought tolerance and high commercial value.', 'soil_requirements': 'Adapted to a wide range of soils, deep alluvial or medium black soils preferred.', 'climate_requirements': 'Semi-arid and mild winter climate. Requires hot, dry summers.', 'water_irrigation_needs': 'Drought tolerant, but yields best with drip irrigation (400-600 mm).', 'varieties': 'Bhagwa, Ganesh, Ruby.', 'seed_selection_sowing': 'Propagated by hard wood cuttings.', 'nutrient_management': 'Requires NPK and FYM, split application of nitrogen.', 'season_of_cultivation': 'Flowering/fruiting can be managed (Bahar treatment) for specific seasons.', 'land_preparation': 'Deep tillage and planting pits.', 'process_of_cultivation': 'Planting → Pruning → Bahar Treatment → Fertilization → Harvesting.', 'organic_farming_practices': 'Pest control using neem-based products and mulching.', 'harvesting_storage': 'Harvest when skin color changes and sounds metallic when tapped. Good shelf life.', 'estimated_cost': 'Moderate establishment cost.', 'locations_of_cultivation': 'Maharashtra, Gujarat, Rajasthan.', 'pests_affecting': 'Fruit borer, anar butterfly.', 'pest_control_measures': 'Chemical: Lambda-cyhalothrin. Organic: Bagging of fruits.'},
    'papaya-silage': {'title': 'Papaya Cultivation', 'identity_context': 'Carica papaya. Fast-growing tropical fruit, high in Vitamin A and C.', 'soil_requirements': 'Well-drained sandy loam soil, sensitive to waterlogging.', 'climate_requirements': 'Warm, humid climate (21°C-33°C). Extremely sensitive to frost.', 'water_irrigation_needs': 'Frequent, light irrigation.', 'varieties': 'Pusa Dwarf, Coorg Honey Dew.', 'seed_selection_sowing': 'Sown directly or seedlings transplanted. Plant 1.5m apart.', 'nutrient_management': 'High NPK needs, especially K.', 'season_of_cultivation': 'Planted in all seasons except severe winter and heavy rains.', 'land_preparation': 'Ploughing and pit digging.', 'process_of_cultivation': 'Planting → Inter-cropping (early stages) → Fertilization → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers for better fruit quality.', 'harvesting_storage': 'Harvest when fruit shows yellow streaks. Store in cool place.', 'estimated_cost': 'Low initial cost, short gestation period.', 'locations_of_cultivation': 'Andhra Pradesh, Gujarat, Maharashtra.', 'pests_affecting': 'Root rot, papaya mosaic virus, aphids.', 'pest_control_measures': 'Chemical: Systemic insecticides for aphids. Organic: Roguing (removing) diseased plants.'},
    'cauliflower-silage': {'title': 'Cauliflower Cultivation', 'identity_context': 'Brassica oleracea. Cool season vegetable, grown for its edible white curd.', 'soil_requirements': 'Similar to cabbage, fertile loamy soils.', 'climate_requirements': 'Cool season crop, sensitive to sudden temperature changes.', 'water_irrigation_needs': 'Requires consistent moisture during curd formation.', 'varieties': 'Pusa Katki, Early Synthetic.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High demand for Boron and Molybdenum.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Blanching (tying leaves over the curd) → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when curd is firm and white. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, whiptail.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'cabbage-silage': {'title': 'Cabbage Cultivation', 'identity_context': 'Brassica oleracea. Leafy vegetable, important for vitamins and minerals.', 'soil_requirements': 'Fertile, well-drained loamy soil, pH 6.0-6.5.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires constant moisture, frequent light irrigation.', 'varieties': 'Pusa Mukta, Golden Acre.', 'seed_selection_sowing': 'Transplanted at 4-6 weeks old.', 'nutrient_management': 'High NPK needs, especially N.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Fine, compact seedbed.', 'process_of_cultivation': 'Transplanting → Irrigation → Head formation → Harvesting.', 'organic_farming_practices': 'Use compost and companion planting (e.g., mint).', 'harvesting_storage': 'Harvest when heads are firm. Cold storage needed.', 'estimated_cost': 'Moderate.', 'locations_of_cultivation': 'UP, Odisha, West Bengal.', 'pests_affecting': 'Diamondback moth, aphids, black rot.', 'pest_control_measures': 'Chemical: Imidacloprid. Organic: Bt for caterpillars.'},
    'carrot-silage': {'title': 'Carrot Cultivation', 'identity_context': 'Daucus carota. Root vegetable, rich in Vitamin A.', 'soil_requirements': 'Deep, loose, sandy loamy soils, stone-free.', 'climate_requirements': 'Cool season crop. Ideal temperature: 15°C-20°C.', 'water_irrigation_needs': 'Requires uniform moisture; avoid water stress during root growth.', 'varieties': 'Pusa Kesar, Nantes.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'High Potassium needs.', 'season_of_cultivation': 'Rabi (Oct-Feb).', 'land_preparation': 'Deep ploughing to a depth of 30cm to allow straight root growth.', 'process_of_cultivation': 'Sowing → Thinning → Inter-culturing → Irrigation → Harvesting.', 'organic_farming_practices': 'Use compost, intercrop with onions.', 'harvesting_storage': 'Harvest when roots are fully developed. Store in cool, humid conditions.', 'estimated_cost': 'Low to moderate.', 'locations_of_cultivation': 'UP, Haryana, Punjab.', 'pests_affecting': 'Carrot weevil, leaf blight.', 'pest_control_measures': 'Chemical: Mancozeb. Organic: Crop rotation.'},
    'radish-silage': {'title': 'Radish Cultivation', 'identity_context': 'Raphanus sativus. Fast-growing root vegetable.', 'soil_requirements': 'Loose, sandy loam soils.', 'climate_requirements': 'Cool season crop, very quick maturity.', 'water_irrigation_needs': 'Requires constant moisture for tender roots.', 'varieties': 'Pusa Chetki (Tropical), Japanese White.', 'seed_selection_sowing': 'Sown directly in lines, thin later.', 'nutrient_management': 'Responds well to organic manure and balanced NPK.', 'season_of_cultivation': 'All year round (depending on variety).', 'land_preparation': 'Deep, fine tillage.', 'process_of_cultivation': 'Sowing → Thinning → Irrigation → Harvesting (25-45 days).', 'organic_farming_practices': 'Use compost and avoid chemical fertilizers.', 'harvesting_storage': 'Harvest when roots reach optimal size. Cannot be stored long.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, flea beetles.', 'pest_control_measures': 'Chemical: Malathion. Organic: Neem oil.'},
    'spinach-silage': {'title': 'Spinach Cultivation', 'identity_context': 'Spinacia oleracea. Leafy vegetable, rich in iron.', 'soil_requirements': 'Wide range, deep fertile loams preferred.', 'climate_requirements': 'Cool season crop, sensitive to hot weather (causes bolting).', 'water_irrigation_needs': 'High moisture requirement, frequent light irrigation.', 'varieties': 'Pusa Jyoti, All Green.', 'seed_selection_sowing': 'Sown directly.', 'nutrient_management': 'High Nitrogen need for leaf growth.', 'season_of_cultivation': 'Rabi (winter).', 'land_preparation': 'Fine tilth, rich in organic matter.', 'process_of_cultivation': 'Sowing → Irrigation → Fertilization → Harvesting (multiple cuts).', 'organic_farming_practices': 'Heavy organic manure application.', 'harvesting_storage': 'Harvested by cutting leaves; consume fresh.', 'estimated_cost': 'Low.', 'locations_of_cultivation': 'Grown across most states.', 'pests_affecting': 'Aphids, leaf miners.', 'pest_control_measures': 'Organic: Neem oil, water spray.'},
    }
    
    details = crop_data.get(crop_name)
    
    if details:
        required_fields = [
            'identity_context', 'soil_requirements', 'climate_requirements', 'water_irrigation_needs',
            'varieties', 'seed_selection_sowing', 'nutrient_management', 'season_of_cultivation',
            'land_preparation', 'process_of_cultivation', 'organic_farming_practices', 
            'harvesting_storage', 'estimated_cost', 'locations_of_cultivation', 
            'pests_affecting', 'pest_control_measures'
        ]
        
        # Check if this is the dedicated Pest Management API call
        if request.path.startswith('/api/get-pest-details/'):
            # The structure for the 5-point guide
            pest_details_5_point = {
                'title': details.get('title', crop_name.title() + ' Management'),
                'identification': details.get('pests_affecting', 'Data not available.') + ' Symptoms: ' + details.get('identity_context', 'Not specified.'),
                'mixtures': details.get('pest_control_measures', 'Data not available.'),
                'application_process': details.get('process_of_cultivation', 'Data not available.'), # Using Process of Cultivation as a general application guide
                'safety_precautions': details.get('harvesting_storage', 'Data not available.') + ' Always follow PHI and PPE rules.',
                'recommendations': details.get('organic_farming_practices', 'Data not available.')
            }
            return JsonResponse(pest_details_5_point)

        # Default 16-point return for /api/crop-details/
        for field in required_fields:
            if field not in details:
                details[field] = 'Data not available.' 
        
        if 'title' not in details:
             details['title'] = crop_name.title() + ' Details'
        return JsonResponse(details)
    
    else:
        # Final fallback for crops not defined in the dictionary at all
        return JsonResponse({'error': f'Crop details for "{crop_name}" not found in database.'}, status=404)

@csrf_exempt
def get_pest_management_details(request, crop_name):
    # This function is the API endpoint the JS is calling. It uses the main handler.
    return get_crop_details(request, crop_name)

@csrf_exempt
def scan_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        detected_disease = random.choice(['leaf_blight', 'powdery_mildew', 'bacterial_spot'])
        
        disease_database = {
            'leaf_blight': {'name': 'Leaf Blight', 'description': 'Fungal disease causing brown spots on leaves, leading to premature leaf death and reduced yield.', 'treatments': ['Remove affected leaves immediately', 'Improve air circulation around plants', 'Apply copper-based fungicide', 'Reduce overhead watering'], 'pesticides': [{'name': 'Mancozeb 75% WP', 'dosage': '2g per liter water', 'frequency': 'Every 10-15 days'}, {'name': 'Copper Oxychloride', 'dosage': '3g per liter water', 'frequency': 'Bi-weekly'}], 'prevention': ['Plant resistant varieties', 'Maintain proper plant spacing', 'Avoid overhead irrigation', 'Remove crop debris after harvest']},
            'powdery_mildew': {'name': 'Powdery Mildew', 'description': 'White powdery fungal growth on leaves and stems, reducing photosynthesis and plant vigor.', 'treatments': ['Spray with baking soda solution', 'Apply sulfur-based fungicide', 'Increase air circulation', 'Remove infected plant parts'], 'pesticides': [{'name': 'Sulfur 80% WP', 'dosage': '2.5g per liter water', 'frequency': 'Weekly during infection'}, {'name': 'Propiconazole', 'dosage': '1ml per liter water', 'frequency': 'Every 15 days'}], 'prevention': ['Avoid overcrowding plants', 'Water at soil level', 'Choose resistant varieties', 'Maintain proper humidity levels']},
            'bacterial_spot': {'name': 'Bacterial Spot', 'description': 'Bacterial infection causing dark spots with yellow halos on leaves and fruits.', 'treatments': ['Apply copper-based bactericide', 'Remove infected plant material', 'Improve drainage', 'Use drip irrigation'], 'pesticides': [{'name': 'Streptomycin', 'dosage': '0.5g per liter water', 'frequency': 'Every 7-10 days'}, {'name': 'Copper Hydroxide', 'dosage': '2g per liter water', 'frequency': 'Bi-weekly'}], 'prevention': ['Use certified disease-free seeds', 'Avoid working with wet plants', 'Rotate crops annually', 'Disinfect tools regularly']}
        }
        
        confidence = 85 + random.randint(0, 10)
        response_data = {
            'success': True,
            'disease_type': disease_database[detected_disease]['name'],
            'description': disease_database[detected_disease]['description'],
            'confidence': f"{confidence}%",
            'treatments': disease_database[detected_disease]['treatments'],
            'pesticide_recommendations': disease_database[detected_disease]['pesticides'],
            'prevention_tips': disease_database[detected_disease]['prevention'],
        }
        return JsonResponse(response_data)

    return JsonResponse({'error': 'Invalid request or no image uploaded'}, status=400)

@csrf_exempt
def register_farmer(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phoneNumber')
        email_id = request.POST.get('emailId')
        
        print(f"New registration: Phone={phone_number}, Email={email_id}")
        
        return JsonResponse({'success': True, 'message': 'Registration successful!'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def check_dbt_status(request):
    if request.method == 'POST':
        aadhaar = request.POST.get('dbtAadhaar')
        account = request.POST.get('bankAccount')
        
        is_linked = random.random() > 0.3
        
        if is_linked:
            message = f'✅ Your Aadhaar {aadhaar} is successfully linked to DBT scheme with account {account}. You are eligible for direct benefit transfers.'
            return JsonResponse({'success': True, 'message': message})
        else:
            message = f'❌ Your Aadhaar {aadhaar} is not linked to DBT scheme. Please visit your nearest bank branch to link your Aadhaar with bank account.'
            return JsonResponse({'success': False, 'message': message})
            
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def connect_company(request):
    if request.method == 'POST':
        return JsonResponse({'success': True, 'message': 'Thank you for your interest! Our partner companies will contact you shortly.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)