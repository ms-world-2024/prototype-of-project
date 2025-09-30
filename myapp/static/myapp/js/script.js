// script.js

const dashboardOverlay = document.getElementById('dashboardOverlay');
const menuBtn = document.getElementById('menuBtn');
const closeDashboard = document.getElementById('closeDashboard');

/**
 * Maps the old page IDs from your HTML to the new Django URLs.
 */
const pageRoutes = {
    'homePage': '/home/',
    'cropsPage': '/crops/',
    'marketPage': '/market/',
    'scannerPage': '/scanner/',
    'dbtPage': '/dbt/',
    'pestPage': '/pest/',
    'organicMainPage': '/organic/',
    'videosPage': '/videos/',
    'agriNewsPage': '/agri-news/',
    'ctocPage': '/connect-companies/',
    'jobsPage': '/jobs/',
    'benefitsPage': '/benefits/',
    'organicPestPage': '/organic-pest/',
    'registrationPage': '/signup/',
    'reviewPage': '/review/',        
    'reviewsListPage': '/reviews/all/', 
};

/**
 * Redirects the browser to the URL associated with the specified page ID.
 */
function showPage(pageId) {
    const url = pageRoutes[pageId];
    if (url) {
        window.location.href = url;
    } else {
        console.error(`No URL found for page ID: ${pageId}`);
    }
}

// --- Menu and Dashboard Handlers (Standard Logic) ---

menuBtn.addEventListener('click', () => {
    dashboardOverlay.classList.toggle('hidden');
    menuBtn.classList.toggle('hamburger-active');
});

if (closeDashboard) {
    closeDashboard.addEventListener('click', () => {
        dashboardOverlay.classList.add('hidden');
        menuBtn.classList.remove('hamburger-active');
    });
}

document.querySelectorAll('.dashboard-card').forEach(card => {
    card.addEventListener('click', () => {
        const pageId = card.getAttribute('data-page');
        if (pageId) {
            showPage(pageId);
        }
    });
});

const organicDashboardBtn = document.getElementById('organicDashboardBtn');
if (organicDashboardBtn) {
    organicDashboardBtn.addEventListener('click', () => {
        showPage('organicMainPage');
    });
}

if (dashboardOverlay) {
    dashboardOverlay.addEventListener('click', (e) => {
        if (e.target === dashboardOverlay) {
            dashboardOverlay.classList.add('hidden');
            menuBtn.classList.remove('hamburger-active');
        }
    });
}


// --- Voice Functions (Standard Logic) ---

let isVoiceEnabled = false;
let selectedLanguage = 'en-US';

const languageSelect = document.getElementById('languageSelect');
if (languageSelect) {
    languageSelect.addEventListener('change', (e) => {
        selectedLanguage = e.target.value;
        if (isVoiceEnabled) {
            const langNames = {
                'en-US': 'English', 'hi-IN': 'Hindi', 'te-IN': 'Telugu'
            };
            speakText(`Language changed to ${langNames[selectedLanguage]}`);
        }
    });
}

const voiceBtn = document.getElementById('voiceBtn');
if (voiceBtn) {
    voiceBtn.addEventListener('click', () => {
        isVoiceEnabled = !isVoiceEnabled;
        const btn = document.getElementById('voiceBtn');
        if (isVoiceEnabled) {
            btn.textContent = '🔇 Voice Off';
            btn.classList.remove('voice-pulse');
            speakText('Voice reading enabled. Double click on any text to hear it read aloud.');
        } else {
            btn.textContent = '🔊 Voice';
            btn.classList.add('voice-pulse');
            speakText('Voice reading disabled.');
        }
    });
}

document.addEventListener('dblclick', (event) => {
    if (isVoiceEnabled) {
        const selectedText = window.getSelection().toString();
        if (selectedText) {
            speakText(selectedText);
        }
    }
});

function speakText(text) {
    if ('speechSynthesis' in window && text) {
        speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.8;
        utterance.pitch = 1;
        utterance.lang = selectedLanguage;
        const voices = speechSynthesis.getVoices();
        const voice = voices.find(v => v.lang.startsWith(selectedLanguage.split('-')[0]));
        if (voice) {
            utterance.voice = voice;
        }
        speechSynthesis.speak(utterance);
    }
}

