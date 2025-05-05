from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .models import BankAccount
from .models import KYC
from django.forms.widgets import SelectDateWidget
from datetime import date
from .models import Transaction
from .models import Profile
from .models import User, Profile, BankAccount


class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, label="Full Name")
    email = forms.EmailField()
    age = forms.IntegerField(min_value=18, label="Age")
    phone_number = forms.CharField(max_length=15, label="Phone Number (used as Account Number)")

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'age', 'phone_number', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control form-control-lg'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.full_name = self.cleaned_data['full_name']
        user.age = self.cleaned_data['age']
        user.phone_number = self.cleaned_data['phone_number']
        if commit:
            user.save()
            Profile.objects.create(user=user, phone_number=user.phone_number)
            BankAccount.objects.create(user=user, account_number=user.phone_number)
        return user


class DepositForm(forms.Form):
    account = forms.ModelChoiceField(queryset=BankAccount.objects.none())
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = BankAccount.objects.filter(user=user)

class WithdrawForm(DepositForm):
    pass  # Same fields as deposit

class TransferForm(forms.Form):
    from_account = forms.ModelChoiceField(queryset=BankAccount.objects.none())
    to_account = forms.ModelChoiceField(queryset=BankAccount.objects.none())
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['from_account'].queryset = BankAccount.objects.filter(user=user)
        self.fields['to_account'].queryset = BankAccount.objects.exclude(user=user)  # External transfer




class BillPaymentForm(forms.Form):
    account = forms.ModelChoiceField(queryset=BankAccount.objects.none())
    biller_name = forms.CharField(max_length=100)
    bill_number = forms.CharField(max_length=50)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = BankAccount.objects.filter(user=user)



class KYCUploadForm(forms.ModelForm):
    class Meta:
        model = KYC
        fields = ['id_document']



class CardFreezeForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['is_frozen']





class TransactionFilterForm(forms.Form):
    account = forms.ModelChoiceField(queryset=BankAccount.objects.none(), required=False)
    transaction_type = forms.ChoiceField(choices=[('', 'All')] + list(Transaction.TRANSACTION_TYPES), required=False)
    start_date = forms.DateField(widget=SelectDateWidget(years=range(2020, date.today().year+1)), required=False)
    end_date = forms.DateField(widget=SelectDateWidget(years=range(2020, date.today().year+1)), required=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = BankAccount.objects.filter(user=user)


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture', 'phone_number', 'location']
