"""
API Views for Gawa application
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q, Sum, F
from decimal import Decimal
import uuid

from .models import (
    User, Group, GroupMember, Expense, ExpenseParticipant,
    Payment, Balance, SmartSplitSuggestion
)
from .serializers import (
    UserSerializer, UserProfileSerializer, GroupSerializer,
    GroupDetailSerializer, ExpenseSerializer, ExpenseDetailSerializer,
    ExpenseParticipantSerializer, PaymentSerializer, BalanceSerializer,
    SmartSplitSuggestionSerializer, CreateGroupSerializer,
    CreateExpenseSerializer, InitiatePaymentSerializer
)
from .supabase_service import get_supabase_service
from .payhero_service import get_payhero_service
from .auth import get_current_user


# ============================================================================
# Authentication Views
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User registration via Supabase"""
    email = request.data.get('email')
    password = request.data.get('password')
    name = request.data.get('name')
    phone_number = request.data.get('phone_number')
    
    if not all([email, password, name, phone_number]):
        return Response({
            'success': False,
            'message': 'Missing required fields: email, password, name, phone_number'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    supabase_service = get_supabase_service()
    result = supabase_service.sign_up(email, password, name, phone_number)
    
    if result['success']:
        user_serializer = UserSerializer(result['user'])
        return Response({
            'success': True,
            'message': 'User registered successfully',
            'user': user_serializer.data,
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({
            'success': False,
            'message': result.get('message', 'Registration failed')
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login via Supabase"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'success': False,
            'message': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    supabase_service = get_supabase_service()
    result = supabase_service.sign_in(email, password)
    
    if result['success']:
        user_serializer = UserSerializer(result['user'])
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': user_serializer.data,
            'access_token': result.get('access_token'),
            'refresh_token': result.get('refresh_token'),
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': result.get('message', 'Login failed')
        }, status=status.HTTP_401_UNAUTHORIZED)


# ============================================================================
# User Views
# ============================================================================

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserProfileSerializer
        return UserSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_me(request):
    """Get current user profile with insights"""
    user = request.user
    serializer = UserProfileSerializer(user)
    
    # Get payment statistics
    payments_made = Payment.objects.filter(payer=user, status='success').aggregate(
        total=Sum('amount')
    )
    
    groups_count = user.groups.count()
    expenses_count = user.expenses_participated.count()
    
    return Response({
        'user': serializer.data,
        'statistics': {
            'total_payments_made': str(payments_made.get('total') or 0),
            'groups_count': groups_count,
            'expenses_count': expenses_count,
        }
    })


# ============================================================================
# Group Views
# ============================================================================

class GroupViewSet(viewsets.ModelViewSet):
    """ViewSet for managing groups"""
    permission_classes = [IsAuthenticated]
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GroupDetailSerializer
        elif self.action == 'create':
            return CreateGroupSerializer
        return GroupSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new group"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        group = Group.objects.create(
            title=serializer.validated_data['title'],
            description=serializer.validated_data.get('description', ''),
            created_by=request.user
        )
        
        # Add creator as member
        GroupMember.objects.create(group=group, user=request.user)
        
        # Add members by phone number
        member_phones = serializer.validated_data.get('member_phone_numbers', [])
        for phone in member_phones:
            try:
                supabase_service = get_supabase_service()
                member = supabase_service.get_user_by_phone(phone)
                if member and member != request.user:
                    GroupMember.objects.get_or_create(group=group, user=member)
            except Exception as e:
                pass  # Skip invalid phone numbers
        
        response_serializer = GroupDetailSerializer(group)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        """Filter groups for current user"""
        return Group.objects.filter(members=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the group"""
        group = self.get_object()
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({
                'success': False,
                'message': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        supabase_service = get_supabase_service()
        member = supabase_service.get_user_by_phone(phone_number)
        
        if not member:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        group_member, created = GroupMember.objects.get_or_create(
            group=group, user=member
        )
        
        if created:
            return Response({
                'success': True,
                'message': f'Member {member.name} added'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': 'Member already in group'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def balances(self, request, pk=None):
        """Get who owes who in the group"""
        group = self.get_object()
        balances = Balance.objects.filter(group=group)
        serializer = BalanceSerializer(balances, many=True)
        
        return Response({
            'group_id': group.id,
            'group_title': group.title,
            'balances': serializer.data,
        })


# ============================================================================
# Expense Views
# ============================================================================

class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet for managing expenses"""
    permission_classes = [IsAuthenticated]
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ExpenseDetailSerializer
        elif self.action == 'create':
            return CreateExpenseSerializer
        return ExpenseSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new expense and calculate shares"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        group_id = serializer.validated_data['group_id']
        title = serializer.validated_data['title']
        description = serializer.validated_data.get('description', '')
        total_amount = serializer.validated_data['total_amount']
        split_type = serializer.validated_data['split_type']
        participant_ids = serializer.validated_data['participant_ids']
        custom_splits = serializer.validated_data.get('custom_splits', {})
        
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create expense
        expense = Expense.objects.create(
            group=group,
            title=title,
            description=description,
            total_amount=total_amount,
            paid_by=request.user,
            split_type=split_type
        )
        
        # Add participants and calculate shares
        participants_list = []
        for participant_id in participant_ids:
            try:
                participant = User.objects.get(id=participant_id)
                participants_list.append(participant)
            except User.DoesNotExist:
                pass
        
        if split_type == 'equal':
            share_amount = total_amount / len(participants_list)
            for participant in participants_list:
                ExpenseParticipant.objects.create(
                    expense=expense,
                    user=participant,
                    amount_owed=share_amount
                )
        elif split_type == 'custom' and custom_splits:
            for participant in participants_list:
                amount_owed = Decimal(str(custom_splits.get(participant.id, 0)))
                if amount_owed > 0:
                    ExpenseParticipant.objects.create(
                        expense=expense,
                        user=participant,
                        amount_owed=amount_owed
                    )
        
        # Add participants to expense
        for participant in participants_list:
            expense.participants.add(participant)
        
        # Create or update balances
        for participant in participants_list:
            if participant != request.user:
                balance, _ = Balance.objects.get_or_create(
                    group=group,
                    debtor=participant,
                    creditor=request.user,
                    defaults={'amount': Decimal('0')}
                )
                balance.amount += total_amount / len(participants_list)
                balance.save()
        
        response_serializer = ExpenseDetailSerializer(expense)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        """Filter expenses for current user's groups"""
        return Expense.objects.filter(group__members=self.request.user)
    
    @action(detail=True, methods=['post'])
    def settle(self, request, pk=None):
        """Mark expense as settled"""
        expense = self.get_object()
        expense.settled = True
        expense.save()
        
        # Mark all participants as settled
        ExpenseParticipant.objects.filter(expense=expense).update(settled=True)
        
        return Response({
            'success': True,
            'message': 'Expense marked as settled'
        })


# ============================================================================
# Payment Views
# ============================================================================

class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payments"""
    permission_classes = [IsAuthenticated]
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        """Filter payments for current user"""
        return Payment.objects.filter(
            Q(payer=self.request.user) | Q(payee=self.request.user)
        )
    
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Initiate a payment via PayHero"""
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        expense_id = serializer.validated_data['expense_id']
        participant_id = serializer.validated_data['participant_id']
        
        try:
            expense = Expense.objects.get(id=expense_id)
            participant = User.objects.get(id=participant_id)
            expense_participant = ExpenseParticipant.objects.get(
                expense=expense, user=participant
            )
        except (Expense.DoesNotExist, User.DoesNotExist, ExpenseParticipant.DoesNotExist):
            return Response({
                'success': False,
                'message': 'Expense participant not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create payment record
        payment, _ = Payment.objects.get_or_create(
            expense_participant=expense_participant,
            defaults={
                'expense': expense,
                'payer': participant,
                'payee': expense.paid_by,
                'amount': expense_participant.amount_owed,
                'status': 'pending',
            }
        )
        
        # Initiate PayHero STK push
        payhero_service = get_payhero_service()
        result = payhero_service.initiate_stk_push(
            participant.phone_number,
            float(expense_participant.amount_owed),
            payment.id
        )
        
        if result['success']:
            payment.status = 'initiated'
            payment.payhero_transaction_id = result['checkout_request_id']
            payment.save()
            
            return Response({
                'success': True,
                'message': 'STK push sent',
                'payment_id': payment.id,
                'checkout_request_id': result['checkout_request_id'],
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Failed to initiate payment')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Check payment status"""
        payment = self.get_object()
        serializer = PaymentSerializer(payment)
        
        # Check with PayHero if initiated
        if payment.status == 'initiated' and payment.payhero_transaction_id:
            payhero_service = get_payhero_service()
            result = payhero_service.check_transaction_status(
                payment.payhero_transaction_id
            )
            
            if result['success']:
                return Response({
                    'payment': serializer.data,
                    'payhero_status': result,
                })
        
        return Response(serializer.data)


# ============================================================================
# Smart Split Views
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_split(request):
    """Generate AI-based split suggestions"""
    expense_id = request.data.get('expense_id')
    
    try:
        expense = Expense.objects.get(id=expense_id)
    except Expense.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Expense not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Simple rule-based suggestion logic
    participants = list(expense.participants.all())
    
    if not participants:
        return Response({
            'success': False,
            'message': 'No participants in expense'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    suggestion_data = {}
    
    # Base: Equal split
    equal_share = expense.total_amount / len(participants)
    for p in participants:
        suggestion_data[p.id] = {
            'name': p.name,
            'suggested_amount': str(equal_share),
            'reasoning': 'Equal split based on participant count'
        }
    
    # Option: Based on credit score (participants with higher credit get slight discount)
    total_credit_score = sum(p.credit_score for p in participants)
    if total_credit_score > 0:
        credit_weighted = {}
        for p in participants:
            weight = p.credit_score / total_credit_score
            credit_weighted[p.id] = {
                'name': p.name,
                'suggested_amount': str(expense.total_amount * weight),
                'reasoning': f'Weighted by credit score ({p.credit_score})'
            }
    
    # Create suggestion
    suggestion = SmartSplitSuggestion.objects.create(
        expense=expense,
        suggestion_data={
            'equal_split': suggestion_data,
            'credit_weighted': credit_weighted if total_credit_score > 0 else None,
        },
        reasoning='Automatically generated suggestions based on participant credit scores and count.'
    )
    
    serializer = SmartSplitSuggestionSerializer(suggestion)
    return Response({
        'success': True,
        'suggestion': serializer.data,
    }, status=status.HTTP_201_CREATED)


# ============================================================================
# Webhook Views
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def payhero_webhook(request):
    """Handle PayHero webhook"""
    try:
        payhero_service = get_payhero_service()
        result = payhero_service.process_webhook(request.data)
        
        if result['success']:
            return Response({
                'success': True,
                'message': result.get('message')
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': result.get('message')
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
