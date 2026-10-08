
import streamlit as st
import pandas as pd
import dns.resolver
from email_validator import validate_email, EmailNotValidError
from functools import lru_cache

st.set_page_config(page_title="Bulk Email Verifier")
st.title("Bulk Email Verifier")
st.write("Upload a CSV file containing an email column.")

@lru_cache(maxsize=10000)
def check_domain(domain):
    try:
        records = dns.resolver.resolve(
            domain, "MX", lifetime=5
        )
        # A null MX means the domain does not accept mail.
        mx_hosts = [str(r.exchange) for r in records]
        if "." in mx_hosts:
            return "Invalid", "Null MX"
        return "Domain Ready", "MX record found"
    except dns.resolver.NXDOMAIN:
        return "Invalid", "Domain does not exist"
    except dns.resolver.NoAnswer:
        return "Unknown", "No MX record; fallback not checked"
    except Exception:
        return "Unknown", "DNS lookup failed"

def verify_email(email):
    try:
        result = validate_email(
            str(email).strip(),
            check_deliverability=False
        )
        status, reason = check_domain(result.domain)
        return pd.Series([status, reason])
    except EmailNotValidError:
        return pd.Series(["Invalid", "Invalid email syntax"])

uploaded_file = st.file_uploader(
    "Upload CSV", type=["csv"]
)

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "email" not in df.columns:
        st.error("CSV must contain an 'email' column.")
    else:
        df[["status", "reason"]] = (
            df["email"].apply(verify_email)
        )

        st.dataframe(df)
        st.write(df["status"].value_counts())

        st.download_button(
            "Download Results",
            df.to_csv(index=False),
            "verified_emails.csv",
            "text/csv"
        )