if ('speechSynthesis' in window) {
    speechSynthesis.onvoiceschanged = () => {};
}


// --- Data Fetching and Display Logic (APIs) ---

async function updateWeather() {
    const todayWeather = document.getElementById('todayWeather');
    if (!todayWeather) return;
    try {
        const response = await fetch('/api/weather/?lat=28.7041&lon=77.1025');
        const data = await response.json();

        if (data.error) {
            console.error(data.error);
            return;
        }

        document.getElementById('temperature').textContent = data.current.temp + '°C';
        document.getElementById('condition').textContent = data.current.condition;
        document.getElementById('humidity').textContent = data.current.humidity + '%';
        document.getElementById('windSpeed').textContent = data.current.wind_speed + ' km/h';
        document.getElementById('rainfall').textContent = data.current.rainfall + 'mm';
        document.getElementById('uvIndex').textContent = data.current.uv_index;
        
        const forecastContainer = document.getElementById('weatherForecast');
        if (forecastContainer) {
            forecastContainer.innerHTML = data.forecast.map(day => `
                <div class="bg-white bg-opacity-20 p-2 rounded-lg text-center">
                    <div class="text-xs font-semibold">${day.day}</div>
                    <div class="text-lg">${day.icon}</div>
                    <div class="text-xs">${day.high}°/${day.low}°</div>
                    <div class="text-xs opacity-75">${day.rain}%</div>
                </div>
            `).join('');
        }

        const now = new Date();
        const timeString = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
        document.getElementById('lastUpdated').textContent = `Last updated: ${timeString}`;

    } catch (error) {
        console.error('Weather API error:', error);
    }
}

const toggleForecast = document.getElementById('toggleForecast');
if (toggleForecast) {
    toggleForecast.addEventListener('click', () => {
        const todayWeather = document.getElementById('todayWeather');
        const forecastView = document.getElementById('forecastView');
        if (forecastView.classList.contains('hidden')) {
            forecastView.classList.remove('hidden');
            todayWeather.classList.add('hidden');
            toggleForecast.textContent = 'Today View';
        } else {
            forecastView.classList.add('hidden');
            todayWeather.classList.remove('hidden');
            toggleForecast.textContent = '10-Day View';
        }
    });
}

async function updateMarketPrices() {
    const cerealPrices = document.getElementById('cerealPrices');
    if (!cerealPrices) return;
    try {
        const response = await fetch('/api/market-prices/');
        const marketData = await response.json();

        updatePriceSection('cerealPrices', marketData.cereals);
        updatePriceSection('vegetablePrices', marketData.vegetables);
        updatePriceSection('pulsesPrices', marketData.pulses);

        const allCrops = [...marketData.cereals, ...marketData.vegetables, ...marketData.pulses];
        const topDemand = allCrops.sort((a, b) => b.change - a.change).slice(0, 5);

        const topDemandContainer = document.getElementById('topDemandCrops');
        if (topDemandContainer) {
            topDemandContainer.innerHTML = topDemand.map(crop => `
                <div class="bg-white bg-opacity-20 p-3 rounded-lg text-center">
                    <div class="text-lg font-bold">${crop.name}</div>
                    <div class="text-sm">₹${crop.price}${crop.unit ? '/' + crop.unit : '/quintal'}</div>
                    <div class="text-xs ${crop.change > 0 ? 'text-green-200' : 'text-red-200'}">
                        ${crop.change > 0 ? '↗' : '↘'} ${Math.abs(crop.change)}%
                    </div>
                </div>
            `).join('');
        }
        
        const analysisContainer = document.getElementById('marketAnalysis');
        if (analysisContainer) {
            analysisContainer.innerHTML = `
                <div class="text-center p-4 bg-green-50 rounded-lg">
                    <div class="text-2xl font-bold text-green-600">📈 Rising</div>
                    <p class="text-sm text-gray-600">Pulses & Organic Vegetables</p>
                </div>
                <div class="text-center p-4 bg-yellow-50 rounded-lg">
                    <div class="text-2xl font-bold text-yellow-600">→ Stable</div>
                    <p class="text-sm text-gray-600">Wheat & Rice Prices</p>
                </div>
                <div class="text-center p-4 bg-blue-50 rounded-lg">
                    <div class="text-2xl font-bold text-blue-600">🎯 Opportunity</div>
                    <p class="text-sm text-gray-600">Export Quality Basmati</p>
                </div>
            `;
        }

        const priceUpdateTime = document.getElementById('priceUpdateTime');
        if (priceUpdateTime) {
            priceUpdateTime.textContent = new Date().toLocaleString('en-IN');
        }

    } catch (error) {
        console.error('Market API error:', error);
    }
}

