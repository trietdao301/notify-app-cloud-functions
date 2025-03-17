# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`
from firebase_admin import initialize_app

from sendNotificationToTopic.function import sendNotificationToTopic
from subscription_web import subscribeToTopic, unsubscribeFromTopic  
initialize_app()




