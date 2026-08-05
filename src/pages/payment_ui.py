import streamlit as st
import time
import qrcode
from io import BytesIO

def main():
    # --- Page setup ---
    st.title("💳 Ride Payment")

    # --- Payment method selection ---
    st.subheader("Select Payment Method")
    method = st.radio("Choose your payment method:", ["💵 Cash", "💳 Card", "📱 UPI"])

    # --- Card option ---
    if method == "💳 Card":
        st.text_input("Card Number", placeholder="1234 5678 9012 3456")
        st.text_input("Expiry Date (MM/YY)")
        st.text_input("CVV", type="password")

    # --- UPI option (static QR, no amount) ---
    elif method == "📱 UPI":
        merchant_upi = "relaxitaxi@upi"  # your static UPI ID (no amount)
        upi_link = f"upi://pay?pa={merchant_upi}&pn=RelaxiTaxi&cu=INR"

        # Generate QR Code
        qr = qrcode.make(upi_link)
        buf = BytesIO()
        qr.save(buf)
        st.image(buf.getvalue(), caption="📱 Scan to Pay via UPI", width=200)
        st.info(f"Or tap to pay: [Pay via UPI]({upi_link})")

    # --- Confirm payment button ---
    if st.button("Confirm Payment 💰", use_container_width=True):
        st.success("✅ Payment successful! Thank you for riding with RelaxiTaxi.")
        time.sleep(2)
        st.switch_page("pages/book_ride.py")

if __name__ == "__main__":
    main()
