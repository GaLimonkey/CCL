import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    UPLOAD_FOLDER = 'app/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}