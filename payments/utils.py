import boto3
import json
from django.conf import settings
from botocore.exceptions import ClientError
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import html
from datetime import datetime

logger = logging.getLogger(__name__)

def is_email_verified(email, auto_verify=True):
    """
    Check if an email address is verified with Amazon SES.
    If auto_verify is True and the email is not verified, send a verification email.
    
    Args:
        email (str): The email address to check
        auto_verify (bool): Whether to automatically send a verification email if not verified
        
    Returns:
        bool: True if the email is verified, False otherwise
    """
    try:
        # Initialize SES client
        ses = boto3.client(
            'ses',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Get list of verified email addresses
        response = ses.list_verified_email_addresses()
        
        # Check if the email is in the verified list
        is_verified = email in response.get('VerifiedEmailAddresses', [])
        
        # If not verified and auto_verify is True, send verification email
        if not is_verified and auto_verify:
            try:
                ses.verify_email_identity(EmailAddress=email)
                logger.info(f"Verification email sent to {email} during order processing")
            except ClientError as e:
                logger.error(f"Error sending verification email to {email}: {e}")
        
        return is_verified
        
    except ClientError as e:
        logger.error(f"Error checking verification status for {email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking verification status for {email}: {e}")
        return False

def send_order_confirmation_email(order):
    """
    Send order confirmation email using Amazon SES.
    
    Args:
        order: The Order object containing order details
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    # Check if the recipient email is verified (required in SES sandbox mode)
    # Also attempt to verify the email if it's not already verified
    if not is_email_verified(order.email, auto_verify=True):
        logger.warning(f"Cannot send order confirmation to {order.email} - email not verified in SES. Verification email has been sent.")
        return False
        
    # Initialize SES client
    try:
        ses = boto3.client(
            'ses',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Prepare email content
        sender = f"Botanica <{settings.AWS_SES_SENDER_EMAIL}>"
        recipient = order.email
        subject = f"Botanica Order Confirmation #{order.id}"
        
        # Get the current year for copyright
        current_year = datetime.now().year
        
        # Format the order date
        order_date = order.created.strftime('%d %B %Y')
        
        # Create HTML body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f1f1f1; padding: 10px 20px; text-align: center; font-size: 12px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f8f8; }}
                .total {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Thank You for Your Order!</h1>
                </div>
                <div class="content">
                    <p>Dear {html.escape(order.first_name)} {html.escape(order.last_name)},</p>
                    <p>We're pleased to confirm that we've received your order. Here are your order details:</p>
                    
                    <p><strong>Order Number:</strong> {order.id}</p>
                    <p><strong>Order Date:</strong> {order_date}</p>
                    
                    <h3>Items Ordered</h3>
                    <table>
                        <tr>
                            <th>Product</th>
                            <th>Quantity</th>
                            <th>Price</th>
                        </tr>
        """
        
        # Add order items to HTML
        for item in order.items.all():
            html_body += f"""
                        <tr>
                            <td>{html.escape(item.plant.name)}</td>
                            <td>{item.quantity}</td>
                            <td>€{item.price:.2f}</td>
                        </tr>
            """
        
        # Add order total
        html_body += f"""
                        <tr class="total">
                            <td colspan="2">Total</td>
                            <td>€{order.total_price:.2f}</td>
                        </tr>
                    </table>
                    
                    <h3>Shipping Address</h3>
                    <p>
                        {html.escape(order.address_line1)}<br>
                        {f"{html.escape(order.address_line2)}<br>" if order.address_line2 else ""}
                        {html.escape(order.town_or_city)}, {html.escape(order.get_county_display())}{f", {html.escape(order.eircode)}" if order.eircode else ""}
                    </p>
                    
                    <p>We'll notify you when your order has been shipped. If you have any questions, please contact our customer service team.</p>
                    
                    <p>Thank you for shopping with Botanica!</p>
                </div>
                <div class="footer">
                    <p>&copy; {current_year} Botanica. All rights reserved.</p>
                    <p>This email was sent to {html.escape(order.email)}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        text_body = f"""
        Thank You for Your Order!
        
        Dear {order.first_name} {order.last_name},
        
        We're pleased to confirm that we've received your order. Here are your order details:
        
        Order Number: {order.id}
        Order Date: {order_date}
        
        Items Ordered:
        """
        
        for item in order.items.all():
            text_body += f"""
        - {item.plant.name} (Qty: {item.quantity}) - €{item.price:.2f}
            """
        
        text_body += f"""
        Total: €{order.total_price:.2f}
        
        Shipping Address:
        {order.address_line1}
        {f"{order.address_line2}" if order.address_line2 else ""}
        {order.town_or_city}, {order.get_county_display()}{f", {order.eircode}" if order.eircode else ""}
        
        We'll notify you when your order has been shipped. If you have any questions, please contact our customer service team.
        
        Thank you for shopping with Botanica!
        
        &copy; {current_year} Botanica. All rights reserved.
        This email was sent to {order.email}
        """
        
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        
        # Attach parts
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        response = ses.send_raw_email(
            Source=sender,
            Destinations=[recipient],
            RawMessage={'Data': msg.as_string()}
        )
        
        logger.info(f"Order confirmation email sent via SES for order #{order.id}. MessageId: {response['MessageId']}")
        return True
        
    except ClientError as e:
        logger.error(f"Error sending SES email for order #{order.id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending SES email for order #{order.id}: {e}")
        return False