function updatePriceSection(containerId, crops) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = crops.map(crop => `
        <div class="flex justify-between items-center border-b pb-2">
            <span class="font-medium">${crop.name}</span>
            <div class="text-right">
                <div class="font-semibold">₹${crop.price}${crop.unit ? '/' + crop.unit : '/quintal'}</div>
                <div class="text-xs ${crop.change > 0 ? 'text-green-600' : 'text-red-600'}">
                    ${crop.change > 0 ? '↗' : '↘'} ${Math.abs(crop.change)}%
                </div>
            </div>
        </div>
    `).join('');
}

const refreshPrices = document.getElementById('refreshPrices');
if (refreshPrices) {
    refreshPrices.addEventListener('click', () => {
        updateMarketPrices();
        if (isVoiceEnabled) {
            speakText('Market prices updated successfully');
        }
    });
}


// --- Crops, Scanner, and Form Submission Logic (APIs) ---

document.querySelectorAll('.crop-card').forEach(card => {
    card.addEventListener('click', async () => {
        const cropName = card.getAttribute('data-crop');
        const isPestPage = window.location.pathname.includes('/pest/');
        
        // Determine which API to call based on the page URL
        // Pest Page calls the dedicated 5-point handler; Crops Page calls the 16-point handler
        const apiUrl = isPestPage 
            ? `/api/get-pest-details/${cropName}/` 
            : `/api/crop-details/${cropName}/`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                const errorData = await response.json();
                alert(`Error fetching details: ${errorData.error || 'Check server logs.'}`);
                return;
            }
            const data = await response.json();
            
            const listSection = document.getElementById('cropListSection');
            const detailsSection = document.getElementById('cropDetails') || document.getElementById('pestDetailsDisplay');

            if (data && listSection && detailsSection) {
                
                // Set the main title element (which exists on both pages)
                const titleElement = detailsSection.querySelector('#cropTitle') || detailsSection.querySelector('#pestTitle');
                if (titleElement) titleElement.textContent = data.title;
                
                // --- MAPPING LOGIC ---
                if (isPestPage) {
                    // 5-POINT PEST MANAGEMENT MAPPING (Pest Page)
                    document.getElementById('identification').textContent = data.identification;
                    document.getElementById('mixtures').textContent = data.mixtures;
                    document.getElementById('application_process').textContent = data.application_process;
                    document.getElementById('safety_precautions').textContent = data.safety_precautions;
                    document.getElementById('recommendations').textContent = data.recommendations;
                } else {
                    // 16-POINT CULTIVATION MAPPING (Crops Page)
                    document.getElementById('identity_context').textContent = data.identity_context;
                    document.getElementById('soil_requirements').textContent = data.soil_requirements;
                    document.getElementById('climate_requirements').textContent = data.climate_requirements;
                    document.getElementById('water_irrigation_needs').textContent = data.water_irrigation_needs;
                    document.getElementById('varieties').textContent = data.varieties;
                    document.getElementById('seed_selection_sowing').textContent = data.seed_selection_sowing;
                    document.getElementById('nutrient_management').textContent = data.nutrient_management;
                    document.getElementById('season_of_cultivation').textContent = data.season_of_cultivation;
                    document.getElementById('land_preparation').textContent = data.land_preparation;
                    document.getElementById('process_of_cultivation').textContent = data.process_of_cultivation;
                    document.getElementById('organic_farming_practices').textContent = data.organic_farming_practices;
                    document.getElementById('harvesting_storage').textContent = data.harvesting_storage;
                    document.getElementById('estimated_cost').textContent = data.estimated_cost;
                    document.getElementById('locations_of_cultivation').textContent = data.locations_of_cultivation;
                    document.getElementById('pests_affecting').textContent = data.pests_affecting;
                    document.getElementById('pest_control_measures').textContent = data.pest_control_measures;
                }

                // 3. Toggle visibility
                listSection.classList.add('hidden');
                detailsSection.classList.remove('hidden');

                if (isVoiceEnabled) {
                    speakText(`Showing information for ${data.title}. ${data.identification ? data.identification.substring(0, 50) : data.identity_context.substring(0, 50)}...`);
                }
            } else {
                alert(`Detailed information for ${cropName} is unavailable. Please check the Django server log for errors.`);
            }
        } catch (error) {
            console.error('Fetch error:', error);
            alert(`An error occurred while loading details for ${cropName}.`);
        }
    });
});

