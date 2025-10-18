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
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import (
    User, Group, GroupMember, Expense, ExpenseParticipant,
    Payment, Balance, SmartSplitSuggestion
)
from .serializers import (
    UserSerializer, UserProfileSerializer, GroupSerializer,
    GroupDetailSerializer, ExpenseSerializer, ExpenseDetailSerializer,
    ExpenseParticipantSerializer, PaymentSerializer, BalanceSerializer,
    SmartSplitSuggestionSerializer, CreateGroupSerializer,
    CreateExpenseSerializer, InitiatePaymentSerializer,
    RegisterSerializer, LoginSerializer, LoginResponseSerializer,
    AddMemberSerializer, SmartSplitRequestSerializer,
    PayHeroWebhookSerializer
)
from .supabase_service import get_supabase_service
from .payhero_service import get_payhero_service
from .auth import get_current_user


# ============================================================================
# Authentication Views
# ============================================================================

@extend_schema(
    request=RegisterSerializer,
    responses={201: UserSerializer},
    tags=['Authentication'],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User registration via Supabase
    
    Create a new user account with email, password, name and phone number.
    """
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


@extend_schema(
    request=LoginSerializer,
    responses={200: LoginResponseSerializer},
    tags=['Authentication'],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login via Supabase
    
    Login with email and password to get access token.
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
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

@extend_schema(tags=['Users'])
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


@extend_schema(
    responses={200: UserProfileSerializer},
    tags=['Users'],
)
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

@extend_schema(tags=['Groups'])
class GroupViewSet(viewsets.ModelViewSet):
    """ViewSet for managing groups"""
    permission_classes = [IsAuthenticated]
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    http_method_names = ['get', 'post', 'head', 'options']  # Exclude PUT, PATCH, DELETE
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GroupDetailSerializer
        elif self.action == 'create':
            return CreateGroupSerializer
        return GroupSerializer
    
    @extend_schema(
        request=RegisterSerializer,
        responses={201: GroupDetailSerializer},
        examples=[
            OpenApiExample(
                "Create Group",
                value={
                    "title": "Weekend Trip",
                    "description": "Mombasa beach trip",
                    "member_phone_numbers": ["+254712345678", "+254798765432"]
                },
            ),
        ],
    )
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
    
    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "phone_number": {"type": "string", "example": "+254712345678"}
            }
        },
        responses={201: GroupDetailSerializer},
    )
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
    
    @extend_schema(responses={200: BalanceSerializer})
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

@extend_schema(tags=['Expenses'])
class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet for managing expenses"""
    permission_classes = [IsAuthenticated]
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    http_method_names = ['get', 'post', 'head', 'options']  # Exclude PUT, PATCH, DELETE
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ExpenseDetailSerializer
        elif self.action == 'create':
            return CreateExpenseSerializer
        return ExpenseSerializer
    
    @extend_schema(
        request=CreateExpenseSerializer,
        responses={201: ExpenseDetailSerializer},
        examples=[
            OpenApiExample(
                "Create Expense - Equal Split",
                value={
                    "group_id": 1,
                    "title": "Dinner",
                    "description": "Restaurant bill",
                    "total_amount": 2000,
                    "split_type": "equal",
                    "participant_ids": ["user-1", "user-2", "user-3"],
                    "auto_initiate_payments": False
                },
            ),
            OpenApiExample(
                "Create Expense - Equal Split with Auto STK Push",
                value={
                    "group_id": 1,
                    "title": "Weekend Trip",
                    "description": "Transportation and accommodation",
                    "total_amount": 6000,
                    "split_type": "equal",
                    "participant_ids": ["user-1", "user-2", "user-3", "user-4"],
                    "auto_initiate_payments": True
                },
            ),
            OpenApiExample(
                "Create Expense - Custom Split",
                value={
                    "group_id": 1,
                    "title": "Shopping",
                    "description": "Grocery shopping",
                    "total_amount": 5000,
                    "split_type": "custom",
                    "participant_ids": ["user-1", "user-2"],
                    "custom_splits": {
                        "user-1": 3000,
                        "user-2": 2000
                    }
                },
            ),
        ],
    )
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
        auto_initiate = serializer.validated_data.get('auto_initiate_payments', False)
        
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
        
        # Auto-initiate STK push for all participants if requested
        initiated_payments = []
        if auto_initiate:
            payhero_service = get_payhero_service()
            expense_participants = ExpenseParticipant.objects.filter(expense=expense)
            
            for ep in expense_participants:
                # Skip the person who paid
                if ep.user == request.user:
                    continue
                
                # Create payment record
                payment, created = Payment.objects.get_or_create(
                    expense_participant=ep,
                    defaults={
                        'expense': expense,
                        'payer': ep.user,
                        'payee': request.user,
                        'amount': ep.amount_owed,
                        'status': 'pending',
                    }
                )
                
                # Initiate STK push
                result = payhero_service.initiate_stk_push(
                    phone_number=ep.user.phone_number,
                    amount=float(ep.amount_owed),
                    payment_id=payment.id,
                    external_reference=f"EXP-{expense.id}-PAY-{payment.id}",
                    customer_name=ep.user.name
                )
                
                if result['success']:
                    payment.status = 'initiated'
                    payment.payhero_transaction_id = result.get('checkout_request_id')
                    payment.save()
                    
                    initiated_payments.append({
                        'user': ep.user.name,
                        'phone': ep.user.phone_number,
                        'amount': float(ep.amount_owed),
                        'status': 'sent'
                    })
        
        response_serializer = ExpenseDetailSerializer(expense)
        response_data = response_serializer.data
        
        # Add payment initiation info if applicable
        if auto_initiate and initiated_payments:
            response_data['initiated_payments'] = initiated_payments
            response_data['payments_sent'] = len(initiated_payments)
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        """Filter expenses for current user's groups"""
        return Expense.objects.filter(group__members=self.request.user)
    
    @extend_schema(responses={200: ExpenseDetailSerializer})
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

@extend_schema(tags=['Payments'])
class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payments"""
    permission_classes = [IsAuthenticated]
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    http_method_names = ['get', 'head', 'options']  # Only GET operations, payments created via actions
    
    @extend_schema(exclude=True)
    def create(self, request, *args, **kwargs):
        """Hidden: Use /initiate/ or /initiate-all/ instead"""
        return Response({
            'message': 'Use /api/payments/initiate/ to create payments'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def get_queryset(self):
        """Filter payments for current user"""
        return Payment.objects.filter(
            Q(payer=self.request.user) | Q(payee=self.request.user)
        )
    
    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "expense_id": {"type": "integer", "example": 1},
                "participant_id": {"type": "string", "example": "user-1"}
            }
        },
        responses={200: PaymentSerializer},
        examples=[
            OpenApiExample(
                "Initiate Payment",
                value={
                    "expense_id": 1,
                    "participant_id": "user-1"
                },
            ),
        ],
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
            phone_number=participant.phone_number,
            amount=float(expense_participant.amount_owed),
            payment_id=payment.id,
            external_reference=f"EXP-{expense.id}-PAY-{payment.id}",
            customer_name=participant.name
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
    
    @extend_schema(responses={200: PaymentSerializer})
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
    
    @extend_schema(
        responses={200: {
            'type': 'object',
            'properties': {
                'expense': {'type': 'object'},
                'participants': {'type': 'array'},
            }
        }}
    )
    @action(detail=False, methods=['get'], url_path='expense-participants/(?P<expense_id>[^/.]+)')
    def expense_participants(self, request, expense_id=None):
        """Get all participants and their payment status for an expense"""
        try:
            expense = Expense.objects.get(id=expense_id)
        except Expense.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Expense not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all participants with their payment status
        participants_data = []
        expense_participants = ExpenseParticipant.objects.filter(expense=expense)
        
        for ep in expense_participants:
            # Get existing payment for this participant
            payment = Payment.objects.filter(expense_participant=ep).first()
            
            participants_data.append({
                'user_id': ep.user.id,
                'user_name': ep.user.name,
                'phone_number': ep.user.phone_number,
                'amount_owed': float(ep.amount_owed),
                'amount_paid': float(ep.amount_paid),
                'settled': ep.settled,
                'payment_status': payment.status if payment else 'not_initiated',
                'payment_id': payment.id if payment else None,
                'checkout_request_id': payment.payhero_transaction_id if payment else None,
            })
        
        return Response({
            'success': True,
            'expense': {
                'id': expense.id,
                'title': expense.title,
                'total_amount': float(expense.total_amount),
                'paid_by': expense.paid_by.name,
                'settled': expense.settled,
            },
            'participants': participants_data,
        })
    
    @extend_schema(
        request={
            'type': 'object',
            'properties': {
                'expense_id': {'type': 'integer'}
            }
        },
        responses={200: {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'initiated_count': {'type': 'integer'},
                'payments': {'type': 'array'},
            }
        }}
    )
    @action(detail=False, methods=['post'], url_path='initiate-all')
    def initiate_all(self, request):
        """Initiate STK push for all unpaid participants in an expense"""
        expense_id = request.data.get('expense_id')
        
        try:
            expense = Expense.objects.get(id=expense_id)
        except Expense.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Expense not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all unpaid participants
        expense_participants = ExpenseParticipant.objects.filter(
            expense=expense,
            settled=False
        )
        
        payhero_service = get_payhero_service()
        initiated_payments = []
        failed_payments = []
        
        for ep in expense_participants:
            # Skip if already paid
            if ep.amount_paid >= ep.amount_owed:
                continue
            
            # Get or create payment record
            payment, created = Payment.objects.get_or_create(
                expense_participant=ep,
                defaults={
                    'expense': expense,
                    'payer': ep.user,
                    'payee': expense.paid_by,
                    'amount': ep.amount_owed,
                    'status': 'pending',
                }
            )
            
            # Skip if already initiated or successful
            if payment.status in ['initiated', 'success']:
                continue
            
            # Initiate STK push
            result = payhero_service.initiate_stk_push(
                phone_number=ep.user.phone_number,
                amount=float(ep.amount_owed),
                payment_id=payment.id,
                external_reference=f"EXP-{expense.id}-PAY-{payment.id}",
                customer_name=ep.user.name
            )
            
            if result['success']:
                payment.status = 'initiated'
                payment.payhero_transaction_id = result.get('checkout_request_id')
                payment.save()
                
                initiated_payments.append({
                    'user_name': ep.user.name,
                    'phone_number': ep.user.phone_number,
                    'amount': float(ep.amount_owed),
                    'payment_id': payment.id,
                    'checkout_request_id': result.get('checkout_request_id'),
                    'status': 'sent'
                })
            else:
                failed_payments.append({
                    'user_name': ep.user.name,
                    'phone_number': ep.user.phone_number,
                    'amount': float(ep.amount_owed),
                    'error': result.get('message', 'Unknown error')
                })
        
        return Response({
            'success': True,
            'message': f'Initiated {len(initiated_payments)} STK push requests',
            'initiated_count': len(initiated_payments),
            'failed_count': len(failed_payments),
            'initiated_payments': initiated_payments,
            'failed_payments': failed_payments,
        }, status=status.HTTP_200_OK)


# ============================================================================
# Smart Split Views
# ============================================================================

@extend_schema(
    request={
        "type": "object",
        "properties": {
            "expense_id": {"type": "integer", "example": 1}
        }
    },
    responses={201: SmartSplitSuggestionSerializer},
    examples=[
        OpenApiExample(
            "Smart Split Request",
            value={
                "expense_id": 1
            },
        ),
    ],
    tags=['Smart Split'],
)
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
    credit_weighted = {}
    if total_credit_score > 0:
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

@extend_schema(
    request={
        "type": "object",
        "properties": {
            "response": {
                "type": "object",
                "properties": {
                    "CheckoutRequestID": {"type": "string"},
                    "ResultCode": {"type": "integer"},
                    "MpesaReceiptNumber": {"type": "string"}
                }
            }
        }
    },
    tags=['Webhooks'],
)
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
