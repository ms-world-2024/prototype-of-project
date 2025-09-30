from django.urls import path
from myapp import views

urlpatterns = [
    # AUTHENTICATION
    path('', views.login_view, name='login'),
    path('signup/', views.signup_view, name="signup"),
    path('logout/', views.logout_view, name="logout"),
    
    # MAIN PAGES
    path('home/', views.home_view, name='home'),
    path('crops/', views.crops_view, name='crops'),
    path('market/', views.market_view, name='market'),
    path('scanner/', views.scanner_view, name='scanner'),
    path('dbt/', views.dbt_view, name='dbt'),
    path('pest/', views.pest_view, name='pest'), # Dynamic Pest Management Page
    
    # ORGANIC HUB PAGES
    path('organic/', views.organic_main_view, name='organic_main'),
    path('videos/', views.videos_view, name='videos'),
    path('agri-news/', views.agri_news_view, name='agri_news'),
    path('connect-companies/', views.ctoc_view, name='connect_companies'),
    path('jobs/', views.jobs_view, name='jobs'),
    path('benefits/', views.benefits_view, name='benefits'),
    path('organic-pest/', views.organic_pest_view, name='organic_pest'),
    path('about-organic/', views.about_organic_view, name='about_organic'),
    
    # REVIEW PAGES
    path('review/', views.submit_review, name='submit_review'),
    path('reviews/all/', views.view_reviews, name='view_reviews'),


    # API ENDPOINTS (Critical for dynamic data)
    path('api/weather/', views.get_weather, name='get_weather'),
    path('api/market-prices/', views.get_market_prices, name='get_market_prices'),
    
    # 16-POINT CROP DETAILS (Used by /crops/)
    path('api/crop-details/<str:crop_name>/', views.get_crop_details, name='get_crop_details'),
    
    # 5-POINT PEST MANAGEMENT DETAILS (Used by /pest/)
    path('api/get-pest-details/<str:crop_name>/', views.get_pest_management_details, name='get_pest_management_details'),
    
    path('api/scan-image/', views.scan_image, name='scan_image'),
    path('api/register-farmer/', views.register_farmer, name='register_farmer'),
    path('api/check-dbt/', views.check_dbt_status, name='check_dbt_status'),
    path('api/connect-company/', views.connect_company, name='connect_company'),
]