const backToCrops = document.getElementById('backToCrops');
if (backToCrops) {
    backToCrops.addEventListener('click', () => {
        const cropListSection = document.getElementById('cropListSection');
        const cropDetails = document.getElementById('cropDetails');
        if (cropListSection && cropDetails) {
            cropListSection.classList.remove('hidden');
            cropDetails.classList.add('hidden');
        } else {
            showPage('cropsPage');
        }
    });
}

// Back button logic for the PEST page
const backToPestList = document.getElementById('backToPestList');
if (backToPestList) {
    backToPestList.addEventListener('click', () => {
        // Find the list section using its ID (which is 'cropListSection' on the pest page)
        const pestListSection = document.getElementById('cropListSection'); 
        const pestDetailsDisplay = document.getElementById('pestDetailsDisplay');
        if (pestListSection && pestDetailsDisplay) {
            pestListSection.classList.remove('hidden');
            pestDetailsDisplay.classList.add('hidden');
        } else {
            showPage('pestPage');
        }
    });
}

const startScan = document.getElementById('startScan');
const imageUpload = document.getElementById('imageUpload');
if (startScan && imageUpload) {
    startScan.addEventListener('click', async () => {
        if (!imageUpload.files[0]) {
            alert('Please upload an image first.');
            return;
        }

        const formData = new FormData();
        formData.append('image', imageUpload.files[0]);

        const scanLine = document.getElementById('scanLine');
        const scanResult = document.getElementById('scanResult');
        if (scanLine) scanLine.classList.remove('hidden');

        try {
            const response = await fetch('/api/scan-image/', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();

            if (scanLine) scanLine.classList.add('hidden');
            if (data.success) {
                document.getElementById('diseaseType').textContent = data.disease_type;
                document.getElementById('diseaseDescription').textContent = data.description;
                document.getElementById('confidence').textContent = data.confidence;
                
                const treatmentList = document.getElementById('treatmentList');
                treatmentList.innerHTML = data.treatments.map(treatment =>
                    `<div class="bg-blue-50 p-2 rounded text-sm">• ${treatment}</div>`
                ).join('');
                
                const pesticideContainer = document.getElementById('pesticideRecommendations');
                pesticideContainer.innerHTML = data.pesticide_recommendations.map(pesticide => `
                    <div class="bg-purple-50 p-3 rounded-lg">
                        <h5 class="font-semibold text-purple-800">${pesticide.name}</h5>
                        <p class="text-sm text-gray-700">Dosage: ${pesticide.dosage}</p>
                        <p class="text-sm text-gray-700">Frequency: ${pesticide.frequency}</p>
                    </div>
                `).join('');

                const preventionList = document.getElementById('preventionTips');
                preventionList.innerHTML = data.prevention_tips.map(tip =>
                    `<li>• ${tip}</li>`
                ).join('');

                if (scanResult) scanResult.classList.remove('hidden');
                if (isVoiceEnabled) {
                    speakText(`Disease detected: ${data.disease_type} with ${data.confidence} confidence. Check the detailed treatment recommendations.`);
                }
            } else {
                alert(data.error);
            }
        } catch (error) {
            console.error('Scan API error:', error);
            if (scanLine) scanLine.classList.add('hidden');
            alert('An error occurred during scanning. Please try again.');
        }
    });
}
const captureImage = document.getElementById('captureImage');
if (captureImage) {
    captureImage.addEventListener('click', () => {
        alert('Camera functionality would be implemented here. For demo, please use the upload button.');
    });
}
const readScanResult = document.getElementById('readScanResult');
if (readScanResult) {
    readScanResult.addEventListener('click', () => {
        const diseaseType = document.getElementById('diseaseType').textContent;
        const description = document.getElementById('diseaseDescription').textContent;
        const confidence = document.getElementById('confidence').textContent;
        const fullText = `Detected disease: ${diseaseType}. ${description}. Detection confidence: ${confidence}. Please check the detailed treatment recommendations for detailed guidance.`;
        speakText(fullText);
    });
}
const saveResults = document.getElementById('saveResults');
if (saveResults) {
    saveResults.addEventListener('click', () => {
        alert('Disease detection report saved to your device. You can access it from the reports section.');
    });
}
const shareResults = document.getElementById('shareResults');
if (shareResults) {
    shareResults.addEventListener('click', () => {
        if (navigator.share) {
            navigator.share({
                title: 'Crop Disease Detection Report',
                text: `Disease detected: ${document.getElementById('diseaseType').textContent}`,
                url: window.location.href
            });
        } else {
            alert('Report sharing functionality - would integrate with WhatsApp, email, etc.');
        }
    });
}

const registrationForm = document.getElementById('registrationForm');
if (registrationForm) {
    registrationForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const phone = document.getElementById('phoneNumber').value;
        const email = document.getElementById('emailId').value;
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        try {
            const response = await fetch('/api/register-farmer/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ phoneNumber: phone, emailId: email }).toString(),
            });
            const data = await response.json();

            if (data.success) {
                alert(data.message);
                window.location.href = '/home/';
            } else {
                alert(data.message);
            }
        } catch (error) {
            alert('Registration failed. Please try again.');
        }
    });
}

