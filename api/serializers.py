from rest_framework import serializers
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

    def get_credit_level(self, obj):
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

    def get_members_count(self, obj):
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

    def get_remaining_balance(self, obj):
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
        write_only=True
    )
    
    class Meta:
        model = Group
        fields = ['title', 'description', 'member_phone_numbers']


class CreateExpenseSerializer(serializers.Serializer):
    """Serializer for creating an expense"""
    group_id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    split_type = serializers.ChoiceField(choices=['equal', 'custom', 'itemized'])
    participant_ids = serializers.ListField(child=serializers.CharField())
    custom_splits = serializers.DictField(
        child=serializers.DecimalField(max_digits=12, decimal_places=2),
        required=False
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
    expense_id = serializers.IntegerField()
    participant_id = serializers.CharField()

    class Meta:
        fields = ['expense_id', 'participant_id']


class PayHeroWebhookSerializer(serializers.Serializer):
    """Serializer for PayHero webhook"""
    ResultCode = serializers.CharField()
    ResultDesc = serializers.CharField()
    MerchantRequestID = serializers.CharField()
    CheckoutRequestID = serializers.CharField()
    Amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    MpesaReceiptNumber = serializers.CharField()
    TransactionDate = serializers.CharField()
    PhoneNumber = serializers.CharField()
