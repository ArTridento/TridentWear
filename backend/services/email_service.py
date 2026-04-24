import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import get_settings
from typing import List
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

settings = get_settings()


class EmailService:
    """Email service for OTP and order notifications"""

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email body

        Returns:
            True if sent successfully
        """
        try:
            # ========== CREATE MESSAGE ==========
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.SENDER_EMAIL
            message["To"] = to_email

            # ========== ATTACH HTML ==========
            part = MIMEText(html_content, "html")
            message.attach(part)

            # ========== SEND EMAIL ==========
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()  # Secure connection
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(message)

            logger.info(f"Email sent to: {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    @staticmethod
    def send_otp_email(email: str, otp: str) -> bool:
        """
        Send OTP email to user.

        Args:
            email: User email
            otp: 6-digit OTP

        Returns:
            True if sent successfully
        """
        subject = "Your TridentWear OTP"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #000;">Welcome to TridentWear</h2>
                    <p>Your One-Time Password (OTP) is:</p>

                    <div style="font-size: 32px; font-weight: bold; text-align: center; padding: 20px; background: #f0f0f0; border-radius: 5px; margin: 20px 0;">
                        {otp}
                    </div>

                    <p style="color: #666;">
                        <strong>⚠️ Security Notice:</strong> This OTP is valid for 10 minutes only.
                    </p>

                    <p style="color: #666;">
                        Never share your OTP with anyone. TridentWear support will never ask for your OTP.
                    </p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">

                    <p style="color: #999; font-size: 12px;">
                        If you didn't request this OTP, please ignore this email.
                    </p>

                    <p style="color: #999; font-size: 12px;">
                        © 2026 TridentWear. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """

        return EmailService.send_email(email, subject, html_content)

    @staticmethod
    def send_order_confirmation_email(
        email: str,
        order_id: str,
        order_date: str,
        items: List[dict],
        subtotal: Decimal,
        tax: Decimal,
        shipping: Decimal,
        total: Decimal,
    ) -> bool:
        """
        Send order confirmation email.

        Args:
            email: Customer email
            order_id: Order ID
            order_date: Order date
            items: List of order items
            subtotal: Subtotal
            tax: Tax amount
            shipping: Shipping cost
            total: Total amount

        Returns:
            True if sent successfully
        """
        subject = f"Order Confirmation - {order_id}"

        # ========== BUILD ITEMS TABLE ==========
        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{item['name']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{item['quantity']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">₹{item['unit_price']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">₹{item['total']}</td>
            </tr>
            """

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #000;">Order Confirmation</h2>
                    <p>Thank you for your purchase at TridentWear!</p>

                    <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Order ID:</strong> {order_id}</p>
                        <p><strong>Order Date:</strong> {order_date}</p>
                    </div>

                    <h3>Order Items</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #f0f0f0;">
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Product</th>
                                <th style="padding: 10px; text-align: center; border-bottom: 2px solid #ddd;">Qty</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">Price</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>

                    <div style="margin-top: 20px; text-align: right;">
                        <p><strong>Subtotal:</strong> ₹{subtotal}</p>
                        <p><strong>Tax (18%):</strong> ₹{tax}</p>
                        <p><strong>Shipping:</strong> ₹{shipping}</p>
                        <h3 style="color: #000; border-top: 1px solid #ddd; padding-top: 10px;">
                            <strong>Total: ₹{total}</strong>
                        </h3>
                    </div>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">

                    <p>Your order will be processed shortly. You'll receive a shipping confirmation once your items are dispatched.</p>

                    <p style="color: #999; font-size: 12px;">
                        © 2026 TridentWear. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """

        return EmailService.send_email(email, subject, html_content)

    @staticmethod
    def send_password_reset_email(email: str, reset_token: str) -> bool:
        """
        Send password reset email.

        Args:
            email: User email
            reset_token: Reset token

        Returns:
            True if sent successfully
        """
        subject = "Reset Your TridentWear Password"

        reset_link = f"https://tridentwear.com/reset-password?token={reset_token}"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #000;">Password Reset Request</h2>
                    <p>We received a request to reset your TridentWear password.</p>

                    <p style="margin-top: 20px;">
                        <a href="{reset_link}" style="display: inline-block; padding: 10px 20px; background: #000; color: #fff; text-decoration: none; border-radius: 5px;">
                            Reset Password
                        </a>
                    </p>

                    <p style="color: #666;">
                        Or copy and paste this link in your browser:<br>
                        <code>{reset_link}</code>
                    </p>

                    <p style="color: #666; margin-top: 20px;">
                        This link will expire in 1 hour.
                    </p>

                    <p style="color: #666;">
                        If you didn't request this reset, please ignore this email and your password will remain unchanged.
                    </p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">

                    <p style="color: #999; font-size: 12px;">
                        © 2026 TridentWear. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """

        return EmailService.send_email(email, subject, html_content)
