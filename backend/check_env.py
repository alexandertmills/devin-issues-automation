import os

print('Environment variables check:')
print(f'GITHUB_APP_KEY present: {bool(os.getenv("GITHUB_APP_KEY"))}')
print(f'DEVIN_SERVICE_API_KEY present: {bool(os.getenv("DEVIN_SERVICE_API_KEY"))}')
print(f'NEON_CREDENTIALS_user present: {bool(os.getenv("NEON_CREDENTIALS_user"))}')
print(f'NEON_CREDENTIALS_password present: {bool(os.getenv("NEON_CREDENTIALS_password"))}')

user = os.getenv("NEON_CREDENTIALS_user")
password = os.getenv("NEON_CREDENTIALS_password")
if user and password:
    print(f'Can construct NEON_DATABASE_URL: True')
else:
    print(f'Can construct NEON_DATABASE_URL: False')