const dbtForm = document.getElementById('dbtForm');
if (dbtForm) {
    dbtForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const aadhaar = document.getElementById('dbtAadhaar').value;
        const account = document.getElementById('bankAccount').value;
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        const result = document.getElementById('dbtResult');
        const resultText = document.getElementById('dbtResultText');

        try {
            const response = await fetch('/api/check-dbt/', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: new URLSearchParams({ dbtAadhaar: aadhaar, bankAccount: account }).toString(),
            });
            const data = await response.json();

            if (data.success) {
                result.className = 'mt-6 p-4 rounded-lg bg-green-50';
            } else {
                result.className = 'mt-6 p-4 rounded-lg bg-red-50';
            }
            resultText.textContent = data.message;
            result.classList.remove('hidden');

            if (isVoiceEnabled) {
                speakText(data.message);
            }
        } catch (error) {
            console.error('API Error:', error);
            alert('Could not connect to DBT service. Please try again.');
        }
    });
}

const companyConnectForm = document.getElementById('companyConnectForm');
if (companyConnectForm) {
    companyConnectForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const formData = new FormData(e.target);
        const body = new URLSearchParams(formData).toString();

        try {
            const response = await fetch('/api/connect-company/', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: body,
            });
            const data = await response.json();
            alert(data.message);
        } catch (error) {
            alert('Failed to connect. Please check your internet and try again.');
        }
    });
}

const reviewForm = document.querySelector('form[action$="/review/"]');
if (reviewForm) {
    reviewForm.addEventListener('submit', async (e) => {
        const rating = document.querySelector('input[name="rating"]:checked');
        
        if (!rating) {
            e.preventDefault(); 
            alert('Please select a rating before submitting.');
            return;
        }
    });
}


// --- Chatbot Logic ---

