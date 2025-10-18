from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import (
    User, Group, GroupMember, Expense, ExpenseParticipant,
    Payment, Balance, SmartSplitSuggestion
)
from decimal import Decimal


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = [
            'id', 'name', 'email', 'phone_number', 'credit_score',
            'total_payments', 'on_time_payments', 'total_late_payments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'credit_score']


class UserProfileSerializer(serializers.ModelSerializer):
    """Detailed user profile with additional insights"""
    credit_level = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'name', 'email', 'phone_number', 'credit_score',
            'credit_level', 'total_payments', 'on_time_payments',
            'total_late_payments', 'created_at'
        ]

    @extend_schema_field(OpenApiTypes.STR)
    def get_credit_level(self, obj) -> str:
        """Determine credit level based on score"""
        if obj.credit_score >= 850:
            return 'Excellent'
        elif obj.credit_score >= 750:
            return 'Good'
        elif obj.credit_score >= 650:
            return 'Fair'
        else:
            return 'Poor'


class GroupMemberSerializer(serializers.ModelSerializer):
    """Serializer for GroupMember"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = GroupMember
        fields = ['id', 'user', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for Group model"""
    created_by = UserSerializer(read_only=True)
    members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = [
            'id', 'title', 'description', 'created_by',
            'members_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.INT)
    def get_members_count(self, obj) -> int:
        return obj.members.count()


class GroupDetailSerializer(serializers.ModelSerializer):
    """Detailed group serializer with members"""
    created_by = UserSerializer(read_only=True)
    group_members = GroupMemberSerializer(many=True, read_only=True)
    
    class Meta:
        model = Group
        fields = [
            'id', 'title', 'description', 'created_by',
            'group_members', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExpenseParticipantSerializer(serializers.ModelSerializer):
    """Serializer for ExpenseParticipant"""
    user = UserSerializer(read_only=True)
    remaining_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpenseParticipant
        fields = [
            'id', 'user', 'amount_owed', 'amount_paid',
            'remaining_balance', 'settled'
        ]
        read_only_fields = ['id', 'amount_paid']

    @extend_schema_field(OpenApiTypes.STR)
    def get_remaining_balance(self, obj) -> str:
        return str(obj.remaining_balance())


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for Expense model"""
    paid_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'group', 'title', 'description', 'total_amount',
            'paid_by', 'split_type', 'date_created', 'updated_at', 'settled'
        ]
        read_only_fields = ['id', 'date_created', 'updated_at']


class ExpenseDetailSerializer(serializers.ModelSerializer):
    """Detailed expense serializer with participants"""
    paid_by = UserSerializer(read_only=True)
    expense_participants = ExpenseParticipantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'group', 'title', 'description', 'total_amount',
            'paid_by', 'split_type', 'expense_participants',
            'date_created', 'updated_at', 'settled'
        ]
        read_only_fields = ['id', 'date_created', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    payer = UserSerializer(read_only=True)
    payee = UserSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'expense', 'payer', 'payee', 'amount', 'status',
            'transaction_id', 'payhero_transaction_id', 'created_at',
            'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'completed_at',
            'transaction_id', 'payhero_transaction_id'
        ]


class BalanceSerializer(serializers.ModelSerializer):
    """Serializer for Balance model"""
    debtor = UserSerializer(read_only=True)
    creditor = UserSerializer(read_only=True)
    
    class Meta:
        model = Balance
        fields = [
            'id', 'group', 'debtor', 'creditor', 'amount',
            'settled', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']


class SmartSplitSuggestionSerializer(serializers.ModelSerializer):
    """Serializer for SmartSplitSuggestion"""
    class Meta:
        model = SmartSplitSuggestion
        fields = [
            'id', 'expense', 'suggestion_data', 'reasoning',
            'accepted', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# Write Serializers (for POST/PUT operations)
class CreateGroupSerializer(serializers.ModelSerializer):
    """Serializer for creating a group"""
    member_phone_numbers = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        write_only=True,
        help_text="List of phone numbers to invite (+254712345678 format)"
    )
    
    class Meta:
        model = Group
        fields = ['title', 'description', 'member_phone_numbers']


class CreateExpenseSerializer(serializers.Serializer):
    """Serializer for creating an expense"""
    group_id = serializers.IntegerField(
        help_text="ID of the group this expense belongs to"
    )
    title = serializers.CharField(
        max_length=255,
        help_text="Expense title (e.g., 'Dinner', 'Hotel')"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional expense description"
    )
    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total amount in KES"
    )
    split_type = serializers.ChoiceField(
        choices=['equal', 'custom', 'itemized'],
        help_text="How to split: 'equal' divides equally, 'custom' uses custom_splits"
    )
    participant_ids = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of user IDs participating in this expense"
    )
    custom_splits = serializers.DictField(
        child=serializers.DecimalField(max_digits=12, decimal_places=2),
        required=False,
        help_text="For 'custom' split_type: {user_id: amount_owed}"
    )
    auto_initiate_payments = serializers.BooleanField(
        default=False,
        required=False,
        help_text="If True, automatically send STK push to all participants"
    )

    def validate_total_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total amount must be greater than 0")
        return value

    def validate_custom_splits(self, value):
        if value:
            total = sum(Decimal(v) for v in value.values())
            if total != Decimal(self.initial_data.get('total_amount', 0)):
                raise serializers.ValidationError(
                    "Custom splits must sum to total amount"
                )
        return value


class InitiatePaymentSerializer(serializers.Serializer):
    """Serializer for initiating PayHero payment"""
    expense_id = serializers.IntegerField(
        help_text="ID of the expense to pay for"
    )
    participant_id = serializers.CharField(
        help_text="User ID of the person making the payment"
    )

    class Meta:
        fields = ['expense_id', 'participant_id']


class PayHeroWebhookSerializer(serializers.Serializer):
    """Serializer for PayHero webhook"""
    ResultCode = serializers.CharField(
        help_text="0 = Success, other values = Failed"
    )
    ResultDesc = serializers.CharField(
        help_text="Result description from PayHero"
    )
    MerchantRequestID = serializers.CharField(
        help_text="Merchant request ID from PayHero"
    )
    CheckoutRequestID = serializers.CharField(
        help_text="Checkout request ID from PayHero"
    )
    Amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Payment amount in KES"
    )
    MpesaReceiptNumber = serializers.CharField(
        help_text="M-Pesa receipt number"
    )
    TransactionDate = serializers.CharField(
        help_text="Transaction date from PayHero"
    )
    PhoneNumber = serializers.CharField(
        help_text="Customer phone number"
    )


# Additional Serializers for Request Bodies
class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration"""
    name = serializers.CharField(
        help_text="User's full name"
    )
    email = serializers.EmailField(
        help_text="User's email address"
    )
    phone_number = serializers.CharField(
        help_text="User's phone number (+254712345678 format)"
    )
    password = serializers.CharField(
        write_only=True,
        help_text="User's password"
    )


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(
        help_text="User email address"
    )
    password = serializers.CharField(
        write_only=True,
        help_text="User password"
    )


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for login response"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    user = UserSerializer()
    access_token = serializers.CharField(
        help_text="JWT access token for authentication"
    )
    refresh_token = serializers.CharField(
        help_text="JWT refresh token for renewing access token"
    )


class AddMemberSerializer(serializers.Serializer):
    """Serializer for adding member to group"""
    phone_number = serializers.CharField(
        help_text="Phone number of user to add (+254712345678 format)"
    )


class SmartSplitRequestSerializer(serializers.Serializer):
    """Serializer for smart split request"""
    expense_id = serializers.IntegerField(
        help_text="ID of the expense to get split suggestions for"
    )
