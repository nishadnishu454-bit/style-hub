from django.core.mail import send_mail
from django.conf import settings

def send_branded_otp_email(email, otp, purpose_text, expiry_minutes=5):
    subject = f"STYLE-HUB | OTP for {purpose_text}"
    
    html_message = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f3f4f6; color: #1f2937; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); border: 1px solid #e5e7eb; }}
            .header {{ text-align: center; border-bottom: 2px solid #f3f4f6; padding-bottom: 20px; margin-bottom: 30px; }}
            .brand {{ font-size: 28px; font-weight: 900; letter-spacing: -0.05em; color: #111827; text-transform: uppercase; }}
            .subtitle {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: #9ca3af; font-weight: bold; margin-top: 5px; }}
            .content {{ line-height: 1.6; font-size: 16px; color: #4b5563; }}
            .otp-box {{ text-align: center; background-color: #f9fafb; border: 1px dashed #d1d5db; padding: 20px; border-radius: 8px; font-size: 36px; font-weight: bold; letter-spacing: 6px; color: #111827; margin: 30px 0; }}
            .purpose {{ font-weight: bold; color: #111827; }}
            .warning {{ font-size: 13px; color: #9ca3af; border-top: 1px solid #f3f4f6; padding-top: 20px; margin-top: 30px; text-align: center; }}
            .support {{ font-size: 12px; color: #6b7280; text-align: center; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="brand">STYLE-HUB</div>
                <div class="subtitle">Premium Men's Atelier</div>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>You requested a One-Time Password (OTP) for <span class="purpose">{purpose_text}</span> on STYLE-HUB.</p>
                <div class="otp-box">{otp}</div>
                <p>This code is valid for <strong>{expiry_minutes} minutes</strong>. Please do not share this OTP with anyone, including STYLE-HUB support tailors.</p>
            </div>
            <div class="warning">
                If you did not request this code, please ignore this email or secure your account.
            </div>
            <div class="support">
                Need assistance? Contact us at support@stylehub.com
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"STYLE-HUB\n\nHello,\n\nYour OTP for {purpose_text} is: {otp}\n\nThis code is valid for {expiry_minutes} minutes. Please do not share this code with anyone.\n\nSupport: support@stylehub.com"
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False
    )
