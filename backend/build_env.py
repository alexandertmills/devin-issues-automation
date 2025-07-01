import os

neon_user = os.getenv("NEON_CREDENTIALS_user")
neon_password = os.getenv("NEON_CREDENTIALS_password")
app_id = os.getenv("app_id")
client_id = os.getenv("client_id")
client_sec = os.getenv("client_sec")

neon_url = f"postgresql://{neon_user}:{neon_password}@ep-sweet-breeze-a84hge8c-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"

print("Environment variables to set:")
print(f"NEON_DATABASE_URL={neon_url}")
print(f"GITHUB_APP_ID={app_id}")
print(f"GITHUB_APP_PRIVATE_KEY={client_sec}")
print(f"GITHUB_CLIENT_ID={client_id}")

if all([neon_user, neon_password, app_id, client_id, client_sec]):
    print("\n✅ All required secrets are available")
else:
    print("\n❌ Some secrets are missing:")
    print(f"  NEON_CREDENTIALS_user: {'✅' if neon_user else '❌'}")
    print(f"  NEON_CREDENTIALS_password: {'✅' if neon_password else '❌'}")
    print(f"  app_id: {'✅' if app_id else '❌'}")
    print(f"  client_id: {'✅' if client_id else '❌'}")
    print(f"  client_sec: {'✅' if client_sec else '❌'}")
