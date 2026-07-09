from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from .rag import SecurityRAG

class ChatViewSet(viewsets.ViewSet):
    """AI Chat Assistant API"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def sessions(self, request):
        """Get chat sessions"""
        sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')[:30]
        return Response(ChatSessionSerializer(sessions, many=True).data)
    
    @action(detail=False, methods=['post'])
    def send(self, request):
        """Send a message and get AI response"""
        message = request.data.get('message', '').strip()
        session_id = request.data.get('session_id')
        
        if not message:
            return Response({'error': 'Message required'}, status=400)
        
        # Get or create session
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create(user=request.user, title=message[:50])
        else:
            session = ChatSession.objects.create(
                user=request.user,
                title=message[:50] + ('...' if len(message) > 50 else ''),
            )
        
        # Save user message
        user_msg = ChatMessage.objects.create(
            session=session, role='user', content=message
        )
        
        # Generate AI response
        try:
            rag = SecurityRAG(request.user)
            response_text = rag.answer_query(message)
        except Exception as e:
            response_text = f"I encountered an error analyzing your request: {str(e)}\n\nPlease try asking about alerts, events, incidents, agents, or IPs."
        
        # Save assistant message
        assistant_msg = ChatMessage.objects.create(
            session=session, role='assistant', content=response_text,
            metadata={'model': 'security-rag-v1'}
        )
        
        session.updated_at = timezone.now()
        session.save()
        
        return Response({
            'session_id': str(session.id),
            'session_title': session.title,
            'user_message': ChatMessageSerializer(user_msg).data,
            'assistant_message': ChatMessageSerializer(assistant_msg).data,
        })
    
    @action(detail=False, methods=['post'])
    def new_session(self, request):
        """Create new chat session"""
        session = ChatSession.objects.create(user=request.user)
        return Response({
            'session_id': str(session.id),
            'title': session.title,
        })
    
    @action(detail=False, methods=['get'])
    def messages(self, request):
        """Get messages for a session"""
        session_id = request.query_params.get('session_id')
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
            messages = session.messages.all()
            return Response(ChatMessageSerializer(messages, many=True).data)
        except ChatSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
    
    @action(detail=False, methods=['post'])
    def delete_session(self, request):
        """Delete a chat session"""
        session_id = request.data.get('session_id')
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
            session.delete()
            return Response({'status': 'deleted'})
        except ChatSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
    
    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        """Get suggested questions"""
        return Response([
            "Show me critical alerts from today",
            "What are the top attacking IPs?",
            "How many incidents are open?",
            "Show agent status summary",
            "What's my security score?",
            "List recent failed logins",
            "Summary of today's events",
        ])