from django.db import models
from django.contrib.auth.models import User

class Review(models.Model):
    # Link the review to the currently logged-in user
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Store the rating (1 to 5)
    rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        default=5
    )
    
    # Store the user's comments/feedback
    review_text = models.TextField(max_length=500, blank=True)
    
    # Record when the review was submitted
    submission_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} - Rating: {self.rating}"

    class Meta:
        # Prevents a user from submitting more than one review
        unique_together = ('user',)
        ordering = ['-submission_date']