from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserRegistrationForm
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.decorators import login_required
from .models import BankAccount, Transaction
from .forms import DepositForm, WithdrawForm, TransferForm
from .forms import BillPaymentForm
from .models import BillPayment
from .models import KYC
from .forms import KYCUploadForm
from django.db.models import Q
from .forms import TransactionFilterForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from decimal import Decimal
from .forms import ProfileUpdateForm
from .models import Profile



class LoginView(DjangoLoginView):
    template_name = 'accounts/login.html' 



def buy_airtime(request):
    return render(request, 'services/airtime.html')  

def process_service_payment(user, amount, service_type, details):
    profile = user.profile
    if profile.balance >= amount:
        profile.balance -= amount
        profile.save()
        Transaction.objects.create(user=user, transaction_type=service_type, amount=amount, details=details)
        return True
    return False



def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create the Profile for the user after registration
            Profile.objects.create(user=user)
            return redirect('login')  # Redirect to login page
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def dashboard(request):
   services = [
    {"name": "Deposit", "icon": "fa-download", "url": "deposit"},
    {"name": "Withdraw", "icon": "fa-upload", "url": "withdraw"},
    {"name": "Transfer", "icon": "fa-exchange-alt", "url": "transfer"},
    {"name": "Bill Pay", "icon": "fa-bolt", "url": "bill_payment"},
    {"name": "KYC", "icon": "fa-id-card", "url": "kyc_upload"},
    {"name": "Transactions", "icon": "fa-history", "url": "transaction_history"},
    {"name": "Freeze Cards", "icon": "fa-snowflake", "url": "manage_cards"},
    ]
   transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')[:5]
   profile = request.user.profile

   return render(request, 'accounts/dashboard.html', {
        'services': services,
        'transactions': transactions,
        'profile': profile,
        'user': request.user,
    })


@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Profile

@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    defaults={'balance': Decimal('0.00')}
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def deposit_view(request):
    form = DepositForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        account = form.cleaned_data['account']
        amount = form.cleaned_data['amount']
        account.balance += amount
        account.save()
        Transaction.objects.create(to_account=account, transaction_type='deposit', amount=amount)
        return redirect('dashboard')
    return render(request, 'accounts/transaction_form.html', {'form': form, 'title': 'Deposit'})

@login_required
def withdraw_view(request):
    form = WithdrawForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        account = form.cleaned_data['account']
        amount = form.cleaned_data['amount']
        if amount <= account.balance:
            account.balance -= amount
            account.save()
            Transaction.objects.create(from_account=account, transaction_type='withdrawal', amount=amount)
            return redirect('dashboard')
    return render(request, 'accounts/transaction_form.html', {'form': form, 'title': 'Withdraw'})

@login_required
def transfer_view(request):
    form = TransferForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        from_account = form.cleaned_data['from_account']
        to_account = form.cleaned_data['to_account']
        amount = form.cleaned_data['amount']
        if amount <= from_account.balance:
            from_account.balance -= amount
            to_account.balance += amount
            from_account.save()
            to_account.save()
            Transaction.objects.create(
                from_account=from_account, to_account=to_account,
                transaction_type='transfer', amount=amount
            )
            return redirect('dashboard')
    return render(request, 'accounts/transaction_form.html', {'form': form, 'title': 'Transfer'})




