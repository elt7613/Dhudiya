from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from .models import Collection
from wallet.models import Wallet, WalletTransaction

@receiver(post_save, sender=Collection)
def handle_collection_wallet_deduction(sender, instance, created, **kwargs):
    if created:  # Only for new collections
        # Get today's collections for this customer
        today = instance.collection_date
        customer_collections_today = Collection.objects.filter(
            author=instance.author,
            customer=instance.customer,
            collection_date=today,
            is_active=True
        ).order_by('created_at')

        # If this is the first collection for this customer today
        if customer_collections_today.first() == instance:
            try:
                wallet = Wallet.objects.get(user=instance.author)
                
                # Determine deduction amount based on base_snf_percentage
                default_snf = Decimal('9.0')
                deduction_amount = Decimal('5.00') if instance.base_snf_percentage != default_snf else Decimal('2.00')
                
                # Check if wallet has sufficient balance
                if wallet.balance >= deduction_amount:
                    # Deduct amount from wallet
                    wallet.subtract_balance(deduction_amount)
                    
                    # Create transaction record with appropriate description
                    description = (
                        f'Collection fee for customer {instance.customer.name} on {today}'
                        f'{" (Including SNF adjustment fee)" if deduction_amount == Decimal("5.00") else ""}'
                    )
                    
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=deduction_amount,
                        transaction_type='DEBIT',
                        status='SUCCESS',
                        description=description
                    )
            except Wallet.DoesNotExist:
                # Handle case where user doesn't have a wallet
                pass 