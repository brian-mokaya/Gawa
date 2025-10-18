from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class User(models.Model):
    """User model - synced from Supabase Auth"""
    id = models.CharField(max_length=255, primary_key=True)  # Supabase UID
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    credit_score = models.IntegerField(default=600, validators=[MinValueValidator(0), MaxValueValidator(1000)])
    total_payments = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    on_time_payments = models.IntegerField(default=0)
    total_late_payments = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.name} ({self.email})"

    def calculate_credit_score(self):
        """Calculate credit score based on payment history"""
        score = 600  # Base score
        score += (int(self.total_payments) * 5) + (self.on_time_payments * 10)
        score -= (self.total_late_payments * 15)
        return min(max(score, 0), 1000)  # Clamp between 0 and 1000

    def update_credit_score(self):
        """Update the credit score"""
        self.credit_score = self.calculate_credit_score()
        self.save()


class Group(models.Model):
    """Group model for splitting expenses"""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='groups_created')
    members = models.ManyToManyField(User, related_name='groups', through='GroupMember')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'groups'
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class GroupMember(models.Model):
    """Through table for Group-User relationship"""
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'group_members'
        unique_together = ('group', 'user')
        verbose_name = 'Group Member'
        verbose_name_plural = 'Group Members'

    def __str__(self):
        return f"{self.user.name} in {self.group.title}"


class Expense(models.Model):
    """Expense model for tracking shared costs"""
    SPLIT_CHOICES = [
        ('equal', 'Equal Split'),
        ('custom', 'Custom Split'),
        ('itemized', 'Itemized'),
    ]

    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses_paid')
    split_type = models.CharField(max_length=20, choices=SPLIT_CHOICES, default='equal')
    participants = models.ManyToManyField(User, related_name='expenses_participated', through='ExpenseParticipant')
    date_created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    settled = models.BooleanField(default=False)

    class Meta:
        db_table = 'expenses'
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'
        ordering = ['-date_created']

    def __str__(self):
        return f"{self.title} - {self.total_amount}"

    def calculate_shares(self):
        """Calculate each participant's share"""
        participants_count = self.participants.count()
        if participants_count == 0:
            return {}
        
        if self.split_type == 'equal':
            share = self.total_amount / participants_count
            return {p.id: share for p in self.participants.all()}
        
        # For custom and itemized, fetch from ExpenseParticipant
        shares = {}
        for ep in self.expense_participants.all():
            shares[ep.user.id] = ep.amount_owed
        return shares


class ExpenseParticipant(models.Model):
    """Through table for Expense-User relationship tracking individual shares"""
    id = models.AutoField(primary_key=True)
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='expense_participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_owed = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    settled = models.BooleanField(default=False)

    class Meta:
        db_table = 'expense_participants'
        unique_together = ('expense', 'user')
        verbose_name = 'Expense Participant'
        verbose_name_plural = 'Expense Participants'

    def __str__(self):
        return f"{self.user.name} owes {self.amount_owed} for {self.expense.title}"

    def remaining_balance(self):
        """Calculate remaining balance"""
        return self.amount_owed - self.amount_paid


class Payment(models.Model):
    """Payment model for tracking individual payments via PayHero"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('initiated', 'Initiated (STK Sent)'),
        ('success', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.AutoField(primary_key=True)
    expense_participant = models.OneToOneField(ExpenseParticipant, on_delete=models.CASCADE, related_name='payment')
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='payments')
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_made')
    payee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_received')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    payhero_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payer.name} → {self.payee.name}: {self.amount}"


class Balance(models.Model):
    """Balance tracking model for "who owes who"""
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='balances')
    debtor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owes')
    creditor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owed_by')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    settled = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'balances'
        unique_together = ('group', 'debtor', 'creditor')
        verbose_name = 'Balance'
        verbose_name_plural = 'Balances'

    def __str__(self):
        return f"{self.debtor.name} owes {self.creditor.name}: {self.amount}"


class SmartSplitSuggestion(models.Model):
    """AI-based split suggestions"""
    id = models.AutoField(primary_key=True)
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='ai_suggestions')
    suggestion_data = models.JSONField()  # Stores suggested split distribution
    reasoning = models.TextField()
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'smart_split_suggestions'
        verbose_name = 'Smart Split Suggestion'
        verbose_name_plural = 'Smart Split Suggestions'

    def __str__(self):
        return f"Suggestion for {self.expense.title}"