@login_required
def bill_payment_view(request):
    if request.method == 'POST':
        form = BillPaymentForm(request.user, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            account = data['account']
            amount = data['amount']
            if account.balance >= amount:
                account.balance -= amount
                account.save()
                BillPayment.objects.create(
                    user=request.user,
                    account=account,
                    biller_name=data['biller_name'],
                    bill_number=data['bill_number'],
                    amount=amount
                )
                messages.success(request, "Bill paid successfully.")
                return redirect('dashboard')
            else:
                messages.error(request, "Insufficient balance.")
    else:
        form = BillPaymentForm(request.user)
    return render(request, 'accounts/bill_payment.html', {'form': form, 'title': 'Bill Payment'})


@login_required
def kyc_upload_view(request):
    try:
        kyc = request.user.kyc
    except KYC.DoesNotExist:
        kyc = None

    if request.method == 'POST':
        form = KYCUploadForm(request.POST, request.FILES, instance=kyc)
        if form.is_valid():
            kyc_obj = form.save(commit=False)
            kyc_obj.user = request.user
            kyc_obj.status = 'pending'
            kyc_obj.save()
            messages.success(request, "KYC document submitted successfully.")
            return redirect('dashboard')
    else:
        form = KYCUploadForm(instance=kyc)

    return render(request, 'accounts/kyc_upload.html', {'form': form, 'kyc': kyc})
  


@login_required
def manage_cards(request):
    accounts = BankAccount.objects.filter(user=request.user)
    if request.method == 'POST':
        for account in accounts:
            key = f"freeze_{account.id}"
            if key in request.POST:
                account.is_frozen = not account.is_frozen
                account.save()
        messages.success(request, "Card freeze settings updated.")
        return redirect('manage_cards')

    return render(request, 'accounts/manage_cards.html', {'accounts': accounts})




@login_required
def transaction_history_view(request):
    form = TransactionFilterForm(request.user, request.GET or None)
    transactions = Transaction.objects.filter(
        Q(from_account__user=request.user) | Q(to_account__user=request.user)
    ).order_by('-timestamp')

    if form.is_valid():
        if form.cleaned_data['account']:
            account = form.cleaned_data['account']
            transactions = transactions.filter(
                Q(from_account=account) | Q(to_account=account)
            )
        if form.cleaned_data['transaction_type']:
            transactions = transactions.filter(transaction_type=form.cleaned_data['transaction_type'])
        if form.cleaned_data['start_date']:
            transactions = transactions.filter(timestamp__date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data['end_date']:
            transactions = transactions.filter(timestamp__date__lte=form.cleaned_data['end_date'])

    return render(request, 'accounts/transaction_history.html', {
        'form': form,
        'transactions': transactions,
    })



def create_transaction(from_account, to_account, amount, transaction_type):
    requires_approval = amount > 5000  # Suspicious threshold

    txn = Transaction.objects.create(
        from_account=from_account,
        to_account=to_account,
        sender=from_account,
        transaction_type=transaction_type,
        amount=amount,
        requires_approval=requires_approval,
        is_approved=not requires_approval,
    )

    if not requires_approval:
        # Update balances immediately
        if transaction_type == 'withdrawal':
            from_account.balance -= amount
            from_account.save()
        elif transaction_type == 'deposit':
            to_account.balance += amount
            to_account.save()
        elif transaction_type == 'transfer':
            from_account.balance -= amount
            to_account.balance += amount
            from_account.save()
            to_account.save()
    
    return txn



from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def approve_transactions_view(request):
    pending_txns = Transaction.objects.filter(requires_approval=True, is_approved=False)

    if request.method == 'POST':
        txn_id = request.POST.get('txn_id')
        action = request.POST.get('action')
        txn = Transaction.objects.get(id=txn_id)

        if action == 'approve':
            txn.is_approved = True
            txn.save()
            # Apply balance updates
            if txn.transaction_type == 'withdrawal' and txn.from_account:
                txn.from_account.balance -= txn.amount
                txn.from_account.save()
            elif txn.transaction_type == 'deposit' and txn.to_account:
                txn.to_account.balance += txn.amount
                txn.to_account.save()
            elif txn.transaction_type == 'transfer':
                txn.from_account.balance -= txn.amount
                txn.to_account.balance += txn.amount
                txn.from_account.save()
                txn.to_account.save()
        elif action == 'reject':
            txn.delete()

        messages.success(request, "Transaction decision recorded.")
        return redirect('approve_transactions')

    return render(request, 'accounts/approve_transactions.html', {'transactions': pending_txns})



@login_required
def airtime_view(request):
    if request.method == 'POST':
        network = request.POST.get('network')
        number = request.POST.get('number')
        amount = Decimal(request.POST.get('amount'))

        profile = request.user.profile
        if request.method == 'POST':
            
            if process_service_payment(request.user, amount, 'airtime', f"{network} - {number}"):
                messages.success(request, 'Airtime successful.')
                return redirect('dashboard')
    

            else:
                messages.error(request, 'Insufficient balance.')

    return render(request, 'services/airtime.html')




@login_required
def tv_view(request):
    if request.method == 'POST':
        provider = request.POST.get('provider')
        smartcard = request.POST.get('smartcard')
        amount = Decimal(request.POST.get('amount'))

        profile = request.user.profile
        if profile.balance >= amount:
            profile.balance -= amount
            profile.save()

            Transaction.objects.create(
                user=request.user,
                transaction_type='tv',
                amount=amount,
                details=f"{provider} - {smartcard}"
            )
            messages.success(request, 'TV payment successful.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Insufficient balance.')

    return render(request, 'services/tv.html')


@login_required
def electricity_view(request):
    if request.method == 'POST':
        disco = request.POST.get('disco')
        meter = request.POST.get('meter')
        amount = Decimal(request.POST.get('amount'))

        profile = request.user.profile
        if profile.balance >= amount:
            profile.balance -= amount
            profile.save()

            Transaction.objects.create(
                user=request.user,
                transaction_type='electricity',
                amount=amount,
                details=f"{disco} - {meter}"
            )
            messages.success(request, 'Electricity payment successful.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Insufficient balance.')

    return render(request, 'services/electricity.html')



@login_required
def profile_edit(request):
    profile = Profile.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})

@login_required
def buy_data(request):
    if request.method == 'POST':
        network = request.POST.get('network')
        number = request.POST.get('number')
        amount = Decimal(request.POST.get('amount'))

        profile = request.user.profile
        if profile.balance >= amount:
            profile.balance -= amount
            profile.save()

            Transaction.objects.create(
                user=request.user,
                transaction_type='data',
                amount=amount,
                details=f"{network} - {number}"
            )
            messages.success(request, 'Data purchase successful.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Insufficient balance.')

    return render(request, 'services/data.html')


@login_required
def pay_electricity(request):
    if request.method == 'POST':
        disco = request.POST.get('disco')
        meter = request.POST.get('meter')
        amount = Decimal(request.POST.get('amount'))

        profile = request.user.profile
        if profile.balance >= amount:
            profile.balance -= amount
            profile.save()

            Transaction.objects.create(
                user=request.user,
                transaction_type='electricity',
                amount=amount,
                details=f"{disco} - {meter}"
            )
            messages.success(request, 'Electricity payment successful.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Insufficient balance.')

    return render(request, 'services/electricity.html')


def update_profile_picture(request):
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        profile = request.user.profile
        profile.profile_picture = request.FILES['profile_picture']
        profile.save()
    return redirect('accounts/profile') 
