# Zalongwa Hikvision Registration

A mobile-friendly employee self-registration application for a compatible Hikvision face-and-fingerprint access-control terminal.

## What employees can enter

- Employee ID
- First, middle and last name
- Gender
- Effective start and end dates
- Access-plan template
- Face photograph
- Fingerprint captured using the physical terminal

## Security

- A private enrollment PIN is required.
- Sessions expire after 10 minutes.
- Employees must confirm that the supplied information belongs to them.
- Device credentials are loaded through Streamlit secrets.
- Face photographs and fingerprint templates are not permanently stored by the app.
- Registration should be supervised by an authorized Zalongwa administrator.

## Run locally

```cmd
git clone https://github.com/Heed725/Zalongwa-Hikvision-Registration.git
cd Zalongwa-Hikvision-Registration
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
notepad .streamlit\secrets.toml
streamlit run app.py
```

## Streamlit Community Cloud deployment

1. Deploy `app.py` from the `main` branch.
2. Open **Advanced settings → Secrets**.
3. Paste the following configuration and replace every placeholder:

```toml
HIKVISION_URL = "http://DEVICE_IP:HTTP_PORT"
HIKVISION_USERNAME = "admin"
HIKVISION_PASSWORD = "YOUR_DEVICE_PASSWORD"
HIKVISION_TIMEOUT = "45"
HIKVISION_VERIFY_TLS = "false"
ENROLLMENT_PIN = "YOUR_PRIVATE_ENROLLMENT_PIN"
```

4. Save the secrets and reboot the application.

Never commit `.streamlit/secrets.toml`. Keep only the example file in GitHub.

## Hosting limitation

The Streamlit server must be able to reach the Hikvision terminal. Prefer a VPN or private route. Exposing a biometric device directly to the public internet creates a serious security risk.
