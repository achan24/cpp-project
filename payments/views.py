from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal
import stripe
from orders.models import Order
from .models import Payment
from .utils import send_order_confirmation_email

# Create your views here.

# Stripe API key is now loaded from settings which gets it from environment variables
stripe.api_key = settings.STRIPE_SECRET_KEY

def payment_process(request):
    # Get the order ID from the session
    order_id = request.session.get('order_id')
    if not order_id:
        messages.error(request, "No order found to process payment.")
        return redirect('cart:cart_detail')
    
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        # Create a Stripe Checkout Session
        try:
            success_url = request.build_absolute_uri(reverse('payments:completed')) + '?session_id={CHECKOUT_SESSION_ID}'
            cancel_url = request.build_absolute_uri(reverse('payments:cancelled'))
            
            # Create line items for Stripe Checkout
            line_items = []
            for item in order.items.all():
                line_items.append({
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': item.plant.name,
                            'description': item.plant.description[:100] if item.plant.description else '',
                            'images': [request.build_absolute_uri(item.plant.image.url)] if item.plant.image else [],
                        },
                        'unit_amount': int(item.price * 100),  # Convert to cents
                    },
                    'quantity': item.quantity,
                })
            
            # Create Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'order_id': order.id
                },
                shipping_options=[
                    {
                        'shipping_rate_data': {
                            'type': 'fixed_amount',
                            'fixed_amount': {
                                'amount': 0,
                                'currency': 'eur',
                            },
                            'display_name': 'Free shipping',
                            'delivery_estimate': {
                                'minimum': {
                                    'unit': 'business_day',
                                    'value': 3,
                                },
                                'maximum': {
                                    'unit': 'business_day',
                                    'value': 5,
                                },
                            }
                        }
                    },
                ],
            )
            
            # Create a payment record
            payment = Payment.objects.create(
                order=order,
                payment_id=checkout_session.id,
                amount=order.total_price,
                method='credit_card',
                status='pending'
            )
            
            # Redirect to Stripe Checkout
            return redirect(checkout_session.url, code=303)
        
        except stripe.error.StripeError as e:
            messages.error(request, f"An error occurred with the payment: {str(e)}")
            return redirect('orders:order_detail', order_id=order.id)
    
    else:
        # Display payment form
        return render(request, 'payments/form.html', {
            'order': order,
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
        })

def payment_completed(request):
    # Get the session ID from the query parameters
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, "Payment information missing.")
        return redirect('cart:cart_detail')
    
    try:
        # Retrieve the checkout session from Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Get the order ID from the session metadata
        order_id = checkout_session.metadata.order_id
        
        # Get the order and payment
        order = get_object_or_404(Order, id=order_id)
        payment = get_object_or_404(Payment, payment_id=session_id)
        
        # Update payment status based on Stripe status
        if checkout_session.payment_status == 'paid':
            payment.status = 'completed'
            payment.save()
            
            # Update order status
            order.status = 'processing'
            order.save()
            
            # Send order confirmation via Amazon SES
            email_sent = send_order_confirmation_email(order)
            if email_sent:
                messages.success(request, "Order confirmation has been sent to your email.")
            else:
                messages.warning(
                    request,
                    "We couldn't send your order confirmation email. Our team has been notified. "
                    "A verification email has been sent to your address - please check your inbox and "
                    "click the verification link to receive future order confirmations."
                )
            
            # Clear the order ID from the session
            if 'order_id' in request.session:
                del request.session['order_id']
            
            return render(request, 'payments/completed.html', {
                'order': order,
                'payment': payment
            })
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, "Payment was not successful. Please try again.")
            return redirect('orders:order_detail', order_id=order.id)
    
    except (Order.DoesNotExist, Payment.DoesNotExist, stripe.error.StripeError) as e:
        messages.error(request, f"An error occurred while processing your payment: {str(e)}")
        return redirect('cart:cart_detail')

def payment_cancelled(request):
    # Get the order ID from the session
    order_id = request.session.get('order_id')
    if order_id:
        order = get_object_or_404(Order, id=order_id)
        
        # Check if there's a payment record and update its status
        try:
            payment = Payment.objects.get(order=order)
            payment.status = 'failed'
            payment.save()
        except Payment.DoesNotExist:
            pass
    
    messages.warning(request, "Your payment was cancelled.")
    return render(request, 'payments/cancelled.html')
