from django.contrib import admin
from .models import (
    User, Group, GroupMember, Expense, ExpenseParticipant,
    Payment, Balance, SmartSplitSuggestion
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone_number', 'credit_score')
    list_filter = ('credit_score', 'created_at')
    search_fields = ('name', 'email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'user', 'joined_at')
    list_filter = ('joined_at',)
    search_fields = ('group__title', 'user__name')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'group', 'paid_by', 'total_amount', 'split_type', 'settled')
    list_filter = ('split_type', 'settled', 'date_created')
    search_fields = ('title', 'description')
    readonly_fields = ('date_created', 'updated_at')


@admin.register(ExpenseParticipant)
class ExpenseParticipantAdmin(admin.ModelAdmin):
    list_display = ('id', 'expense', 'user', 'amount_owed', 'amount_paid', 'settled')
    list_filter = ('settled',)
    search_fields = ('expense__title', 'user__name')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'payer', 'payee', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('payer__name', 'payee__name', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'debtor', 'creditor', 'amount', 'settled')
    list_filter = ('settled', 'last_updated')
    search_fields = ('group__title', 'debtor__name', 'creditor__name')
    readonly_fields = ('last_updated',)


@admin.register(SmartSplitSuggestion)
class SmartSplitSuggestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'expense', 'accepted', 'created_at')
    list_filter = ('accepted', 'created_at')
    search_fields = ('expense__title', 'reasoning')
    readonly_fields = ('created_at',)
