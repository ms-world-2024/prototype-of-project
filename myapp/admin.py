from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    # Correctly uses 'submission_date'
    list_display = ('user', 'rating', 'review_text', 'submission_date') 
    list_filter = ('rating', 'submission_date') 
    search_fields = ['user__username', 'review_text']