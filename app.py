from __future__ import annotations

import hashlib
import os
import time
from datetime import date
from html import escape

import streamlit as st

from hikvision import HikvisionClient, HikvisionError, response_message


st.set_page_config(
    page_title="Zalongwa Hikvision Registration",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      :root {--za-green:#3C6731;--za-gold:#D5B641;--za-ink:#243127;}
      .stApp {background:linear-gradient(180deg,#f3f7f2 0,#fff 55%);}
      .block-container {max-width:760px;padding:1rem 1rem 5rem;}
      h1 {color:var(--za-green);font-size:1.7rem!important;margin-bottom:.15rem;}
      h2,h3 {color:var(--za-ink);}
      div[data-testid="stForm"] {background:#fff;border:1px solid #d9e4d6;border-top:5px solid var(--za-gold);
        border-radius:18px;padding:1rem;box-shadow:0 10px 26px rgba(45,82,47,.07);}
      .profile {background:#eef5eb;border:1px solid #c8dcc3;border-radius:15px;padding:14px 16px;margin:.5rem 0 1rem;}
      .profile strong {font-size:1.1rem;color:var(--za-green);}
      .profile small {display:block;color:#58705a;margin-top:4px;}
      .step {display:inline-flex;align-items:center;justify-content:center;width:29px;height:29px;border-radius:50%;
        background:var(--za-green);color:#fff;font-weight:750;margin-right:7px;border:3px solid #e3d58c;}
      .stButton>button,.stFormSubmitButton>button {min-height:48px;border-radius:12px;font-weight:700;}
      @media(max-width:600px){.block-container{padding:.7rem .7rem 4rem}h1{font-size:1.4rem!important}
        div[data-testid="stForm"]{padding:.75rem;border-radius:14px}}
    </style>
    """,
    unsafe_allow_html=True,
)


def setting(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, os.getenv(name, default)))
    except Exception:
        return os.getenv(name, default)


def safe_equal(left: str, right: str) -> bool:
    if not left or not right:
        return False
    return hashlib.sha256(left.encode()).digest() == hashlib.sha256(right.encode()).digest()


def api_client() -> HikvisionClient:
    return HikvisionClient(
        setting("HIKVISION_URL"),
        setting("HIKVISION_USERNAME", "admin"),
        setting("HIKVISION_PASSWORD"),
        int(setting("HIKVISION_TIMEOUT", "45")),
        setting("HIKVISION_VERIFY_TLS", "false").lower() == "true",
    )


def reset_registration() -> None:
    for key in ("employee", "verified_at", "face_done", "fingerprint_done"):
        st.session_state.pop(key, None)


def active_employee() -> dict | None:
    employee = st.session_state.get("employee")
    if not employee or time.time() - st.session_state.get("verified_at", 0) > 600:
        reset_registration()
        return None
    return employee


st.title("Zalongwa Hikvision Registration")
st.caption("Enter your information, then register your face or fingerprint")

required = (setting("HIKVISION_URL"), setting("HIKVISION_PASSWORD"), setting("ENROLLMENT_PIN"))
if not all(required):
    st.error("The administrator must configure the device URL, password and enrollment PIN in Streamlit Cloud secrets.")
    st.stop()

employee = active_employee()

if employee is None:
    st.markdown('<h3><span class="step">1</span>Enter employee information</h3>', unsafe_allow_html=True)
    with st.form("employee_form"):
        employee_no = st.text_input("Employee ID *", max_chars=32, placeholder="Example: 1001")
        first_name = st.text_input("First name *", max_chars=40)
        middle_name = st.text_input("Middle name", max_chars=40)
        last_name = st.text_input("Last name *", max_chars=60)
        gender = st.selectbox("Gender", ["unspecified", "male", "female"])
        d1, d2 = st.columns(2)
        valid_from = d1.date_input("Effective from", value=date.today())
        valid_until = d2.date_input("Effective until", value=date(2036, 12, 31))
        access_plan = st.number_input("Access plan template", min_value=1, max_value=255, value=1)
        pin = st.text_input("Enrollment PIN *", type="password")
        confirm = st.checkbox("I confirm the information belongs to me and is correct.")
        submitted = st.form_submit_button("Save and continue", type="primary", use_container_width=True)

    if submitted:
        names = [first_name.strip(), last_name.strip()]
        if not employee_no.strip() or not all(names):
            st.error("Employee ID, first name and last name are required.")
        elif not employee_no.strip().isalnum():
            st.error("Employee ID may contain letters and numbers only.")
        elif valid_until < valid_from:
            st.error("The end date cannot be earlier than the start date.")
        elif not confirm:
            st.error("Confirm that the information is yours and is correct.")
        elif not safe_equal(pin, setting("ENROLLMENT_PIN")):
            st.error("Incorrect enrollment PIN.")
        else:
            full_name = " ".join(filter(None, [first_name.strip(), middle_name.strip(), last_name.strip()]))
            record = {
                "employee_no": employee_no.strip(),
                "name": full_name,
                "gender": gender,
                "valid_from": valid_from.isoformat(),
                "valid_until": valid_until.isoformat(),
                "access_plan": int(access_plan),
            }
            try:
                client = api_client()
                with st.spinner("Saving employee information to the Hikvision device…"):
                    result, action = client.upsert_user(record)
                if result.ok:
                    st.session_state.employee = record
                    st.session_state.verified_at = time.time()
                    st.success(f"Employee information {action} successfully.")
                    st.rerun()
                else:
                    st.error(f"Employee information was not saved: {response_message(result)}")
            except HikvisionError as exc:
                st.error(str(exc))
    st.info("For security, registration should be supervised by an authorized Zalongwa administrator.")
    st.stop()

st.markdown(
    f"""
    <div class="profile"><strong>{escape(employee['employee_no'])} · {escape(employee['name'])}</strong>
    <small>Valid until {escape(employee['valid_until'])}</small></div>
    """,
    unsafe_allow_html=True,
)

if st.button("Change employee information", use_container_width=True):
    reset_registration()
    st.rerun()

client = api_client()
st.markdown('<h3><span class="step">2</span>Add biometric information</h3>', unsafe_allow_html=True)
face_tab, fingerprint_tab = st.tabs(["Face registration", "Fingerprint registration"])

with face_tab:
    st.write("Use a clear, front-facing photograph with only one person visible.")
    camera_photo = st.camera_input("Take face photograph")
    uploaded_photo = st.file_uploader("Or upload a JPEG", type=["jpg", "jpeg"])
    photo = camera_photo or uploaded_photo
    if st.button("Save my face", type="primary", use_container_width=True, disabled=photo is None):
        try:
            with st.spinner("Registering face on the Hikvision device…"):
                result = client.upload_face(employee["employee_no"], photo.getvalue(), photo.name or "face.jpg")
            if result.ok:
                st.session_state.face_done = True
                st.success("Face registered successfully.")
            else:
                st.error(f"Face registration failed: {response_message(result)}")
        except HikvisionError as exc:
            st.error(str(exc))

with fingerprint_tab:
    st.warning("Stand beside the Hikvision terminal. Your phone cannot scan a fingerprint; the terminal sensor performs the capture.")
    finger_id = st.selectbox("Fingerprint slot", range(1, 11), format_func=lambda number: f"Fingerprint {number}")
    if st.button("Start fingerprint capture", type="primary", use_container_width=True):
        try:
            with st.spinner("Place your finger on the Hikvision sensor now…"):
                captured = client.capture_fingerprint(int(finger_id))
            if not captured.data:
                st.error(captured.message or "The device returned no fingerprint data. Try again.")
            else:
                if captured.quality is not None:
                    st.metric("Fingerprint quality", f"{captured.quality}%")
                result = client.apply_fingerprint(employee["employee_no"], captured.data, int(finger_id))
                if result.ok:
                    st.session_state.fingerprint_done = True
                    st.success("Fingerprint registered successfully.")
                else:
                    st.error(f"Fingerprint registration failed: {response_message(result)}")
        except HikvisionError as exc:
            st.error(str(exc))

if st.session_state.get("face_done") or st.session_state.get("fingerprint_done"):
    st.divider()
    st.success("Registration is saved. You may add the other biometric method or finish.")
    if st.button("Finish and clear this session", use_container_width=True):
        reset_registration()
        st.rerun()

st.caption("The application does not permanently store face images or fingerprint templates. They are sent directly to the configured Hikvision terminal.")