const chatToggle = document.getElementById('chatToggle');
const chatWindow = document.getElementById('chatWindow');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');
const voiceInput = document.getElementById('voiceInput');
const quickHelp = document.getElementById('quickHelp');
const closeChatbot = document.getElementById('closeChatbot');

if (chatToggle && chatWindow) {
    chatToggle.addEventListener('click', () => {
        chatWindow.classList.toggle('hidden');
    });

    closeChatbot.addEventListener('click', () => {
        chatWindow.classList.add('hidden');
    });
}

function addMessage(message, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = isUser ? 'bg-green-100 p-2 rounded-lg ml-8' : 'bg-gray-100 p-2 rounded-lg mr-8';
    messageDiv.innerHTML = `<p class="text-sm">${message}</p>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function getBotResponse(message) {
    const lowerMessage = message.toLowerCase();
    if (lowerMessage.includes('wheat')) {
        return `🌾 **Wheat Cultivation Guide:**
        • **Sowing:** November (1st-3rd week) in Punjab
        • **Varieties:** PBW 725, HD 3086, WH 1105 (rust-resistant)
        • **Soil:** Loamy to clay-loam, pH 6.0-7.5
        • **Water:** 450-600mm during crop cycle
        • **Yield:** 40-50 quintals/ha (average), 60-65 quintals/ha (advanced)
        • **Cost per acre:** ₹25,000-30,000 including all inputs`;
    }
    return `Hello! I can help with a variety of farming topics.`;
}

if (chatSend && chatInput) {
    chatSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

function sendMessage() {
    const message = chatInput.value.trim();
    if (message) {
        addMessage(message, true);
        chatInput.value = '';

        setTimeout(() => {
            const response = getBotResponse(message);
            addMessage(response);
            if (isVoiceEnabled) {
                speakText(response);
            }
        }, 1000);
    }
}

if (voiceInput) {
    voiceInput.addEventListener('click', () => {
        if ('webkitSpeechRecognition' in window) {
            const recognition = new webkitSpeechRecognition();
            recognition.lang = 'en-IN';
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                chatInput.value = transcript;
                sendMessage();
            };
            recognition.start();
            voiceInput.textContent = '🎤 Listening...';
            setTimeout(() => {
                voiceInput.textContent = '🎤 Voice Input';
            }, 3000);
        } else {
            alert('Voice input not supported in this browser');
        }
    });
}

if (quickHelp) {
    quickHelp.addEventListener('click', () => {
        const quickQuestions = [
            'What is the cost estimation for wheat per acre?',
            'How to control pests in rice crop?',
            'What are the best organic farming practices?',
            'Current market prices for vegetables',
            'Soil management tips for better yield'
        ];

        const chatMessages = document.getElementById('chatMessages');
        const helpDiv = document.createElement('div');
        helpDiv.className = 'bg-gradient-to-r from-blue-100 to-purple-100 p-3 rounded-lg border border-blue-200';
        helpDiv.innerHTML = `
            <p class="text-sm font-medium mb-2">💡 Quick Questions:</p>
            ${quickQuestions.map(q => `
                <button class="block w-full text-left text-xs bg-white p-2 mb-1 rounded hover:bg-blue-50 transition-colors" onclick="document.getElementById('chatInput').value='${q}'; sendMessage();">
                    ${q}
                </button>
            `).join('')}
        `;
        chatMessages.appendChild(helpDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

// Initializers
setInterval(updateWeather, 300000);
setInterval(updateMarketPrices, 600000);


// --- Organic Menu Logic ---

const organicMenuToggle = document.getElementById('organicMenuToggle');
const organicMenuOptions = document.getElementById('organicMenuOptions');

if (organicMenuToggle && organicMenuOptions) {
    organicMenuToggle.addEventListener('click', () => {
        organicMenuOptions.classList.toggle('hidden');
    });

    document.addEventListener('click', (e) => {
        if (!organicMenuToggle.contains(e.target) && !organicMenuOptions.contains(e.target)) {
            organicMenuOptions.classList.add('hidden');
        }
    });
}